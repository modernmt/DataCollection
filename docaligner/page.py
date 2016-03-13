class Page(object):

    def __init__(self, url, html, text, mime_type,
                 encoding, french, english, english_mt):
        self.url = url
        self.html = html
        self.text = text
        self.mime_type = mime_type
        self.encoding = encoding
        self.french = french
        self.english = english
        self.english_mt = english_mt

    def __str__(self):
        res = []
        res.append("--Page--")
        res.append("url : %s" % self.url)
        res.append("html : %s" % self.html)
        res.append("text : %s" % self.text.encode('utf-8'))
        res.append("mime_type : %s" % self.mime_type)
        res.append("encoding : %s" % self.encoding)
        res.append("french : %s" % self.french.encode('utf-8'))
        res.append("english : %s" % self.english.encode('utf-8'))
        res.append("english_mt : %s" % self.english_mt.encode('utf-8'))
        return "\n".join(res)
