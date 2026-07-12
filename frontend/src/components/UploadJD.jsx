import { useState } from 'react'
import { createJobFromFile, createJobFromText } from '../api'

export default function UploadJD({ onJobCreated }) {
  const [mode, setMode] = useState('text') // 'text' | 'file'
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
          {loading ? 'Extracting...' : 'Process Job Description'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  )
}
