import { useState, useEffect, useCallback } from 'react'
import LandingPage from './components/LandingPage'
import UploadJD from './components/UploadJD'
import UploadResumes from './components/UploadResumes'
import ResultsTable from './components/ResultsTable'
import { runScreening } from './api'

function ScreenerApp() {
  const [job, setJob] = useState(null)
  const [resumes, setResumes] = useState([])
  const [results, setResults] = useState([])
  const [threshold, setThreshold] = useState(70)
  const [screening, setScreening] = useState(false)
  const [error, setError] = useState(null)

  const handleRunScreening = async () => {
    if (!job || !resumes.length) return
    setScreening(true)
    setError(null)
    setResults([])
    try {
      const resumeIds = resumes.map((r) => r.resume_id)
      const data = await runScreening(job.job_id, resumeIds, threshold)
      setResults(data.results)
      setThreshold(data.shortlist_threshold)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Screening failed.')
    } finally {
      setScreening(false)
    }
  }

  const handleDeleteResume = (resumeId) => {
    setResumes((prev) => prev.filter((r) => r.resume_id !== resumeId))
    setResults([])
  }

  return (
    <div className="container">
      <header>
        <h1>Smart Resume Screener</h1>
        <p className="subtitle">
          Extract, score, and shortlist candidates against a job description.
        </p>
      </header>

      <UploadJD
        onJobCreated={(data) => { setJob(data); setResults([]) }}
        job={job}
        onClear={() => { setJob(null); setResults([]) }}
      />

      <UploadResumes
        onResumesUploaded={(data) => setResumes((prev) => [...prev, ...data])}
        resumes={resumes}
        onDeleteResume={handleDeleteResume}
        onClearResumes={() => { setResumes([]); setResults([]) }}
      />

      {job && resumes.length > 0 && (
        <div className="card">
          <div style={{ marginBottom: 16 }}>
            <label htmlFor="threshold-slider" style={{ display: 'block', marginBottom: 6, fontWeight: 500 }}>
              Shortlist threshold: {threshold}
            </label>
            <input
              id="threshold-slider"
              type="range"
              min="0"
              max="100"
              step="1"
              value={threshold}
              disabled={screening}
              onChange={(e) => setThreshold(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
          <button onClick={handleRunScreening} disabled={screening} className="primary">
            {screening && <span className="spinner" />}
            {screening ? 'Scoring candidates…' : `Run Screening on ${resumes.length} Resume${resumes.length > 1 ? 's' : ''}`}
          </button>
          {error && <p className="error" style={{ marginTop: 10 }}>{error}</p>}
        </div>
      )}

      <ResultsTable
        results={results}
        screening={screening}
        ready={Boolean(job && resumes.length > 0)}
        threshold={threshold}
        jobId={job?.job_id}
      />
    </div>
  )
}

function getViewFromLocation() {
  return window.location.hash === '#app' ? 'app' : 'landing'
}

function App() {
  const [view, setView] = useState(getViewFromLocation)

  useEffect(() => {
    const handlePopState = () => setView(getViewFromLocation())
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const goToApp = useCallback(() => {
    if (window.location.hash !== '#app') {
      window.history.pushState({ view: 'app' }, '', '#app')
    }
    setView('app')
  }, [])

  if (view === 'landing') {
    return <LandingPage onLaunch={goToApp} />
  }

  return <ScreenerApp />
}

export default App