# InsightWave

## AI-Powered Customer Churn Prediction and Retention System for Media Streaming Platforms

InsightWave is an AI-powered customer analytics platform designed to help media streaming platforms understand customer churn, identify at-risk customers, and generate actionable retention insights.

The system combines machine learning, analytics, and generative AI into a single dashboard for customer-level churn prediction and business intelligence.

---

## ✨ Features

### 📊 Customer Churn Prediction
Predict whether a customer is likely to churn using a trained machine learning pipeline.

The system provides:

- Churn prediction
- Churn probability
- Risk level
- Customer-level analysis

### 🤖 AI-Powered Churn Insights

InsightWave uses Groq-powered generative AI to provide:

- Churn explanations
- Behavioral insights
- Retention recommendations

The AI explanation is based on the customer's actual data and the machine learning prediction.

### 💬 InsightWave AI Assistant

Ask natural-language business questions about the available customer dataset.

Example questions:

- Which subscription type has the highest churn rate?
- What is the overall churn rate?
- How does watch time differ between churned and non-churned customers?
- Which payment method has the highest churn?

The assistant uses calculated dataset analytics as its context and avoids inventing unavailable metrics.

### 📈 Analytics Dashboard

The dashboard provides:

- Overall customer statistics
- Churn distribution
- Churn by subscription type
- Churn by payment method
- Churn by region
- Engagement analysis

### 🌙 Light & Dark Mode

InsightWave includes:

- Light theme
- Dark theme
- Persistent theme preference
- Responsive dashboard design

---

## 🧠 Machine Learning

InsightWave evaluates four classification models:

1. Logistic Regression
2. Decision Tree
3. Random Forest
4. Gradient Boosting

The models are evaluated using:

- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix

Gradient Boosting was selected for the prediction API based on the measured validation/test results from the project.

### Model Performance

| Model | Accuracy | Precision | Recall | F1 Score |
|---|---:|---:|---:|---:|
| Gradient Boosting | 98.80% | 99.00% | 98.61% | 98.80% |
| Random Forest | 98.30% | 98.60% | 98.01% | 98.31% |
| Decision Tree | 97.90% | 97.82% | 98.01% | 97.91% |
| Logistic Regression | 88.70% | 87.50% | 90.46% | 88.95% |

> These results are based on the project's held-out dataset split and should not be interpreted as guaranteed real-world performance.

---

## 📁 Dataset

InsightWave uses the **Netflix Customer Churn Dataset**.

### Dataset characteristics

- 5,000 customers
- 14 columns
- 0 missing values
- 0 duplicate rows
- Binary churn target
- Balanced churn distribution

### Target

```text
churned
0 = Not Churned
1 = Churned

## Vercel Deployment

InsightWave is configured as one Vercel Project using Vercel Services:

- `frontend` builds the React/Vite application and serves `/`.
- `backend` runs the existing FastAPI application.
- `/api/*` is routed to FastAPI and the internal service transform removes the `/api` prefix before the existing routes handle the request.

The deployment configuration is in `vercel.json`. The frontend remains configured with `VITE_API_BASE_URL=/api` by default, so production uses one domain without a CORS workaround.

### Required Vercel environment variable

Add this variable in the Vercel Project Settings for the Production, Preview, and Development environments as needed:

```text
GROQ_API_KEY=your_groq_api_key
```

Never commit `.env`. It is ignored by Git and is intended only for local development.

### Local commands

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
cd frontend
npm run dev
```

Vercel Services are a Vercel platform feature and may require Services access to be enabled for the account. Connect the repository as one Vercel Project, keep the project root at the repository root, and add `GROQ_API_KEY` in the dashboard before deploying.