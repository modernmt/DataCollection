#include <algorithm>
#include <cctype>
#include <cstring>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <stdio.h>
#include <stdlib.h>
#include <string>
#include <vector>

#include "compact_lang_det.h"
#include "getopt.h"
#include "gumbo.h"
#include "tld.h"

#include "string_util.h"
#include "header.h"

using std::string;
using std::getline;
using std::cin;
using std::vector;
using std::cout;
using std::ofstream;

typedef CLD2::int32 Encoding;
static const Encoding UNKNOWN_ENCODING = 0;
static const char* magic_number = "df6fa1abb58549287111ba8d776733e9";

// Tags that define a block and thus introduce a line break
static std::set<string> block_tags = {
    "address", "article", "aside",  "audio",    "blockquote", "canvas",
    "dd",      "div",     "dl",     "fieldset", "figcaption", "figure",
    "footer",  "form",    "h1",     "h2",       "h3",         "h4",
    "h5",      "h6",      "header", "hgroup",   "hr",         "noscript",
    "ol",      "output",  "p",      "pre",      "section",    "table",
    "tfoot",   "ul",      "video"};

// Using libidn to get tld
string uri2tld(const string& uri) {
  char* tld_cstr = nullptr;
  const int rc = tld_get_z(uri.c_str(), &tld_cstr);
  if (rc == TLD_SUCCESS && tld_cstr != nullptr) {
    const string result = string(tld_cstr);
    return result;
    free(tld_cstr);
  } else {
    return "";
  }
}

static void DumpText(GumboNode* node, std::ostringstream* textbuffer) {
  if (node->type == GUMBO_NODE_TEXT) {
    string text(node->v.text.text);
    std::replace(text.begin(), text.end(), '\n', ' ');
    *textbuffer << text;
  } else if (node->type == GUMBO_NODE_WHITESPACE) {
    *textbuffer << " ";
  } else if (node->type == GUMBO_NODE_ELEMENT &&
             node->v.element.tag != GUMBO_TAG_SCRIPT &&
             node->v.element.tag != GUMBO_TAG_STYLE) {
    // Insert line breaks for <br> and <li>
    if (node->v.element.tag == GUMBO_TAG_BR ||
        node->v.element.tag == GUMBO_TAG_LI) {
      *textbuffer << std::endl;
    }
    // Descend into subtree
    GumboVector* children = &node->v.element.children;
    for (unsigned int i = 0; i < children->length; ++i) {
      DumpText(static_cast<GumboNode*>(children->data[i]), textbuffer);
    }

    const std::string tagname = gumbo_normalized_tagname(node->v.element.tag);
    // Insert line break if tag defines a block
    if (block_tags.find(tagname) != block_tags.end()) {
      *textbuffer << std::endl;
    }
  }
}

static string DumpText(GumboNode* node) {
  std::ostringstream textbuffer;
  DumpText(node, &textbuffer);
  return textbuffer.str();
}

void SplitTextByLanguage(const int flags, const string& header,
                         const string& buffer, ofstream* outfile,
                         ofstream* statsfile) {
  if (header.empty() || buffer.empty()) {
    return;
  }

  const Header header_values(header);
  const string uri = header_values.get_uri();
  const string tld = uri2tld(uri);

  bool is_plain_text = true;
  CLD2::CLDHints cld_hints = {NULL, NULL, UNKNOWN_ENCODING,
                              CLD2::UNKNOWN_LANGUAGE};
  if (!tld.empty()) {
    cld_hints.tld_hint = tld.c_str();
  }
  CLD2::Language language3[3];
  int percent3[3];
  double normalized_score3[3];
  int valid_prefix_bytes;

  CLD2::ResultChunkVector resultchunkvector;
  int text_bytes;
  bool is_reliable;

  CLD2::ExtDetectLanguageSummaryCheckUTF8(
      buffer.c_str(), buffer.size(), is_plain_text, &cld_hints, flags,
      language3, percent3, normalized_score3, &resultchunkvector, &text_bytes,
      &is_reliable, &valid_prefix_bytes);

  if (is_reliable) {
    if (outfile != nullptr && outfile->is_open()) {
      for (int i = 0; i < static_cast<int>(resultchunkvector.size()); ++i) {
        const CLD2::ResultChunk& rc = resultchunkvector[i];
        CLD2::Language rc_lang = static_cast<CLD2::Language>(rc.lang1);
        if (rc_lang == CLD2::UNKNOWN_LANGUAGE) {
          continue;
        }
        const char* lang_code = LanguageCode(rc_lang);
        const string chunk = string(buffer, rc.offset, rc.bytes);

        *outfile << header << " language:" << lang_code
                 << " offset:" << rc.offset << " bytes: " << rc.bytes
                 << std::endl;
        *outfile << StringUtil::TrimRepeatedWhitespace(chunk) << std::endl;
      }
    }
    if (statsfile != nullptr && statsfile->is_open()) {
      // print some statistics
      *statsfile << header << " bytes:" << buffer.size() << std::endl;
      for (int i = 0; i < 3; i++) {
        if (percent3[i] > 0) {
          const char* lang_name = LanguageName(language3[i]);
          *statsfile << lang_name << "\t" << percent3[i] << "\t"
                     << normalized_score3[i] << std::endl;
        }
      }
    }
  }
}

