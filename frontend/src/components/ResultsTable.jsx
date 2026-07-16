import { useState } from 'react'
import { exportResults } from '../api'

export default function ResultsTable({ results, ready, screening, threshold, jobId }) {
  const [exportingFormat, setExportingFormat] = useState(null)

  if (!ready) return null

  const shortlistedCount = results.filter((r) => r.shortlisted).length

  const handleExport = async (format) => {
    setExportingFormat(format)
    try {
      await exportResults(jobId, format)
    } catch (err) {
      console.error('Export failed', err)
    } finally {
      setExportingFormat(null)
    }
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <h2 style={{ margin: 0 }}>
          3. Screening Results
          {threshold != null && !screening && results.length > 0 && (
            <span style={{ fontWeight: 400, fontSize: '0.85em', opacity: 0.7 }}>
              {' '}(shortlist threshold: {threshold})
            </span>
          )}
        </h2>
        {!screening && results.length > 0 && (
          <div className="export-group">
            <button
              className="btn-export"
              onClick={() => handleExport('csv')}
              disabled={exportingFormat !== null}
            >
              {exportingFormat === 'csv' ? (
                <span className="spinner" />
              ) : (
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
                    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
              {exportingFormat === 'csv' ? 'Exporting…' : 'Export CSV'}
            </button>
            <button
              className="btn-export"
              onClick={() => handleExport('json')}
              disabled={exportingFormat !== null}
            >
              {exportingFormat === 'json' ? (
                <span className="spinner" />
              ) : (
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
                    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
              {exportingFormat === 'json' ? 'Exporting…' : 'Export JSON'}
            </button>
          </div>
        )}
      </div>

      {!screening && results.length > 0 && shortlistedCount === 0 && (
        <p className="empty-state" style={{ marginBottom: 12 }}>
          No candidate scored at or above the {threshold} threshold — scores are shown below for reference.
        </p>
      )}

      {screening && (
        <div className="empty-state">
          <span className="spinner" style={{ borderTopColor: 'var(--accent)', borderColor: 'var(--border)', marginBottom: 10 }} />
          <strong>Scoring candidates…</strong>
          Comparing each resume against the job requirements.
        </div>
      )}

      {!screening && results.length === 0 && (
        <div className="empty-state">
          <strong>No results yet</strong>
          Run the screening above to see candidates ranked by match score.
        </div>
      )}

      {!screening && results.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Candidate</th>
              <th>Score</th>
              <th>Status</th>
              <th>Matched Skills</th>
              <th>Missing Skills</th>
              <th>Justification</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.resume_id} className={r.shortlisted ? 'shortlisted' : ''}>
                <td>{r.candidate_name}</td>
                <td className="score-cell">
                  <span className="score-number">{r.score.toFixed(0)}</span>
                  <div className="score-bar-track">
                    <div
                      className={`score-bar-fill ${r.shortlisted ? 'high' : ''}`}
                      style={{ width: `${Math.min(100, Math.max(0, r.score))}%` }}
                    />
                  </div>
                </td>
                <td>
                  <span className={`badge ${r.shortlisted ? 'badge-green' : 'badge-gray'}`}>
                    {r.shortlisted ? 'Shortlisted' : 'Not shortlisted'}
                  </span>
                </td>
                <td>{r.matched_skills.join(', ') || '—'}</td>
                <td>{r.missing_skills.join(', ') || '—'}</td>
                <td className="justification-cell">{r.justification}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}