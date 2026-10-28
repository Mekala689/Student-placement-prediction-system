import pandas as pd, os, joblib, json
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,roc_auc_score
BASE=os.path.dirname(__file__); path=os.path.join(BASE,'data','placement_dataset.csv')
FEATURES=['department','cgpa','tenth','twelfth','attendance','backlogs','aptitude','coding','communication','projects','internships','certifications','hackathons']
df=pd.read_csv(path); X=df[FEATURES]; y=df['placed']; cat=['department']; num=[x for x in FEATURES if x not in cat]
pre=ColumnTransformer([('num',Pipeline([('imp',SimpleImputer(strategy='median')),('scale',StandardScaler())]),num),('cat',OneHotEncoder(handle_unknown='ignore'),cat)])
model=Pipeline([('pre',pre),('model',RandomForestClassifier(n_estimators=350,max_depth=10,min_samples_leaf=3,class_weight='balanced',random_state=42))])
Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.22,random_state=42,stratify=y); model.fit(Xtr,ytr); pred=model.predict(Xte); proba=model.predict_proba(Xte)[:,1]
metrics={'accuracy':round(accuracy_score(yte,pred)*100,2),'precision':round(precision_score(yte,pred,zero_division=0)*100,2),'recall':round(recall_score(yte,pred,zero_division=0)*100,2),'f1':round(f1_score(yte,pred,zero_division=0)*100,2),'roc_auc':round(roc_auc_score(yte,proba)*100,2),'train_rows':len(Xtr),'test_rows':len(Xte),'model':'Random Forest'}
os.makedirs(os.path.join(BASE,'models'),exist_ok=True); joblib.dump(model,os.path.join(BASE,'models','placement_model.joblib')); json.dump(metrics,open(os.path.join(BASE,'models','metrics.json'),'w'),indent=2); print(metrics)
