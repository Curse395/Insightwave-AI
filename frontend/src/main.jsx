import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const initialForm = {
  age: 34,
  watch_hours: 12.5,
  last_login_days: 8,
  monthly_fee: 13.99,
  number_of_profiles: 2,
  avg_watch_time_per_day: 1.8,
  gender: 'Female',
  subscription_type: 'Standard',
  region: 'North America',
  device: 'TV',
  payment_method: 'Credit Card',
  favorite_genre: 'Drama',
}

const numericFields = [
  ['age', 'Age'],
  ['watch_hours', 'Watch hours'],
  ['last_login_days', 'Last login days'],
  ['monthly_fee', 'Monthly fee'],
  ['number_of_profiles', 'Profiles'],
  ['avg_watch_time_per_day', 'Avg watch time / day'],
]

const selectFields = [
  ['gender', 'Gender', ['Female', 'Male', 'Other']],
  ['subscription_type', 'Subscription', ['Basic', 'Standard', 'Premium']],
  ['region', 'Region', ['Africa', 'Asia', 'Europe', 'North America', 'Oceania', 'South America']],
  ['device', 'Device', ['TV', 'Mobile', 'Tablet', 'Laptop']],
  ['payment_method', 'Payment method', ['Credit Card', 'Crypto', 'Debit Card', 'Gift Card', 'PayPal']],
  ['favorite_genre', 'Favorite genre', ['Action', 'Comedy', 'Drama', 'Horror', 'Romance', 'Sci-Fi']],
]

const assistantExamples = [
  'Which subscription type has the highest churn?',
  'What is the overall churn rate?',
  'How does watch time differ between churned and non-churned customers?',
  'Which payment method has the highest churn?',
]

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) throw new Error(`Request failed (${response.status})`)
  return response.json()
}

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`)
  return data
}

function formatNumber(value) {
  return new Intl.NumberFormat('en-US').format(value)
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`
}

function BarList({ items, labelKey, valueKey, color = 'coral', valueFormatter = formatNumber }) {
  const max = Math.max(...items.map((item) => item[valueKey]), 1)
  return (
    <div className="bar-list">
      {items.map((item) => (
        <div className="bar-row" key={item[labelKey]}>
          <div className="bar-label"><span>{item[labelKey]}</span><strong>{valueFormatter(item[valueKey])}</strong></div>
          <div className="bar-track"><span className={`bar-fill ${color}`} style={{ width: `${(item[valueKey] / max) * 100}%` }} /></div>
        </div>
      ))}
    </div>
  )
}

function MetricCard({ label, value, note, accent }) {
  return <article className={`metric-card ${accent}`}><span className="metric-label">{label}</span><strong>{value}</strong><span className="metric-note">{note}</span></article>
}

function InsightWaveMark({ className = '' }) {
  return <span className={`brand-mark ${className}`} aria-hidden="true"><svg viewBox="0 0 32 32"><path d="M4 20.5c4.2-7.2 7.4-7.2 11.4 0 4.1 7.2 7.4 7.2 12.6-1.9" /><path d="M4 14.3c4.2-7.2 7.4-7.2 11.4 0 4.1 7.2 7.4 7.2 12.6-1.9" /><circle cx="4" cy="14.3" r="1.5" /><circle cx="28" cy="12.4" r="1.5" /></svg></span>
}

