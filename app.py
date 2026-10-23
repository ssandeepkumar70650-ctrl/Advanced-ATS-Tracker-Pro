from flask import Flask, render_template, request, redirect, url_for, flash
import pymupdf, re, sqlite3
from pathlib import Path
from datetime import date
app=Flask(__name__); app.secret_key='change-this-local-secret'
ROOT=Path(__file__).resolve().parent; DB=ROOT/'ats_dashboard.db'
SKILLS=['python','java','c++','javascript','html','css','flask','django','sql','mysql','mongodb','machine learning','data analysis','pandas','numpy','git','github','rest api','aws','docker','communication','problem solving','linux']
def connect():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 with connect() as c:
  c.execute("CREATE TABLE IF NOT EXISTS applications(id INTEGER PRIMARY KEY, company TEXT NOT NULL, position TEXT NOT NULL, applied_on TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Applied')")
  c.execute("CREATE TABLE IF NOT EXISTS profile(id INTEGER PRIMARY KEY CHECK(id=1), full_name TEXT NOT NULL DEFAULT 'Sandeep Kumar', email TEXT NOT NULL DEFAULT '', target_role TEXT NOT NULL DEFAULT 'Software Developer')")
  c.execute("INSERT OR IGNORE INTO profile(id) VALUES(1)")
def skills(text):
 text=text.lower(); return [s for s in SKILLS if re.search(r'(?<![a-z0-9])'+re.escape(s)+r'(?![a-z0-9])',text)]
def dashboard():
 with connect() as c:
  apps=c.execute('SELECT * FROM applications ORDER BY id DESC').fetchall()
  counts={s:c.execute('SELECT COUNT(*) FROM applications WHERE status=?',(s,)).fetchone()[0] for s in ['Applied','Shortlisted','Interview','Rejected']}
  profile=c.execute('SELECT * FROM profile WHERE id=1').fetchone()
 return apps,counts,profile
@app.route('/',methods=['GET','POST'])
def index():
 result=None
 if request.method=='POST' and request.form.get('action')=='analyze':
  f=request.files.get('resume'); jd=request.form.get('job_description','').strip()
  if not f or not f.filename: flash('Please upload a PDF resume.','error')
  elif not f.filename.lower().endswith('.pdf'): flash('Please upload a PDF file.','error')
  elif not jd: flash('Please enter a job description.','error')
  else:
   try:
    pdf=pymupdf.open(stream=f.read(),filetype='pdf'); txt='\n'.join(p.get_text() for p in pdf); pdf.close()
    if not txt.strip(): flash('No readable text found. Try a text-based PDF.','error')
    else:
     rs=skills(txt); req=skills(jd); matched=[s for s in req if s in rs]; missing=[s for s in req if s not in rs]
     result={'score':round(len(matched)/len(req)*100) if req else 0,'matched':matched,'missing':missing,'resume_skills':rs,'word_count':len(txt.split()),'suggestions':(['Review these job-related skills: '+', '.join(missing)] if missing else ['Good keyword coverage. Tailor your experience to the job.'])+(['Your resume appears short; add relevant projects and experience if applicable.'] if len(txt.split())<150 else [])}
   except Exception: flash('Could not read this PDF. Please try another text-based PDF.','error')
 apps,counts,profile=dashboard(); completion=sum(bool(profile[k]) for k in ['full_name','email','target_role'])*100//3
 return render_template('index.html',result=result,applications=apps,counts=counts,profile=profile,completion=completion)
@app.post('/applications/add')
def add():
 co=request.form.get('company','').strip(); pos=request.form.get('position','').strip(); st=request.form.get('status','Applied')
 if co and pos and st in ['Applied','Shortlisted','Interview','Rejected']:
  with connect() as c: c.execute('INSERT INTO applications(company,position,applied_on,status) VALUES(?,?,?,?)',(co,pos,date.today().strftime('%b %d, %Y'),st))
  flash('Application added.','success')
 else: flash('Enter company and position.','error')
 return redirect(url_for('index')+'#applications')
@app.post('/applications/<int:aid>/status')
def status(aid):
 st=request.form.get('status','')
 if st in ['Applied','Shortlisted','Interview','Rejected']:
  with connect() as c: c.execute('UPDATE applications SET status=? WHERE id=?',(st,aid))
 return redirect(url_for('index')+'#applications')
@app.post('/applications/<int:aid>/delete')
def delete(aid):
 with connect() as c: c.execute('DELETE FROM applications WHERE id=?',(aid,))
 flash('Application deleted.','success'); return redirect(url_for('index')+'#applications')
@app.post('/profile')
def profile_update():
 vals=[request.form.get(k,'').strip() for k in ['full_name','email','target_role']]
 with connect() as c: c.execute('UPDATE profile SET full_name=?,email=?,target_role=? WHERE id=1',vals)
 flash('Profile saved.','success'); return redirect(url_for('index')+'#profile')
@app.route('/demo')
def demo(): return render_template('demo.html')
init_db()
if __name__=='__main__': app.run(debug=True)
