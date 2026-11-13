"""Read-only dated Code HTML extraction, without substantive text repair."""
from html.parser import HTMLParser
import hashlib
import re


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def display(value):
    p = Text()
    p.feed(value)
    return re.sub(r'\s+', ' ', ''.join(p.parts)).strip()


def field(raw, name):
    s = raw.decode('utf8')
    a = '<!-- field-start:'+name+' -->'
    b = '<!-- field-end:'+name+' -->'
    if s.count(a) != 1 or s.count(b) != 1:
        raise ValueError(('Field extent mismatch', name, s.count(a), s.count(b)))
    return display(s.split(a, 1)[1].split(b, 1)[0])


def validate_passages(rows, streams):
    for r in rows:
        s = streams[r['source']]
        if not 0 <= r['start'] < r['end'] <= len(s):
            raise ValueError(('Invalid extent', r['id']))
        if r['total'] != len(s) or s[r['start']:r['end']] != r['text']:
            raise ValueError(('Literal mismatch', r['id']))
        if hashlib.sha256(r['text'].encode()).hexdigest() != r['sha256']:
            raise ValueError(('Passage SHA mismatch', r['id']))
