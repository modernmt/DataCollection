#ifndef HEADER_H_
#define HEADER_H_

#include <string>

#include "string_util.h"

namespace {

using std::string;

class Header {
 public:
  explicit Header(const string& header) {
    for (const auto& value : StringUtil::Split(header, ' ')) {
      if (value.find("tld:") == 0) {
        tld_ = value.substr(4);
      } else if (value.find("uri:") == 0) {
        uri_ = value.substr(4);
      } else if (value.find("encoding:") == 0) {
        encoding_ = value.substr(9);
      }
    }
  }

  const string get_tld() const { return tld_; }
  const string get_uri() const { return uri_; }
  const string get_encoding() const { return encoding_; }

 private:
  string uri_;
  string tld_;
  string encoding_;
};

}  // namespace

#endif /* HEADER_H_ */
