import { useState } from 'react'
import { createJobFromFile, createJobFromText } from '../api'

export default function UploadJD({ onJobCreated, job, onClear }) {
  const [mode, setMode] = useState('text')
  const [text, setText] = useState('')
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data =
        mode === 'file'
          ? await createJobFromFile(file, title)
          : await createJobFromText(text, title)
      onJobCreated(data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to process job description.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>1. Job Description</h2>

      {job ? (
        <>
          <div className="uploaded-table-wrap">
            <table className="uploaded-table">
              <thead>
                <tr>
                  <th>Role</th>
                  <th>Required Skills</th>
                  <th>Preferred Skills</th>
                  <th>Min. Experience</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>{job.extracted.title || 'Untitled Role'}</strong></td>
                  <td>{job.extracted.required_skills.join(', ') || '—'}</td>
                  <td>{job.extracted.preferred_skills.join(', ') || '—'}</td>
                  <td>{job.extracted.min_experience_years ? `${job.extracted.min_experience_years}y` : '—'}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="table-actions">
            <button className="btn-ghost-danger" onClick={() => {
              setText('')
              setTitle('')
              setFile(null)
              setError(null)
              onClear()
            }}>Clear JD</button>
          </div>
        </>
      ) : (
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Role title (optional)"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <div className="mode-toggle">
            <button type="button" className={mode === 'text' ? 'active' : ''} onClick={() => setMode('text')}>
              Paste Text
            </button>
            <button type="button" className={mode === 'file' ? 'active' : ''} onClick={() => setMode('file')}>
              Upload File
            </button>
          </div>
          {mode === 'text' ? (
            <textarea
              rows={8}
              placeholder="Paste the job description here..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          ) : (
            <input
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setFile(e.target.files[0])}
            />
          )}
          <button type="submit" disabled={loading || (mode === 'text' ? !text : !file)}>
            {loading && <span className="spinner" />}
            {loading ? 'Extracting requirements…' : 'Process Job Description'}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      )}
    </div>
  )
}