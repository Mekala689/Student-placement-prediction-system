# PlaceIQ — Student Placement Intelligence System

A working Flask + Data Science project with separate Student and Placement Officer portals.

## Features
- Student registration/login and admin login
- Student academic/skill profile
- Placement prediction using a trained Random Forest model
- Live What-If simulator using the same ML model
- Resume Analyzer for PDF/DOCX/TXT: text extraction, skills, missing sections, contact checks, role matches
- Career role matching
- Company eligibility checker
- Prediction history
- Admin dashboard
- Dataset Management with search/filter/pagination/download
- Admin CSV upload + automatic model retraining
- Dataset-driven analytics
- Registered student view

## Dataset
`data/placement_dataset.csv` contains 1,200 synthetic student records created for academic demonstration. It is clearly synthetic and is used to train/test the model.

## Run on Windows
Open CMD inside the extracted folder:

    python -m pip install -r requirements.txt
    python app.py

Open: http://127.0.0.1:5000

## Admin Login
Email: admin@placement.local
Password: admin123

Students should use Register to create their own account.

## Retrain manually
If you replace the dataset with a compatible CSV:

    python train_model.py

Required model columns are defined in `train_model.py` / `app.py`, plus `placed` as the target.

## Important academic note
The bundled dataset is synthetic, so model metrics demonstrate the pipeline rather than real-world placement performance. For a final research claim, replace it with an approved real institutional/public dataset and retrain.
