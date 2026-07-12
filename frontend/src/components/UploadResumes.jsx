import { useState } from 'react'
import { uploadResumesBatch } from '../api'

export default function UploadResumes({ onResumesUploaded }) {
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
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to process resumes.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>2. Candidate Resumes</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          multiple
          onChange={(e) => setFiles(Array.from(e.target.files))}
        />
        {files.length > 0 && <p className="hint">{files.length} file(s) selected</p>}
        <button type="submit" disabled={loading || !files.length}>
          {loading ? 'Extracting...' : 'Upload & Extract Resumes'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  )
}
