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
  const [screening, setScreening] = useState(false)
  const [error, setError] = useState(null)

  const handleRunScreening = async () => {
    if (!job || !resumes.length) return
    setScreening(true)
    setError(null)
    setResults([])
    try {
      const resumeIds = resumes.map((r) => r.resume_id)
      const data = await runScreening(job.job_id, resumeIds)
      setResults(data.results)
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
          <button onClick={handleRunScreening} disabled={screening} className="primary">
            {screening && <span className="spinner" />}
            {screening ? 'Scoring candidates…' : `Run Screening on ${resumes.length} Resume${resumes.length > 1 ? 's' : ''}`}
          </button>
          {error && <p className="error" style={{ marginTop: 10 }}>{error}</p>}
        </div>
      )}

      <ResultsTable results={results} screening={screening} ready={Boolean(job && resumes.length > 0)} />
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