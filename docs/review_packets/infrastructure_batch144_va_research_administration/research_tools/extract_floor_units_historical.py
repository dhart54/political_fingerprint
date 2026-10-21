import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.validate_infrastructure_disaster_candidates142 import normalized_pdf,sha
T=Path('.tmp/infra_batch144');P=Path('docs/review_packets/infrastructure_batch144_va_research_administration')
F={586:('crec20250407house',[15,16],17,21,22,'VIETNAM VETERANS LIVER FLUKE CANCER STUDY ACT',89),1039:('crec20250407house',[17],18,22,23,'CLEAR COMMUNICATION FOR VETERANS CLAIMS ACT',90),530:('crec20250505house',[3],5,27,28,'ACES ACT',115),1286:('crec20250519house',[16,17],18,28,29,'SIMPLIFYING FORMS FOR VETERANS CLAIMS ACT',133),980:('crec20260202house',[5],6,12,12,'VETERANS READINESS AND EMPLOYMENT IMPROVEMENT ACT OF 2025',49)}
def page(k,n):return normalized_pdf((T/(k+f'_page{n}.txt')).read_text(encoding='utf8'))
def content_start(s):
 m=re.match(r'CONGRESSIONAL RECORD — HOUSE\s*H\d+\s+(?:April 7, 2025|May 5, 2025|May 19, 2025|February 2, 2026)\s*',s);assert m,s[:120];return m.end()
def footer(s):return s.index('VerDate')
units=[];comparisons=[]
def add(b,key,k,extents):
 text=' [page boundary] '.join(page(k,e['page'])[e['start']:e['end']] for e in extents)
 u=dict(unit_key=f'hr{b}_'+key,capture_key=k,pdf_normalized_page_extents=extents,page_join_marker=' [page boundary] ',whole_parent_document_reviewed=False,text=text,passage_sha256=sha(text.encode()));units.append(u);return text
infra={s['source_id']:s for s in json.loads(Path('docs/editorial/shared_candidates/house_119_infrastructure_batch139_20260916/sources.json').read_text(encoding='utf8'))['sources']}
for b,(k,bodypages,qp,rp,op,title,roll) in F.items():
 ex=[]
 for i,n in enumerate(bodypages):
  s=page(k,n);start=s.index(title) if i==0 else content_start(s)
  end=s.index('The SPEAKER pro tempore.',start) if i==len(bodypages)-1 else footer(s)
  ex.append(dict(page=n,start=start,end=end))
 floor=add(b,'floor_operative',k,ex)
 q=page(k,qp);m=re.search(r'The question is on the motion.*?H\.R\. '+str(b)+r', as amended\.',q);assert m
 start=q.rfind('The SPEAKER',0,m.start());end=q.find(' f ',m.end())
 if end<0:
  following=page(k,qp+1);qext=[dict(page=qp,start=start,end=footer(q)),dict(page=qp+1,start=content_start(following),end=following.index(' f '))]
 else:qext=[dict(page=qp,start=start,end=end)]
 question=add(b,'question_postponement',k,qext);assert 'postpon' in question.lower()
 s=page(k,rp);loc=s.index('(H.R. '+str(b)+')');start=s.rfind('The SPEAKER',0,loc);end=s.index(']',s.index('[Roll No. '+str(roll)+']',loc))+1
 add(b,'resumption_roll'+str(roll),k,[dict(page=rp,start=start,end=end)])
 s=page(k,op);start=s.index('So (two-thirds');end=s.index('A motion to reconsider was laid on the table.',start)+len('A motion to reconsider was laid on the table.')
 add(b,'passage_result',k,[dict(page=op,start=start,end=end)])
 eh=infra[f'govinfo:hr{b}eh']['text'];eh=eh[eh.index('Be it enacted'):eh.index('Passed the House')];f=floor[floor.index('Be it enacted'):].replace(' [page boundary] ',' ')
 token=lambda z:re.sub('[^a-z0-9]','',z.casefold())
 ehn,fn=token(eh),token(f);equal=ehn==fn
 c=dict(bill=b,whole_operative_tokens_equal=equal,EH_tokens=len(ehn),floor_tokens=len(fn))
 if not equal:
  i=next((i for i,(a,z) in enumerate(zip(ehn,fn)) if a!=z),min(len(ehn),len(fn)));c.update(first_difference=i,EH_window=ehn[max(0,i-60):i+150],floor_window=fn[max(0,i-60):i+150])
 comparisons.append(c)
(T/'floor_units.json').write_text(json.dumps(units,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(T/'operative_comparison.json').write_text(json.dumps(comparisons,indent=2)+'\n',encoding='utf8');print(json.dumps(comparisons,indent=2));print('units',len(units),'selectedpages',len({(u['capture_key'],e['page']) for u in units for e in u['pdf_normalized_page_extents']}))
