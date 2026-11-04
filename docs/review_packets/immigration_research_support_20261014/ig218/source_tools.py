"""Offline, research-only extraction and literal 2022 correspondence replay.

This is not a current-law compiler or an application of H.R.8312. GPO NOTE/page
markers and quotation markup are removed for comparison; whitespace is collapsed
and line-wrapped hyphenated tokens retain their hyphen. No legal text is repaired.
"""
from html.parser import HTMLParser
import re


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def pre(raw):
    matches = re.findall(r'<pre\b[^>]*>(.*?)</pre>', raw.decode('utf8'), re.I | re.S)
    if len(matches) != 1:
        raise ValueError('Expected one PRE')
    parser = Text()
    parser.feed(matches[0])
    return ''.join(parser.parts).replace('\r\n', '\n')


def normalize(value):
    value = re.sub(r'<<NOTE:[^<>]*>>', '', value)
    value = re.sub(r'\[\[Page.*?\]\]', '', value, flags=re.S)
    value = re.sub(r'(?<=[A-Za-z0-9])-[ \t]*\n[ \t]*(?=[A-Za-z0-9])', '-', value)
    return re.sub(r'\s+', ' ', value).strip()


def plain(value):
    return normalize(value).replace('``', '').replace("''", '')


def one_replace(value, old, new):
    if value.count(old) != 1:
        raise ValueError(('Expected one operand', old, value.count(old)))
    return value.replace(old, new, 1)


def payload(operator, start):
    """Take one explicitly delimited GPO quotation, retaining inner paragraphs."""
    at = operator.index('``' + start)
    end = operator.index("''", at)
    return plain(operator[at:end])


def between(value, first, last):
    at = value.index(first)
    return value[at:value.index(last, at)]


def replay(passages):
    t = {x['id']: x['text'] for x in passages}
    b403 = plain(t['recod403'])
    b406 = plain(t['recod406'])
    a403 = b403
    a406 = b406
    op = {k: normalize(t[k]) for k in ['5202a1', '5202b', '5203a', '5204a', '5261', '5272p2', '5272p10']}
    # The source-amendment operands are checked as well as the baseline operands.
    for literal in ['in section 3(b)', 'inserting ``(1)(A)\'\' after ``(b)\'\'',
                    'by striking ``reasons\'\'', 'after ``Houses of Congress\'\'']:
        if literal not in op['5202a1']:
            raise ValueError(('Missing 5202 operator', literal))
    before_b = between(b403, '(b) Removal or Transfer.--', '(c) Not Employee Determining Policy.--')
    after_b = one_replace(before_b, '(b) Removal or Transfer.--', '(b) Removal or Transfer.--(1)(A)')
    after_b = one_replace(after_b, 'in writing the reasons for', 'in writing the substantive rationale, including detailed and case-specific reasons, for')
    after_b = one_replace(after_b, 'to both Houses of Congress,', 'to both Houses of Congress (including to the appropriate congressional committees),')
    after_b = after_b.rstrip() + ' ' + payload(op['5202a1'], '(B) If there is an open or completed inquiry') + ' ' + payload(op['5202a1'], '(2)(A)') + ' '
    a403 = one_replace(a403, before_b, after_b)
    for old, new in [
        ('(i) educate agency employees--', '(i) educate agency employees, including employees of that Office of Inspector General--'),
        ('and Efficiency, the establishment', 'and Efficiency (including the Integrity Committee of that Council), the establishment')]:
        a403 = one_replace(a403, old, new)
    if 'inserting ``, including employees of that Office of Inspector General\'\'' not in op['5204a'] or 'after ``and Efficiency\'\'' not in op['5204a']:
        raise ValueError('Missing 5204 insertion operands')
    a403 += ' ' + payload(op['5203a'], '(h)(1)')
    before_c = between(b406, '(c) Requests for Information.--', '(d) Office Space and Supplies.--')
    after_c = before_c.rstrip() + ' ' + payload(op['5261'], '(3)') + ' '
    a406 = one_replace(a406, before_c, after_c)
    before_h4 = between(b406, '(4) Statement of attorney general regarding denial of request.--', '(i) Non-applicability')
    if 'in subparagraph (B), by striking ``Government\'\'' not in op['5272p2']:
        raise ValueError('Missing 5272(B) operator')
    hb = between(before_h4, '(B)', '(C)')
    # The recodification already omits Government. Do not manufacture a match.
    if 'Government' in hb:
        raise ValueError('Expected already-absent Government operand')
    old_hc = '(C) Other appropriate committees and subcommittees of Congress.'
    new_hc = payload(op['5272p2'], '(C) Any other relevant')
    a406 = one_replace(a406, old_hc, new_hc)
    before_ig = between(plain(t['recod401']), '(4) Inspector general.--', '(5) Office.--').strip()
    if 'before ``the term\'\'' not in op['5202b']:
        raise ValueError('Missing old12(3) operand')
    # Old12(3) inserted before "the term"; the recoder reversed definition order.
    # Preserve that positional discrepancy explicitly, not as an official repair.
    return {
        'status': 'Research correspondence display only; not official consolidated/current law or candidate interpretation',
        '403_before': b403, '403_after_selected_2022': a403,
        '406_before': b406, '406_after_selected_2022': a406,
        '401_ig_before': before_ig,
        '401_ig_qualifier_payload': 'except as otherwise expressly provided,',
        '401_ig_position_limit': 'Old12(3) inserts the qualifier before the term; recoded401(4) has The term first and a paragraph heading. No relocated qualifier or official technical text repair is manufactured. The original operator and correspondence are supplied separately.',
        '401_new_definition_payload': payload(op['5272p10'], '(6)'),
        '406_h4B_Government': {'matches': 0, 'status': 'Already absent in restated text; no strike applied', 'text': hb.strip()},
        'unchanged_406f': between(b406, '(f) Additional Authority.--', '(g) Budgets.--'),
    }
