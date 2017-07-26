#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#include <set>
#include <cctype>
#include <cstring>
#include <string>
#include <algorithm>

#include "compact_lang_det.h"
#include "header.h"
// #include "tld.h"

using CLD2::int32;
using std::string;
using std::getline;
using std::cin;
using std::cout;

typedef int32 Encoding;
static const Encoding UNKNOWN_ENCODING = 0;
static const char* magic_number = "df6fa1abb58549287111ba8d776733e9";

std::vector<std::string> split(const std::string& s, const char delim = ' ') {
  std::vector<std::string> tokens;
  std::stringstream ss(s);
  std::string token;
  while (std::getline(ss, token, delim)) {
    if (!token.empty()) {
      tokens.push_back(token);
    }
  }
  return tokens;
}

string domain_suffix(const string& url) {
	const string protocol_separator = "://";
	size_t start = url.find(protocol_separator);
	if (start == string::npos) {
		start = 0;
	} else {
		start += protocol_separator.size();
	}

	const string path_separator = "/";
	size_t end = url.find_first_of(path_separator, start);
	if (end == string::npos) {
		end = url.size();
	}

	const string host = url.substr(start, end-start);

	size_t suffix_start = host.find_last_of(".");
	if (suffix_start == string::npos) {
		return "";
	}
	return host.substr(suffix_start + 1);
}


void PrintLanguageStats(const int flags, const string& header,
                        const string& buffer, const bool print_chunks) {
  if (header.empty() || buffer.empty()) {
    return;
  }

  const Header header_values(header);
  const string uri = header_values.get_uri();
  //const string tld = uri2tld(uri);
  const string tld = header_values.get_tld();
  // const string tld = domain_suffix(uri);

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
    if (print_chunks) {
      for (int i = 0; i < static_cast<int>(resultchunkvector.size()); ++i) {
        const CLD2::ResultChunk& rc = resultchunkvector[i];
        CLD2::Language rc_lang = static_cast<CLD2::Language>(rc.lang1);
        if (rc_lang == CLD2::UNKNOWN_LANGUAGE) {
          continue;
        }
        const char* lang_code = LanguageCode(rc_lang);
        const string chunk = string(buffer, rc.offset, rc.bytes);

        std::cout << header << " language:" << lang_code
                  << " offset:" << rc.offset << " bytes:" << rc.bytes
                  << std::endl;
        std::cout << chunk << std::endl;
      }
    } else {
      // only print some statistics
      std::cout << header << " bytes:" << buffer.size() << std::endl;
      for (int i = 0; i < 3; i++) {
        if (percent3[i] > 0) {
          const char* lang_name = LanguageName(language3[i]);
          std::cout << lang_name << "\t" << percent3[i] << "\t"
                    << normalized_score3[i] << std::endl;
        }
      }
    }
  } else {
    std::cerr << "prediction unrealiable" << std::endl;
  }
}

// Hints are collected into a struct.
// Flags are passed in (normally zero).
//
// Also returns 3 internal language scores as a ratio to
// normal score for real text in that language. Scores close to 1.0 indicate
// normal text, while scores far away from 1.0 indicate badly-skewed text or
// gibberish
//
// Returns a vector of chunks in different languages, so that caller may
// spell-check, translate, or otherwise process different parts of the input
// buffer in language-dependent ways.
//
// If the input is in fact not valid UTF-8, this returns immediately with
// the result value UNKNOWN_LANGUAGE and is_reliable set to false.
//
// In all cases, valid_prefix_bytes will be set to the number of leading
// bytes that are valid UTF-8. If this is < buffer_length, there is invalid
// input starting at the following byte.

// from
// http://stackoverflow.com/questions/216823/whats-the-best-way-to-trim-stdstring
static string trim(const string& s) {
  auto wsfront = std::find_if_not(s.begin(), s.end(),
                                  [](int c) { return std::isspace(c); });
  auto wsback = std::find_if_not(s.rbegin(), s.rend(),
                                 [](int c) { return std::isspace(c); }).base();
  return (wsback <= wsfront ? std::string() : std::string(wsfront, wsback));
}


int main(int argc, char** argv) {
  int flags = 0;
  bool print_stats = false;
  bool print_chunks = false;
  for (int i = 1; i < argc; ++i) {
    if (strcmp(argv[i], "--scoreasquads") == 0) {
      flags |= CLD2::kCLDFlagScoreAsQuads;
    }
    if (strcmp(argv[i], "--html") == 0) {
      flags |= CLD2::kCLDFlagHtml;
    }
    if (strcmp(argv[i], "--cr") == 0) {
      flags |= CLD2::kCLDFlagCr;
    }
    if (strcmp(argv[i], "--verbose") == 0) {
      flags |= CLD2::kCLDFlagVerbose;
    }
    if (strcmp(argv[i], "--echo") == 0) {
      flags |= CLD2::kCLDFlagEcho;
    }
    if (strcmp(argv[i], "--besteffort") == 0) {
      flags |= CLD2::kCLDFlagBestEffort;
    }
    if (strcmp(argv[i], "--printstats") == 0) {
      print_stats = true;
    }
    if (strcmp(argv[i], "--printchunks") == 0) {
      print_chunks = true;
    }
  }

  std::ostringstream buffer;
  string line;
  string header;
  while (getline(cin, line)) {
    line = trim(line);
    if (line.empty()) {
      continue;
    }
    if (line.find(magic_number) == 0) {
      if (print_stats || print_chunks) {
        PrintLanguageStats(flags, header, buffer.str(), print_chunks);
      }
      buffer.clear();
      buffer.str(string(""));
      header = line;
    } else {
      buffer << line << std::endl;
    }
  }

  if (print_stats || print_chunks) {
    PrintLanguageStats(flags, header, buffer.str(), print_chunks);
  }

  //  ProcessBuffer(flags, header, tld, buffer.str());
}
