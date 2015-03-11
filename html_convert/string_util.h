#ifndef STRING_UTIL_H_
#define STRING_UTIL_H_

#include <algorithm>
#include <string>
#include <vector>

namespace {

using std::string;

class StringUtil {
 public:
  static bool EndsWith(string const& s, const string& end) {
    if (s.length() >= end.length() &&
        s.compare(s.length() - end.length(), end.length(), end) == 0) {
      return true;
    }
//    std::cout << s << " does not end with " << end << std::endl;
    return false;
  }

  static string ToLower(const string& s) {
    string lower(s);
    std::transform(s.begin(), s.end(), lower.begin(), ::tolower);
//    std::cout << lower << std::endl;
    return lower;
  }

  static std::vector<string> Split(const string& s, const char delim = ' ') {
    std::vector<string> tokens;
    std::stringstream ss(s);
    string token;
    while (std::getline(ss, token, delim)) {
      if (!token.empty()) {
        tokens.push_back(token);
      }
    }
    return tokens;
  }

  static string Trim(const string& s) {
    auto wsfront = std::find_if_not(s.begin(), s.end(),
                                    [](int c) { return std::isspace(c); });
    auto wsback =
        std::find_if_not(s.rbegin(), s.rend(),
                         [](int c) { return std::isspace(c); }).base();
    return (wsback <= wsfront ? std::string() : std::string(wsfront, wsback));
  }

  static void TrimRepeatedSpace(string* s) {
    s->erase(std::unique(s->begin(), s->end(),
                         [](char a, char b) { return std::isspace(a) && std::isspace(b); }),
             s->end());
  }

  static string TrimRepeatedWhitespace(const string& s) {
    std::stringstream ss(s);
    std::ostringstream oss;
    string line;
    while (std::getline(ss, line)) {
      line = Trim(line);
      if (!line.empty()) {
        TrimRepeatedSpace(&line);
        oss << line << std::endl;
      }
    }
    return oss.str();
  }
};

}  // namespace

#endif /* STRING_UTIL_H_ */
