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
    try {
      const data = await runScreening(job.job_id)
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
        <p className="subtitle">Extract, score, and shortlist candidates against a job description — powered by a local LLM.</p>
      </header>

      <UploadJD onJobCreated={setJob} />
      {job && (
        <p className="status-line">
          ✓ Job processed: <strong>{job.extracted.title || 'Untitled Role'}</strong> —{' '}
          {job.extracted.required_skills.length} required skills detected
        </p>
      )}

      <UploadResumes onResumesUploaded={(data) => setResumes((prev) => [...prev, ...data])} />
      {resumes.length > 0 && (
        <p className="status-line">✓ {resumes.length} resume(s) processed and ready</p>
      )}

      {job && resumes.length > 0 && (
        <div className="card">
          <button onClick={handleRunScreening} disabled={screening} className="primary">
            {screening ? 'Scoring candidates...' : `Run Screening on ${resumes.length} Resume(s)`}
          </button>
        </div>
      )}

      {error && <p className="error">{error}</p>}

      <ResultsTable results={results} />
    </div>
  )
}

export default App
