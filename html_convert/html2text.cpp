#include <algorithm>
#include <stdio.h>
#include <stdlib.h>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <set>

#include "gumbo.h"

using std::string;
using std::getline;
using std::cin;
using std::cout;

// Tags that define a block and thus introduce a line break
static std::set<string> block_tags = {
    "address", "article", "aside",  "audio",    "blockquote", "canvas",
    "dd",      "div",     "dl",     "fieldset", "figcaption", "figure",
    "footer",  "form",    "h1",     "h2",       "h3",         "h4",
    "h5",      "h6",      "header", "hgroup",   "hr",         "noscript",
    "ol",      "output",  "p",      "pre",      "section",    "table",
    "tfoot",   "ul",      "video"};

static void Cleantext(GumboNode* node, std::ostringstream& oss) {
  if (node->type == GUMBO_NODE_TEXT) {
    string text(node->v.text.text);
    std::replace(text.begin(), text.end(), '\n', ' ');
    oss << text;
  } else if (node->type == GUMBO_NODE_WHITESPACE) {
    oss << " ";
  } else if (node->type == GUMBO_NODE_ELEMENT &&
             node->v.element.tag != GUMBO_TAG_SCRIPT &&
             node->v.element.tag != GUMBO_TAG_STYLE) {
    if (node->v.element.tag == GUMBO_TAG_BR ||
        node->v.element.tag == GUMBO_TAG_LI) {
      oss << std::endl;
    }
    // Insert space before and after spans. This is in violation of the 
    // HTML5 standard but spans are often fitted with margins to make the words
    // look sperated when they are not. Adding spaces mimics this.
    if (node->v.element.tag == GUMBO_TAG_SPAN) {
      *textbuffer << " ";
    }
    // descend into subtree
    GumboVector* children = &node->v.element.children;
    for (unsigned int i = 0; i < children->length; ++i) {
      Cleantext((GumboNode*)children->data[i], oss);
    }
 
    // Space after span, see above
    if (node->v.element.tag == GUMBO_TAG_SPAN) {
      *textbuffer << " ";
    }

    const std::string tagname = gumbo_normalized_tagname(node->v.element.tag);
    if (block_tags.find(tagname) != block_tags.end()) {
      oss << std::endl;
    }
  }
}

void ProcessBuffer(const string& header, const string& buffer) {
  if (header.empty() || buffer.empty()) {
    return;
  }
  GumboOutput* output = gumbo_parse(buffer.c_str());
  std::cout << header << std::endl;
  std::ostringstream extracted_text;
  Cleantext(output->root, extracted_text);
  std::cout << extracted_text.str() << std::endl;
  gumbo_destroy_output(&kGumboDefaultOptions, output);
}

int main(int argc, char** argv) {
  const char* magic_number = "df6fa1abb58549287111ba8d776733e9";
  std::ostringstream buffer;
  string line;
  string header;
  while (getline(cin, line)) {
    if (line.find(magic_number) == 0) {
      ProcessBuffer(header, buffer.str());
      buffer.clear();
      buffer.str(string(""));
      header = line;
    } else {
      buffer << line << std::endl;
    }
  }
  ProcessBuffer(header, buffer.str());
}
