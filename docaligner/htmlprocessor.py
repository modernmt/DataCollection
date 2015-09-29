from HTMLParser import HTMLParser


class HTMLSequencer(HTMLParser):

    def __init__(self, length_function, growth_function):
        HTMLParser.__init__(self)
        self.sequence = []
        self.length_function = length_function
        self.growth_function = growth_function

    def handle_starttag(self, tag, attrs):
        self.sequence.append("<%s>" % tag)

    def handle_endtag(self, tag):
        self.sequence.append("</%s>" % tag)

    def handle_data(self, data):
        if not data.strip():
            return
        n = self.length_function(data)

        for n in range(int(self.growth_function(n))):
            self.sequence.append("%d" % n)

    def get_result(self):
        return self.sequence

    def reset(self):
        HTMLParser.reset(self)
        self.sequence = []