static void GetLinks(const string& suffix, GumboNode* node,
                     vector<string>* links) {
  if (node->type != GUMBO_NODE_ELEMENT) {
    return;
  }
  GumboAttribute* href;
  if (node->v.element.tag == GUMBO_TAG_A &&
      (href = gumbo_get_attribute(&node->v.element.attributes, "href")) &&
      StringUtil::EndsWith(StringUtil::ToLower(href->value), suffix)) {
    links->push_back(href->value);
  }

  GumboVector* children = &node->v.element.children;
  for (unsigned int i = 0; i < children->length; ++i) {
    GetLinks(suffix, static_cast<GumboNode*>(children->data[i]), links);
  }
}

static void DumpLinks(const string& header, GumboNode* node,
                      ofstream* outfile) {
  static string suffix(".pdf");
  vector<string> links;
  GetLinks(suffix, node, &links);
  if (!links.empty()) {
    *outfile << header << std::endl;
    for (const auto& link : links) {
      *outfile << link << std::endl;
    }
  }
}

void ProcessBuffer(const string& header, const string& buffer,
                   const int split_by_language, ofstream* text_file,
                   ofstream* pdf_links_file, ofstream* language_stats_file) {
  if (header.empty() || buffer.empty()) {
    return;
  }
  GumboOutput* output = gumbo_parse(buffer.c_str());

  if (text_file->is_open() || language_stats_file->is_open()) {
    string text = DumpText(output->root);
    if (!split_by_language) {
      *text_file << header << std::endl;
      *text_file << text << std::endl;
    } else {
      int flags = 0;
      SplitTextByLanguage(flags, header, text, text_file, language_stats_file);
    }
  }
  if (pdf_links_file->is_open()) {
    DumpLinks(header, output->root, pdf_links_file);
  }

  gumbo_destroy_output(&kGumboDefaultOptions, output);
}

int main(int argc, char** argv) {
  ofstream text_file, pdf_links_file, lang_stats_file;
  int split_by_language = 0;
  while (1) {
    static struct option long_options[] = {
        {"splitlang", no_argument, &split_by_language, 1},
        {"textfile", required_argument, 0, 't'},
        {"pdflinks", required_argument, 0, 'p'},
        {"langstats", required_argument, 0, 'l'},
        {0, 0, 0, 0}};
    int option_index = 0;

    int c = getopt_long(argc, argv, "t:p:l:", long_options, &option_index);

    // End of options
    if (c == -1) {
      break;
    }

    switch (c) {
      case 0:
        /* If this option set a flag, do nothing else now. */
        if (long_options[option_index].flag != 0) break;
        printf("option %s", long_options[option_index].name);
        if (optarg) printf(" with arg %s", optarg);
        printf("\n");
        break;

      case 't':
        text_file.open(optarg);
        break;

      case 'p':
        pdf_links_file.open(optarg);
        break;

      case 'l':
        lang_stats_file.open(optarg);
        break;

      case '?':
        break;

      default:
        abort();
    }
  }

  std::ostringstream buffer;
  string line;
  string header;
  while (getline(cin, line)) {
    if (line.find(magic_number) == 0) {
      ProcessBuffer(header, buffer.str(), split_by_language, &text_file,
                    &pdf_links_file, &lang_stats_file);
      buffer.clear();
      buffer.str(string(""));
      header = line;
    } else {
      buffer << line << std::endl;
    }
  }
  ProcessBuffer(header, buffer.str(), split_by_language, &text_file,
                &pdf_links_file, &lang_stats_file);
  return 0;
}
