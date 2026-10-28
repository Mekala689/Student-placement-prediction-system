import numpy as np, pandas as pd, os
rng=np.random.default_rng(42); n=1200
cgpa=np.clip(rng.normal(7.35,1.05,n),4.5,10).round(2)
tenth=np.clip(rng.normal(77,11,n),45,100).round(1); twelfth=np.clip(rng.normal(75,12,n),40,100).round(1)
attendance=np.clip(rng.normal(82,10,n),50,100).round(1); backlogs=rng.choice([0,1,2,3,4],n,p=[.68,.17,.08,.05,.02])
aptitude=np.clip(rng.normal(68,15,n),20,100).round(1); coding=np.clip(rng.normal(65,18,n),10,100).round(1); communication=np.clip(rng.normal(70,14,n),20,100).round(1)
projects=rng.choice([0,1,2,3,4,5],n,p=[.05,.16,.29,.28,.16,.06]); internships=rng.choice([0,1,2,3],n,p=[.35,.43,.17,.05])
certifications=rng.choice([0,1,2,3,4,5],n,p=[.13,.27,.27,.18,.1,.05]); hackathons=rng.choice([0,1,2,3,4],n,p=[.38,.31,.18,.09,.04])
department=rng.choice(['CSE','IT','ECE','EEE','AIML'],n,p=[.36,.18,.18,.12,.16])
logit=-10.0 + .72*cgpa + .018*aptitude + .022*coding + .015*communication + .34*projects + .58*internships + .13*certifications + .10*hackathons + .007*attendance - .72*backlogs
prob=1/(1+np.exp(-logit)); placed=(rng.random(n)<prob).astype(int)
package=np.where(placed==1,np.clip(2.5 + .42*(cgpa-6)+.025*(coding-50)+.18*internships+rng.normal(0,.65,n),2.5,12),0).round(2)
df=pd.DataFrame({'student_id':[f'ST{i:04d}' for i in range(1,n+1)],'department':department,'cgpa':cgpa,'tenth':tenth,'twelfth':twelfth,'attendance':attendance,'backlogs':backlogs,'aptitude':aptitude,'coding':coding,'communication':communication,'projects':projects,'internships':internships,'certifications':certifications,'hackathons':hackathons,'placed':placed,'package_lpa':package})
os.makedirs(os.path.join(os.path.dirname(__file__),'data'),exist_ok=True); df.to_csv(os.path.join(os.path.dirname(__file__),'data','placement_dataset.csv'),index=False)
print('Generated',len(df),'rows | placed',int(df.placed.sum()))
