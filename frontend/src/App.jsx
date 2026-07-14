import { useState } from 'react'
import UploadJD from './components/UploadJD'
import UploadResumes from './components/UploadResumes'
import ResultsTable from './components/ResultsTable'
import { runScreening } from './api'

function App() {
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
          Extract, score, and shortlist candidates against a job description — powered by a local LLM.
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

export default App