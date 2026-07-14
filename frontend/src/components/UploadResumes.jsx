import { useState } from 'react'
import { uploadResumesBatch } from '../api'

export default function UploadResumes({ onResumesUploaded, resumes, onDeleteResume, onClearResumes }) {
  const [files, setFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!files.length) return
    setError(null)
    setLoading(true)
    try {
      const data = await uploadResumesBatch(files)
      onResumesUploaded(data)
      setFiles([])
      e.target.reset()
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to process resumes.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>2. Candidate Resumes</h2>

      {resumes.length > 0 && (
        <>
          <div className="uploaded-table-wrap">
            <table className="uploaded-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Candidate</th>
                  <th>Skills Detected</th>
                  <th>Experience</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {resumes.map((r, i) => (
                  <tr key={r.resume_id}>
                    <td className="row-index">{i + 1}</td>
                    <td>
                      <span className="candidate-name">{r.extracted.name || '—'}</span>
                      {r.extracted.email && (
                        <span className="candidate-meta">{r.extracted.email}</span>
                      )}
                    </td>
                    <td>
                      <div className="skills-cell">
                        {r.extracted.skills.slice(0, 5).map((s) => (
                          <span key={s} className="skill-pill">{s}</span>
                        ))}
                        {r.extracted.skills.length > 5 && (
                          <span className="skill-pill muted">+{r.extracted.skills.length - 5} more</span>
                        )}
                      </div>
                    </td>
                    <td>{r.extracted.total_experience_years != null ? `${r.extracted.total_experience_years}y` : '—'}</td>
                    <td>
                      <button className="btn-icon-danger" onClick={() => onDeleteResume(r.resume_id)} title="Remove">
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-actions">
            <button className="btn-ghost-danger" onClick={onClearResumes}>Clear All Resumes</button>
          </div>
        </>
      )}

      <form onSubmit={handleSubmit} style={{ marginTop: resumes.length > 0 ? '16px' : '0' }}>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files))}
        />
        {files.length > 0 && (
          <p className="hint">{files.length} file{files.length > 1 ? 's' : ''} selected</p>
        )}
        <button type="submit" disabled={loading || !files.length}>
          {loading && <span className="spinner" />}
          {loading ? `Extracting ${files.length} resume${files.length > 1 ? 's' : ''}…` : 'Upload & Extract Resumes'}
        </button>
        {error && <p className="error">{error}</p>}
      </form>
    </div>
  )
}