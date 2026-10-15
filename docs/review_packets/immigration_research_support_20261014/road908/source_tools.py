"""Deterministic source extraction and a narrow literal §101 replay.

Raw HTTP bodies are preserved separately. Operative comparison removes GPO NOTE
and page markers, joins newline-wrapped hyphenated tokens retaining the hyphen,
and collapses whitespace. No numeral, punctuation or substantive text repair.
"""
from html.parser import HTMLParser
import re


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True);self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ['head','script','style']:self.skip+=1
        if not self.skip and tag in ['p','br','h1','h2','h3','h4','h5','div','tr','li']:self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ['head','script','style']:self.skip-=1
        if not self.skip and tag in ['p','h1','h2','h3','h4','h5','div','tr','li']:self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)


def display(raw):
    parser=Text();parser.feed(raw.decode('utf8')if isinstance(raw,bytes)else raw)
    return '\n'.join(re.sub(r'[ \t\f\v]+',' ',line).strip()for line in ''.join(parser.parts).replace('\r\n','\n').split('\n')if line.strip())+'\n'


def pre(raw):
    html=raw.decode('utf8');matches=re.findall(r'<pre\b[^>]*>(.*?)</pre>',html,re.I|re.S);assert len(matches)==1
    parser=Text();parser.feed(matches[0]);return ''.join(parser.parts).replace('\r\n','\n')


def code_statute(raw):
    html=raw.decode('utf8');a='<!-- field-start:statute -->';b='<!-- field-end:statute -->';assert html.count(a)==html.count(b)==1
    return display(html.split(a,1)[1].split(b,1)[0])


def normalize(value):
    value=re.sub(r'<<NOTE:[^<>]*>>','',value)
    value=re.sub(r'\[\[Page.*?\]\]','',value,flags=re.S)
    value=re.sub(r'(?<=[A-Za-z0-9])-[ \t]*\n[ \t]*(?=[A-Za-z0-9])','-',value)
    return re.sub(r'\s+',' ',value).strip()


def section(law,number,next_number):
    pattern=r'\bSEC\.\s+(?:<<NOTE:[^<>]*>>\s*)?'+str(number)+r'\.'
    hits=list(re.finditer(pattern,law,re.S));assert len(hits)==1,(number,len(hits))
    a=hits[0].start();m=re.search(r'\bSEC\.\s+(?:<<NOTE:[^<>]*>>\s*)?'+str(next_number)+r'\.',law[hits[0].end():],re.S);assert m
    b=hits[0].end()+m.start()
    assert normalize(law[a:hits[0].end()])=='SEC. '+str(number)+'.'
    return a,b,law[a:b]


def replay(baseline,eh):
    assert baseline.startswith('SEC. 908.') and eh.startswith('SEC. 101.')
    assert 'Section 908 of the 21st Century ROAD to Housing Act is amended' in eh
    b2a=baseline.index('(2) Review of changes.');b2b=baseline.index('(3) Result of failure to act.',b2a)
    old_b2=baseline[b2a:b2b]
    assert old_b2.count('180-day')==1
    assert 'in subsection (b)(2), by striking ``180-day\'\' and inserting ``90-day\'\''in eh
    new_b2=old_b2.replace('180-day','90-day')
    old_heading='(c) Pilot Program Study.--'
    assert baseline.count(old_heading)==1
    new_heading='(c) Pilot Program Study and Extension.--'
    assert 'inserting ``and Extension\'\' after ``Study\'\''in eh
    ca=baseline.index(old_heading);da=baseline.index('(d) Study on De Novo Insured Depository Institutions.',ca)
    report_start=baseline.index('(2) Report to congress.',ca,da)
    old_report=baseline[report_start:da]
    new_report=old_report.replace('(2) Report to congress.','(3) Report to congress.',1)
    assert 'redesignating paragraph (2) as paragraph (3)'in eh
    payload_start=eh.index('(2) Safety and soundness determination; extension of pilot program.')
    payload_end=eh.index("''; and (3)",payload_start)
    new_c2=eh[payload_start:payload_end]
    # Remove only quotation prefixes surrounding the inserted legal text.
    new_c2=new_c2.replace('``','')
    old_dates='between January 1, 2026, and December 31, 2028'
    new_dates='on or after January 1, 2026'
    assert baseline.count(old_dates)==1 and 'in subsection (e)(6)(B)'in eh
    assert 'by striking ``'+old_dates+"'' and inserting ``"+new_dates+"''"in eh
    result=baseline.replace(old_b2,new_b2,1).replace(old_heading,new_heading,1)
    result=result.replace(old_report,new_c2+' '+new_report,1).replace(old_dates,new_dates,1)
    return {'after':result,'before_b2':old_b2,'after_b2':new_b2,
            'before_heading':old_heading,'after_heading':new_heading,
            'before_report':old_report,'after_report':new_report,
            'inserted_c2':new_c2,'before_dates':old_dates,'after_dates':new_dates}
