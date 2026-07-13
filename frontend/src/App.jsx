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
      // Only screen the resumes uploaded in THIS session — not every
      // resume ever stored in the database from past test runs.
      const resumeIds = resumes.map((r) => r.resume_id)
      const data = await runScreening(job.job_id, resumeIds)
      setResults(data.results)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Screening failed.')
    } finally {
      setScreening(false)
    }
  }

  return (
    <div className="container">
      <header>
        <h1>Smart Resume Screener</h1>
        <p className="subtitle">
          Extract, score, and shortlist candidates against a job description — powered by a local LLM.
        </p>
      </header>

      <UploadJD onJobCreated={setJob} />
      {job && (
        <p className="status-line">
          ✓ Job processed: <strong>{job.extracted.title || 'Untitled Role'}</strong> —{' '}
          {job.extracted.required_skills.length} required skill{job.extracted.required_skills.length === 1 ? '' : 's'} detected
        </p>
      )}

      <UploadResumes onResumesUploaded={(data) => setResumes((prev) => [...prev, ...data])} />
      {resumes.length > 0 && (
        <p className="status-line">
          ✓ {resumes.length} resume{resumes.length > 1 ? 's' : ''} processed and ready
        </p>
      )}

      {job && resumes.length > 0 && (
        <div className="card">
          <button onClick={handleRunScreening} disabled={screening} className="primary">
            {screening && <span className="spinner" />}
            {screening ? 'Scoring candidates…' : `Run Screening on ${resumes.length} Resume${resumes.length > 1 ? 's' : ''}`}
          </button>
          {error && <p className="error">{error}</p>}
        </div>
      )}

      <ResultsTable results={results} screening={screening} ready={Boolean(job && resumes.length > 0)} />
    </div>
  )
}

export default App