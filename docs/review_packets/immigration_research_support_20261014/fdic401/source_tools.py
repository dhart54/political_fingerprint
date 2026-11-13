"""Read-only extraction and literal proposal replay; no network/candidate imports.

Derived display text is HTML entity-decoded, CRLF->LF, with horizontal spaces
collapsed and empty lines removed. Raw response bytes remain separate evidence.
"""
from html.parser import HTMLParser
import re


class DisplayText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.skip=0

    def handle_starttag(self,tag,attrs):
        if tag in ['head','script','style']:
            self.skip+=1
        if not self.skip and tag in ['br','p','h1','h2','h3','h4','h5','h6','div','tr','li','pre']:
            self.parts.append('\n')

    def handle_endtag(self,tag):
        if tag in ['head','script','style']:
            self.skip-=1
        if not self.skip and tag in ['p','h1','h2','h3','h4','h5','h6','div','tr','li','pre']:
            self.parts.append('\n')

    def handle_data(self,data):
        if not self.skip:
            self.parts.append(data)


def display_text(raw):
    parser=DisplayText()
    parser.feed(raw.decode('utf8') if isinstance(raw,bytes) else raw)
    text=''.join(parser.parts).replace('\r\n','\n')
    return '\n'.join(re.sub(r'[ \t\f\v]+',' ',line).strip()
                     for line in text.split('\n') if line.strip())+'\n'


def field(raw,name):
    text=raw.decode('utf8')
    a='<!-- field-start:'+name+' -->'
    b='<!-- field-end:'+name+' -->'
    assert text.count(a)==text.count(b)==1,name
    return display_text(text.split(a,1)[1].split(b,1)[0])


def table_pre(raw):
    text=raw.decode('utf8')
    blocks=re.findall(r'<pre\b[^>]*>(.*?)</pre>',text,re.I|re.S)
    assert len(blocks)==1
    return display_text(blocks[0])


def literal_payload(eh,begin,end):
    start=eh.index(begin)
    stop=eh.index(end,start)
    return eh[start:stop]


def replay(operative,eh):
    """Apply only EH §401's four explicit operations to this dated witness.

    Returned text is synthetic conditional proposal text, never enacted/current
    law or a resolution of partial-term/holdover/incumbent application.
    """
    assert eh.startswith('SEC. 401. FDIC BOARD ACCOUNTABILITY.')
    assert 'in subsection (c)' in eh
    rename_from='Consumer Financial Protection Bureau'
    rename_to='Bureau of Consumer Financial Protection'
    assert 'by striking ``'+rename_from+"'' each place such term appears and inserting ``"+rename_to+"''" in eh
    old_c=next(line for line in operative.splitlines() if line.startswith('(C) 3 of whom'))
    new_c=literal_payload(eh,'(C) 3 of whom',"''; and (3)")
    term_sentence=literal_payload(eh,'No individual may be appointed',"''; and (B)")
    cap=literal_payload(eh,'(4) Maximum length of service.',"''.")
    old_term='Each appointed member shall be appointed for a term of 6 years.'
    assert operative.count(old_c)==operative.count(old_term)==1
    assert '(4) Maximum length of service' not in operative
    assert new_c.endswith('having less than $17,000,000,000 in total assets.')
    assert 'and separately 1 of whom' in new_c
    assert term_sentence=='No individual may be appointed as a member for more than two terms.'
    assert cap=='(4) Maximum length of service.--Notwithstanding any other provision of this Act, no person shall serve as a member for more than twelve years in total.'
    after=operative.replace(rename_from,rename_to)
    after=after.replace(old_c,new_c)
    after=after.replace(old_term,old_term+' '+term_sentence)
    after=after.replace('(d) Vacancy',cap+'\n(d) Vacancy')
    return {'after_text':after,'rename_from':rename_from,'rename_to':rename_to,
            'rename_count':operative.count(rename_from),'old_C':old_c,'new_C':new_c,
            'old_c1':old_term,'new_c1':old_term+' '+term_sentence,'new_c4':cap,
            'term_append_payload':term_sentence}
