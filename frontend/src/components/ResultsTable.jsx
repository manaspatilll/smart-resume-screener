export default function ResultsTable({ results }) {
  if (!results || !results.length) return null

  return (
    <div className="card">
      <h2>3. Screening Results</h2>
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
              <td className="score-cell">{r.score.toFixed(0)}</td>
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
    </div>
  )
}
