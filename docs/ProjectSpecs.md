# InsightWave — Project Specification

## 1. Project Overview

InsightWave is an AI-powered customer intelligence system for media streaming platforms. It predicts customers who are likely to discontinue their subscription, analyzes the behavioral factors associated with that prediction, and provides AI-powered business insights and retention recommendations.

## 2. Dataset

Dataset: Netflix Customer Churn Dataset

Records: 5,000

Target column:
- churned

Target values:
- 0 = Not Churned
- 1 = Churned

Dataset characteristics:
- 14 columns
- 0 missing values
- 0 duplicate rows
- Approximately balanced target distribution

## 3. Features

### Numerical Features

- age
- watch_hours
- last_login_days
- monthly_fee
- number_of_profiles
- avg_watch_time_per_day

### Categorical Features

- gender
- subscription_type
- region
- device
- payment_method
- favorite_genre

### Excluded Feature

- customer_id

`customer_id` is an identifier and must never be used as an ML feature.

## 4. Machine Learning

The following models will be implemented and compared:

1. Logistic Regression
2. Decision Tree
3. Random Forest
4. Gradient Boosting

## 5. Model Evaluation

Models will be evaluated using:

- Accuracy
- Precision
- Recall
- F1-Score
- Confusion Matrix

Model selection must be based on measured evaluation results rather than assumptions.

## 6. ML Pipeline

The ML pipeline will follow:

Dataset
→ Data Validation
→ Preprocessing
→ Feature Encoding
→ Train/Test Split
→ Model Training
→ Model Evaluation
→ Model Comparison
→ Selected Model
→ Model Persistence
→ Prediction API

## 7. AI Capabilities

InsightWave will provide:

- Customer churn-risk explanation
- Behavioral insights
- Retention recommendations
- Natural-language business queries
- AI-generated business summaries

## 8. Web Application

### Frontend

React.js

### Backend

FastAPI

### Database

PostgreSQL

### ML

Python
Pandas
NumPy
Scikit-learn

### Visualization

Frontend charts / data visualization

### AI

LLM-based AI layer

## 9. Core Product Features

### Dashboard

Display:

- Total customers
- Churned customers
- Active/non-churned customers
- Overall churn rate
- Customer risk distribution
- Important behavioral insights
- Model performance

### Customer Prediction

Allow business users to provide customer information and receive:

- Churn prediction
- Churn probability
- Risk level
- Important contributing factors
- Suggested retention actions

### Customer Analytics

Allow users to analyze customer behavior and identify patterns associated with churn.

### AI Assistant

The AI assistant should support natural-language questions such as:

- Which customers have the highest churn risk?
- Why are customers leaving?
- What factors are associated with higher churn?
- What retention actions could be considered?

## 10. Project Rules

- Do not use `customer_id` as a feature.
- Do not modify the original dataset.
- Do not invent dataset columns or values.
- Do not claim the dataset contains features that it does not contain.
- Keep preprocessing reproducible.
- Keep the ML pipeline separate from the web application.
- Keep dependencies minimal where practical.
- Do not introduce unnecessary technologies.
- All major features must be functionally tested before submission.
- Model selection must be supported by actual evaluation results.

## 11. Development Strategy

Development should prioritize:

1. Functional correctness
2. ML reliability
3. Backend integration
4. Frontend functionality
5. AI integration
6. Testing
7. UI polish

Avoid unnecessary complexity that does not contribute to the project's core requirements.

## 12. Definition of Done

The project is considered complete when:

- Dataset loads successfully.
- Data preprocessing works.
- All four ML models train successfully.
- Model metrics are generated.
- Models can be compared.
- Selected model can make predictions.
- Prediction is accessible through the backend.
- Dashboard displays real project data.
- Customer risk prediction works.
- AI explanations work.
- AI retention recommendations work.
- AI assistant can answer supported business questions.
- Frontend and backend work together.
- Core workflows have been tested.