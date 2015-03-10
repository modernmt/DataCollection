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

using CLD2::int32;
using std::string;
using std::getline;
using std::cin;
using std::vector;
using std::cout;
using std::ofstream;

typedef int32 Encoding;
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


static void DumpText(GumboNode* node, ofstream* outfile) {
  if (node->type == GUMBO_NODE_TEXT) {
    string text(node->v.text.text);
    std::replace(text.begin(), text.end(), '\n', ' ');
    *outfile << text;
  } else if (node->type == GUMBO_NODE_WHITESPACE) {
    *outfile << " ";
  } else if (node->type == GUMBO_NODE_ELEMENT &&
             node->v.element.tag != GUMBO_TAG_SCRIPT &&
             node->v.element.tag != GUMBO_TAG_STYLE) {
    // Insert line breaks for <br> and <li>
    if (node->v.element.tag == GUMBO_TAG_BR ||
        node->v.element.tag == GUMBO_TAG_LI) {
      *outfile << std::endl;
    }
    // Descend into subtree
    GumboVector* children = &node->v.element.children;
    for (unsigned int i = 0; i < children->length; ++i) {
      DumpText(static_cast<GumboNode*>(children->data[i]), outfile);
    }

    const std::string tagname = gumbo_normalized_tagname(node->v.element.tag);
    // Insert line break if tag defines a block
    if (block_tags.find(tagname) != block_tags.end()) {
      *outfile << std::endl;
    }
  }
}


static void GetLinks(const string& suffix, GumboNode* node, vector<string>* links) {
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

static void DumpLinks(const string& header, GumboNode* node, ofstream* outfile) {
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
                   ofstream* text_file, ofstream* pdf_links_file,
                   ofstream* language_stats_file) {
  if (header.empty() || buffer.empty()) {
    return;
  }
  GumboOutput* output = gumbo_parse(buffer.c_str());

  if (text_file->is_open()) {
    *text_file << header << std::endl;
    DumpText(output->root, text_file);
    *text_file << std::endl;
  }
  if (pdf_links_file->is_open()) {
    DumpLinks(header, output->root, pdf_links_file);
  }

  gumbo_destroy_output(&kGumboDefaultOptions, output);
}

int main(int argc, char** argv) {

  ofstream text_file, pdf_links_file, lang_stats_file;

  while (1) {
    static struct option long_options[] = {
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
      ProcessBuffer(header, buffer.str(), &text_file, &pdf_links_file,
                    &lang_stats_file);
      buffer.clear();
      buffer.str(string(""));
      header = line;
    } else {
      buffer << line << std::endl;
    }
  }
  ProcessBuffer(header, buffer.str(), &text_file, &pdf_links_file,
                &lang_stats_file);
  return 1;
}
