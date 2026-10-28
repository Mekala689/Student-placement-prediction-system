from flask import Flask,render_template,request,redirect,url_for,session,flash,jsonify,send_file
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename
import sqlite3,os,re,json,joblib,pandas as pd,numpy as np
from datetime import datetime
from pypdf import PdfReader
from docx import Document
BASE=os.path.dirname(__file__); DB=os.path.join(BASE,'placement.db'); DATA=os.path.join(BASE,'data','placement_dataset.csv'); MODEL=os.path.join(BASE,'models','placement_model.joblib'); METRICS=os.path.join(BASE,'models','metrics.json'); UP=os.path.join(BASE,'uploads')
app=Flask(__name__); app.secret_key='spi-pro-2026'; app.config['MAX_CONTENT_LENGTH']=6*1024*1024
FEATURES=['department','cgpa','tenth','twelfth','attendance','backlogs','aptitude','coding','communication','projects','internships','certifications','hackathons']
SKILLS=['python','java','c++','javascript','sql','html','css','react','flask','django','machine learning','data science','power bi','tableau','excel','aws','azure','git','github','dsa','communication','leadership','problem solving']
ROLE_SKILLS={'Data Analyst':['python','sql','excel','power bi','data science'],'Software Developer':['java','python','dsa','git','sql'],'Web Developer':['html','css','javascript','react','git'],'Business Analyst':['excel','sql','power bi','communication','leadership'],'ML Engineer':['python','machine learning','data science','sql','git'],'Cloud Associate':['aws','azure','python','git','sql']}
COMPANIES=[('TCS',6.0,0,60,55),('Infosys',6.0,0,60,55),('Accenture',6.5,0,65,60),('Cognizant',6.0,0,60,60),('Zoho',6.0,2,70,70),('Freshworks',7.0,0,70,70)]
model=joblib.load(MODEL); metrics=json.load(open(METRICS))
def db(): c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 c=db(); c.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT,department TEXT);CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY,cgpa REAL DEFAULT 7.5,tenth REAL DEFAULT 75,twelfth REAL DEFAULT 75,attendance REAL DEFAULT 80,backlogs INTEGER DEFAULT 0,aptitude REAL DEFAULT 60,coding REAL DEFAULT 60,communication REAL DEFAULT 60,projects INTEGER DEFAULT 1,internships INTEGER DEFAULT 0,certifications INTEGER DEFAULT 0,hackathons INTEGER DEFAULT 0,skills TEXT DEFAULT '');CREATE TABLE IF NOT EXISTS predictions(id INTEGER PRIMARY KEY,user_id INTEGER,probability REAL,status TEXT,created TEXT);''')
 if not c.execute("SELECT 1 FROM users WHERE email='admin@placement.local'").fetchone(): c.execute('INSERT INTO users(name,email,password,role,department) VALUES(?,?,?,?,?)',('Placement Officer','admin@placement.local',generate_password_hash('admin123'),'admin','Placement Cell'))
 c.commit(); c.close()
init()
def guard(role=None):
 def d(fn):
  from functools import wraps
  @wraps(fn)
  def w(*a,**k):
   if not session.get('uid'): return redirect(url_for('login'))
   if role and session.get('role')!=role: return redirect(url_for('dashboard'))
   return fn(*a,**k)
  return w
 return d
def profile(uid):
 c=db(); p=c.execute('SELECT * FROM profiles WHERE user_id=?',(uid,)).fetchone(); c.close(); return p
def predict(d):
 row={k:d.get(k) for k in FEATURES}; row['department']=row.get('department') or 'CSE'
 for k in FEATURES[1:]: row[k]=float(row[k] or 0)
 prob=float(model.predict_proba(pd.DataFrame([row]))[0,1])*100
 status='High Chance' if prob>=75 else 'Moderate Chance' if prob>=50 else 'Needs Improvement'
 factors=[]
 checks=[('CGPA',row['cgpa'],7.5),('Aptitude',row['aptitude'],70),('Coding',row['coding'],70),('Communication',row['communication'],70),('Projects',row['projects'],3),('Internships',row['internships'],1)]
 for n,v,t in checks: factors.append((n,'Strong' if v>=t else 'Improve',v,t))
 return {'probability':round(prob,1),'status':status,'factors':factors}
@app.route('/')
def landing(): return render_template('landing.html')
@app.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  f=request.form; c=db()
  try:
   cur=c.execute('INSERT INTO users(name,email,password,role,department) VALUES(?,?,?,?,?)',(f['name'],f['email'].lower(),generate_password_hash(f['password']),'student',f['department'])); c.execute('INSERT INTO profiles(user_id) VALUES(?)',(cur.lastrowid,)); c.commit(); flash('Account created. Login now.','ok'); return redirect(url_for('login'))
  except sqlite3.IntegrityError: flash('Email already registered.','bad')
  finally: c.close()
 return render_template('auth.html',mode='Register')
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  c=db(); u=c.execute('SELECT * FROM users WHERE email=?',(request.form['email'].lower(),)).fetchone(); c.close()
  if u and check_password_hash(u['password'],request.form['password']): session.update(uid=u['id'],name=u['name'],role=u['role']); return redirect(url_for('dashboard'))
  flash('Invalid login.','bad')
 return render_template('auth.html',mode='Login')
@app.route('/logout')
def logout(): session.clear(); return redirect(url_for('landing'))
@app.route('/dashboard')
@guard()
def dashboard():
 if session['role']=='admin': return redirect(url_for('admin_dashboard'))
 p=profile(session['uid']); c=db(); h=c.execute('SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC LIMIT 5',(session['uid'],)).fetchall(); c.close(); return render_template('student_dashboard.html',p=p,h=h)
@app.route('/profile',methods=['GET','POST'])
@guard('student')
def profile_page():
 if request.method=='POST':
  f=request.form; c=db(); c.execute('''UPDATE profiles SET cgpa=?,tenth=?,twelfth=?,attendance=?,backlogs=?,aptitude=?,coding=?,communication=?,projects=?,internships=?,certifications=?,hackathons=?,skills=? WHERE user_id=?''',tuple(f.get(k,0) for k in ['cgpa','tenth','twelfth','attendance','backlogs','aptitude','coding','communication','projects','internships','certifications','hackathons'])+(f.get('skills',''),session['uid'])); c.commit(); c.close(); flash('Profile saved.','ok')
 return render_template('profile.html',p=profile(session['uid']))
@app.route('/predict',methods=['GET','POST'])
@guard('student')
def predictor():
 p=profile(session['uid']); result=None
 if request.method=='POST':
  d=dict(request.form); result=predict(d); c=db(); c.execute('INSERT INTO predictions(user_id,probability,status,created) VALUES(?,?,?,?)',(session['uid'],result['probability'],result['status'],datetime.now().strftime('%d %b %Y %H:%M'))); c.commit(); c.close()
 return render_template('predict.html',p=p,result=result)
@app.route('/whatif')
@guard('student')
def whatif(): return render_template('whatif.html',p=profile(session['uid']))
@app.route('/api/predict',methods=['POST'])
@guard('student')
def api_predict(): return jsonify(predict(request.get_json() or {}))
@app.route('/resume',methods=['GET','POST'])
@guard('student')
def resume():
 result=None
 if request.method=='POST':
  f=request.files.get('resume')
  if not f or not f.filename: flash('Choose PDF, DOCX or TXT.','bad')
  else:
   path=os.path.join(UP,secure_filename(f.filename)); f.save(path)
   try:
    ext=os.path.splitext(path)[1].lower()
    if ext=='.pdf': text='\n'.join((x.extract_text() or '') for x in PdfReader(path).pages)
    elif ext=='.docx': text='\n'.join(x.text for x in Document(path).paragraphs)
    elif ext=='.txt': text=open(path,encoding='utf8',errors='ignore').read()
    else: raise ValueError('Unsupported file type')
    low=text.lower(); found=[s for s in SKILLS if re.search(r'(?<!\w)'+re.escape(s)+r'(?!\w)',low)]; secs={s:bool(re.search(s,low)) for s in ['education','skills','project','experience','internship','certification']}; email=bool(re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+',text)); phone=bool(re.search(r'\b(?:\+?91[- ]?)?[6-9]\d{9}\b',text)); score=min(100,round(min(len(found),8)/8*45+sum(secs.values())/6*35+email*10+phone*10)); roles=[]
    own=set(found)
    for role,req in ROLE_SKILLS.items(): roles.append((role,round(len(own&set(req))/len(req)*100)))
    result={'score':score,'skills':found,'missing':[s.title() for s,v in secs.items() if not v],'email':email,'phone':phone,'words':len(text.split()),'roles':sorted(roles,key=lambda x:x[1],reverse=True)[:3]}
   except Exception as e: flash(str(e),'bad')
   finally:
    try: os.remove(path)
    except: pass
 return render_template('resume.html',result=result)
@app.route('/career')
@guard('student')
def career():
 p=profile(session['uid']); own=set(x.strip().lower() for x in (p['skills'] or '').split(',') if x.strip()); rows=[]
 for role,req in ROLE_SKILLS.items(): rows.append((role,round(len(own&set(req))/len(req)*100),[x for x in req if x not in own]))
 return render_template('career.html',rows=sorted(rows,key=lambda x:x[1],reverse=True))
@app.route('/companies')
@guard('student')
def companies():
 p=profile(session['uid']); rows=[]
 for n,cg,b,ap,co in COMPANIES:
  ck=[p['cgpa']>=cg,p['backlogs']<=b,p['aptitude']>=ap,p['coding']>=co]; rows.append((n,round(sum(ck)/4*100),ck,(cg,b,ap,co)))
 return render_template('companies.html',rows=rows)
@app.route('/history')
@guard('student')
def history():
 c=db(); h=c.execute('SELECT * FROM predictions WHERE user_id=? ORDER BY id DESC',(session['uid'],)).fetchall(); c.close(); return render_template('history.html',h=h)
@app.route('/admin')
@guard('admin')
def admin_dashboard():
 df=pd.read_csv(DATA); c=db(); students=c.execute("SELECT count(*) n FROM users WHERE role='student'").fetchone()['n']; c.close(); stats={'students':students,'records':len(df),'placed':int(df.placed.sum()),'rate':round(df.placed.mean()*100,1),'avgcgpa':round(df.cgpa.mean(),2)}; return render_template('admin_dashboard.html',stats=stats,metrics=metrics)
@app.route('/admin/dataset')
@guard('admin')
def dataset():
 df=pd.read_csv(DATA); q=request.args.get('q','').strip(); dep=request.args.get('department',''); view=df.copy()
 if q: view=view[view.student_id.str.contains(q,case=False,na=False)]
 if dep: view=view[view.department==dep]
 page=max(1,int(request.args.get('page',1))); per=25; pages=max(1,int(np.ceil(len(view)/per))); page=min(page,pages); rows=view.iloc[(page-1)*per:page*per].to_dict('records'); return render_template('dataset.html',rows=rows,total=len(df),shown=len(view),page=page,pages=pages,deps=sorted(df.department.unique()),q=q,dep=dep)
@app.route('/admin/dataset/download')
@guard('admin')
def dataset_download(): return send_file(DATA,as_attachment=True,download_name='placement_dataset.csv')
@app.route('/admin/dataset/upload',methods=['POST'])
@guard('admin')
def dataset_upload():
 f=request.files.get('dataset')
 try:
  df=pd.read_csv(f); required=set(FEATURES+['placed']); missing=required-set(df.columns)
  if missing: raise ValueError('Missing columns: '+', '.join(sorted(missing)))
  df.to_csv(DATA,index=False); os.system(f'"{os.sys.executable}" "{os.path.join(BASE,"train_model.py")}"'); global model,metrics; model=joblib.load(MODEL); metrics=json.load(open(METRICS)); flash('Dataset uploaded and model retrained successfully.','ok')
 except Exception as e: flash('Upload failed: '+str(e),'bad')
 return redirect(url_for('dataset'))
@app.route('/admin/analytics')
@guard('admin')
def analytics():
 df=pd.read_csv(DATA); deps=df.groupby('department').placed.mean().mul(100).round(1).to_dict(); bins=pd.cut(df.cgpa,[0,6,7,8,9,10],labels=['<6','6-7','7-8','8-9','9-10'],include_lowest=True); cg=df.groupby(bins,observed=True).placed.mean().mul(100).round(1).to_dict(); return render_template('analytics.html',deps=deps,cg=cg,metrics=metrics)
@app.route('/admin/students')
@guard('admin')
def students():
 c=db(); rows=c.execute("SELECT u.id,u.name,u.email,u.department,p.cgpa,p.aptitude,p.coding,p.communication FROM users u LEFT JOIN profiles p ON u.id=p.user_id WHERE u.role='student' ORDER BY u.id DESC").fetchall(); c.close(); return render_template('students.html',rows=rows)
if __name__=='__main__': app.run(debug=True)
