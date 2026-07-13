export default function ResultsTable({ results, ready, screening }) {
  // Nothing to show at all until a JD + resumes are both ready
  if (!ready) return null

  return (
    <div className="card">
      <h2>3. Screening Results</h2>

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