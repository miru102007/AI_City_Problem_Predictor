# 🏙️ AI City Problem Predictor

### AI-Powered Smart City Infrastructure Risk Assessment

An AI-based Smart City application designed to estimate potential infrastructure risks using environmental conditions, traffic intensity, road age, public complaints, and maintenance history.

## 🚀 Live Demo

**Try the application:** https://ai-city-problem-predictor.onrender.com

## 📌 Project Overview

City infrastructure problems can affect public safety and daily life. This project provides a dashboard to estimate infrastructure risk and recommend suitable follow-up actions based on user-provided conditions.

The application is developed as a Smart City prototype for infrastructure risk assessment and maintenance planning.

## ✨ Key Features

- **AI Risk Prediction:** Estimates infrastructure risk from five input factors.
- **Risk Factor Analysis:** Displays individual factor levels.
- **Recommended Actions:** Suggests follow-up maintenance or inspection actions.
- **Department Alerts:** Displays suggested departments, priorities, and alerts.
- **Dashboard:** Provides an overview of assessments and risk information.
- **Reports & History:** Provides assessment and alert information during the application session.
- **Web-Based Access:** Open the deployed application through a browser.

## 📊 Input Parameters

| Parameter | Description |
|---|---|
| Rainfall | Recent or forecast rainfall in mm |
| Traffic Intensity | Estimated traffic load in percentage |
| Road Age | Approximate age of the road in years |
| Previous Complaints | Number of reported issues |
| Maintenance Gap | Months since the last maintenance activity |

## 🛠️ Technologies Used

- Python
- Scikit-learn
- Logistic Regression
- CSV Dataset
- HTML and CSS
- Render Cloud Hosting
- GitHub

## 🧠 Machine Learning Workflow

1. Collect infrastructure-related data.
2. Validate the dataset and its columns.
3. Train a Logistic Regression model using the training script.
4. Save the trained model as `city_model.pkl`.
5. Use the model to estimate risk from the entered parameters.
6. Display the prediction and suggested follow-up actions.

## 📂 Project Structure

```text
AI_City_Problem_Predictor/
├── app.py
├── train_model.py
├── city_data.csv
├── city_model.pkl
├── requirements.txt
├── render.yaml
└── README.md