function App() {
  const [theme, setTheme] = useState(() => window.localStorage.getItem('insightwave-theme') || 'light')
  const [overview, setOverview] = useState(null)
  const [distribution, setDistribution] = useState(null)
  const [subscription, setSubscription] = useState([])
  const [payment, setPayment] = useState([])
  const [region, setRegion] = useState([])
  const [engagement, setEngagement] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(initialForm)
  const [prediction, setPrediction] = useState(null)
  const [predicting, setPredicting] = useState(false)
  const [predictError, setPredictError] = useState('')
  const [assistantQuestion, setAssistantQuestion] = useState('')
  const [assistantResponse, setAssistantResponse] = useState(null)
  const [assistantLoading, setAssistantLoading] = useState(false)
  const [assistantError, setAssistantError] = useState('')

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem('insightwave-theme', theme)
  }, [theme])

  useEffect(() => {
    Promise.all([
      fetchJson('/analytics/overview'),
      fetchJson('/analytics/churn-distribution'),
      fetchJson('/analytics/by-subscription'),
      fetchJson('/analytics/by-payment-method'),
      fetchJson('/analytics/by-region'),
      fetchJson('/analytics/engagement'),
    ])
      .then(([overviewData, distributionData, subscriptionData, paymentData, regionData, engagementData]) => {
        setOverview(overviewData)
        setDistribution(distributionData)
        setSubscription(subscriptionData)
        setPayment(paymentData)
        setRegion(regionData)
        setEngagement(engagementData)
      })
      .catch((requestError) => setError(`Unable to load dashboard data. ${requestError.message}`))
      .finally(() => setLoading(false))
  }, [])

  function updateField(event) {
    const { name, value, type } = event.target
    setForm((current) => ({ ...current, [name]: type === 'number' ? Number(value) : value }))
  }

  async function submitPrediction(event) {
    event.preventDefault()
    setPredicting(true)
    setPredictError('')
    setPrediction(null)
    try {
      setPrediction(await postJson('/ai/insights', form))
    } catch (requestError) {
      setPredictError(`Prediction unavailable. ${requestError.message}`)
    } finally {
      setPredicting(false)
    }
  }

  async function askAssistant(event, question = assistantQuestion) {
    event?.preventDefault()
    const trimmedQuestion = question.trim()
    if (!trimmedQuestion) {
      setAssistantError('Enter a business question to ask the assistant.')
      setAssistantResponse(null)
      return
    }

    setAssistantQuestion(trimmedQuestion)
    setAssistantLoading(true)
    setAssistantError('')
    setAssistantResponse(null)
    try {
      setAssistantResponse(await postJson('/ai/chat', { message: trimmedQuestion }))
    } catch (requestError) {
      setAssistantError(`Assistant unavailable. ${requestError.message}`)
    } finally {
      setAssistantLoading(false)
    }
  }

  const churnedShare = distribution ? distribution.churned / (distribution.churned + distribution.non_churned) : 0
  const engagementRows = engagement ? [
    ['Watch hours', engagement.watch_hours],
    ['Last login days', engagement.last_login_days],
    ['Avg watch time / day', engagement.avg_watch_time_per_day],
  ] : []

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand"><InsightWaveMark /><span>InsightWave</span></div>
        <div className="topbar-actions"><div className="status-pill"><span className="status-dot" /> Live intelligence workspace</div><button className="theme-toggle" type="button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}><span aria-hidden="true">{theme === 'light' ? '☾' : '☀'}</span><b>{theme === 'light' ? 'Dark' : 'Light'}</b></button></div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">Customer intelligence / phase 04</p>
          <h1>See churn clearly.<br /><em>Act earlier.</em></h1>
          <p className="hero-copy">AI-powered customer churn prediction and retention intelligence for media streaming platforms.</p>
        </div>
        <div className="hero-signal"><span>DATASET SIGNAL</span><strong>{overview ? formatPercent(overview.churn_rate) : '--'}</strong><small>overall churn rate</small></div>
      </section>

      {error && <div className="alert error">{error}</div>}
      {loading && <div className="loading-panel">Loading live analytics from FastAPI...</div>}

      {!loading && !error && <>
        <section className="metrics-grid" aria-label="Customer overview">
          <MetricCard label="Total customers" value={formatNumber(overview.total_customers)} note="active records" accent="mint" />
          <MetricCard label="Churned customers" value={formatNumber(overview.churned_customers)} note="requires attention" accent="coral" />
          <MetricCard label="Non-churned" value={formatNumber(overview.non_churned_customers)} note="retained customers" accent="blue" />
          <MetricCard label="Overall churn rate" value={formatPercent(overview.churn_rate)} note="of total customers" accent="gold" />
        </section>

        <section className="section-heading"><div><p className="eyebrow">Portfolio pulse</p><h2>Where retention is shifting</h2></div><span className="section-caption">Updated from the live customer dataset</span></section>
        <section className="dashboard-grid">
          <article className="panel distribution-panel"><div className="panel-heading"><div><span className="panel-kicker">01 / Customer base</span><h3>Churn distribution</h3></div><span className="panel-icon">◒</span></div><div className="donut-wrap"><div className="donut" style={{ '--churned': `${churnedShare * 360}deg` }}><div><strong>{formatPercent(churnedShare)}</strong><span>churned</span></div></div><div className="legend"><div><i className="legend-dot coral" /><span>Churned</span><strong>{formatNumber(distribution.churned)}</strong></div><div><i className="legend-dot blue" /><span>Non-churned</span><strong>{formatNumber(distribution.non_churned)}</strong></div></div></div></article>
          <article className="panel"><div className="panel-heading"><div><span className="panel-kicker">02 / Plans</span><h3>By subscription type</h3></div><span className="panel-icon">↗</span></div><BarList items={subscription} labelKey="subscription_type" valueKey="churn_rate" valueFormatter={formatPercent} /></article>
          <article className="panel"><div className="panel-heading"><div><span className="panel-kicker">03 / Billing</span><h3>By payment method</h3></div><span className="panel-icon">$</span></div><BarList items={payment} labelKey="payment_method" valueKey="churn_rate" valueFormatter={formatPercent} color="gold" /></article>
          <article className="panel region-panel"><div className="panel-heading"><div><span className="panel-kicker">04 / Geography</span><h3>By region</h3></div><span className="panel-icon">◎</span></div><BarList items={region} labelKey="region" valueKey="churn_rate" valueFormatter={formatPercent} color="blue" /></article>
        </section>

        <section className="engagement-section"><div className="section-heading"><div><p className="eyebrow">Behavioral signals</p><h2>Engagement comparison</h2></div><span className="section-caption">Churned vs non-churned customers</span></div><div className="engagement-grid">{engagementRows.map(([label, values]) => <article className="engagement-card" key={label}><span>{label}</span><div className="engagement-values"><div><i className="legend-dot coral" /><strong>{values.churned.mean.toFixed(1)}</strong><small>Churned avg</small></div><div><i className="legend-dot blue" /><strong>{values.non_churned.mean.toFixed(1)}</strong><small>Retained avg</small></div></div><div className="compare-line"><span style={{ width: `${Math.min((values.churned.mean / Math.max(values.churned.mean, values.non_churned.mean)) * 100, 100)}%` }} /><span style={{ width: `${Math.min((values.non_churned.mean / Math.max(values.churned.mean, values.non_churned.mean)) * 100, 100)}%` }} /></div></article>)}</div></section>
      </>}

      <section className="prediction-section"><div className="prediction-intro"><p className="eyebrow">Customer-level analysis</p><h2>Run a churn prediction</h2><p>Enter a customer profile to score churn risk and receive grounded AI guidance.</p><div className="model-badge"><span className="status-dot" /> Model ready <small>Gradient Boosting + InsightWave AI</small></div></div><form className="prediction-form" onSubmit={submitPrediction}><div className="form-grid">{numericFields.map(([name, label]) => <label key={name}>{label}<input name={name} type="number" step="any" min="0" value={form[name]} onChange={updateField} required /></label>)}{selectFields.map(([name, label, options]) => <label key={name}>{label}<select name={name} value={form[name]} onChange={updateField}>{options.map((option) => <option key={option}>{option}</option>)}</select></label>)}</div><button className="submit-button" type="submit" disabled={predicting}>{predicting ? 'Generating AI analysis...' : 'Predict + explain risk'} <span>→</span></button>{predictError && <div className="alert error">{predictError}</div>}{prediction && <div className={`prediction-result ${prediction.risk_level.toLowerCase()}`}><div><span className="result-label">Prediction result</span><strong>{prediction.churn_prediction === 1 ? 'Likely to churn' : 'Likely to stay'}</strong></div><div className="result-stat"><span>Probability</span><strong>{formatPercent(prediction.churn_probability)}</strong></div><div className="risk-tag">{prediction.risk_level} risk</div></div>}{prediction && <div className="ai-insights-result"><div className="ai-result-heading"><span className="result-label">AI interpretation</span><span className="ai-chip">Grounded in profile</span></div><p>{prediction.explanation}</p><div className="ai-columns"><div><h4>Behavioral insights</h4><ul>{prediction.behavioral_insights.map((insight) => <li key={insight}>{insight}</li>)}</ul></div><div><h4>Retention recommendations</h4><ul>{prediction.retention_recommendations.map((recommendation) => <li key={recommendation}>{recommendation}</li>)}</ul></div></div></div>}</form></section>

      <section className="assistant-section"><div className="assistant-heading"><div><p className="eyebrow">Business intelligence assistant</p><h2>Ask InsightWave</h2><p>Ask questions about the actual customer dataset and computed churn analytics.</p></div><InsightWaveMark className="assistant-mark" /></div><div className="assistant-body"><div className="assistant-examples"><span className="examples-label">Try a question</span>{assistantExamples.map((example) => <button key={example} type="button" onClick={() => { setAssistantQuestion(example); askAssistant(null, example) }}>{example}<span>↗</span></button>)}</div><form className="assistant-form" onSubmit={askAssistant}><label htmlFor="assistant-question">Your question</label><div className="assistant-input-row"><input id="assistant-question" value={assistantQuestion} onChange={(event) => { setAssistantQuestion(event.target.value); setAssistantError('') }} placeholder="e.g. Which region has the highest churn?" /><button type="submit" disabled={assistantLoading}>{assistantLoading ? 'Thinking...' : 'Ask'} <span>→</span></button></div>{assistantError && <div className="alert error">{assistantError}</div>}{assistantLoading && <div className="assistant-status">Checking the relevant InsightWave analytics...</div>}{assistantResponse && <div className="assistant-response"><div className="question-echo"><span>You asked</span><strong>{assistantQuestion}</strong></div><div className="answer-block"><span className="result-label">InsightWave answer</span><p>{assistantResponse.answer}</p><div className="data-used"><span>Data used</span>{assistantResponse.data_used.map((item) => <b key={item}>{item}</b>)}</div></div></div>}</form></div></section>
      <footer>InsightWave <span>•</span> Churn intelligence dashboard <span>•</span> Connected to FastAPI</footer>
    </main>
  )
}

createRoot(document.getElementById('root')).render(<StrictMode><App /></StrictMode>)
