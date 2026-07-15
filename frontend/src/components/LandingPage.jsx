function IconExtract() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M6 3h9l4 4v14a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" strokeLinejoin="round" />
      <path d="M14 3v4a1 1 0 0 0 1 1h4" strokeLinejoin="round" />
      <path d="M8.5 12.5h7M8.5 15.5h7M8.5 18h4" strokeLinecap="round" />
    </svg>
  )
}

function IconMatch() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <circle cx="9" cy="9" r="5.5" />
      <circle cx="15" cy="15" r="5.5" />
    </svg>
  )
}

function IconScore() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M4 19V11M12 19V5M20 19v-7" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 19h18" strokeLinecap="round" />
    </svg>
  )
}

function IconBolt() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M13 3 5 13.5h5.5L11 21l8-10.5h-5.5L13 3Z" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

const FEATURES = [
  {
    icon: <IconExtract />,
    title: 'Deterministic extraction',
    body: 'Skills, experience, education, and titles are parsed with rule-based matching against a curated taxonomy — the same approach real ATS platforms use. No LLM guesswork, no dropped fields.',
  },
  
  {
    icon: <IconScore />,
    title: 'LLM-grounded scoring',
    body: 'The model reasons only over confirmed matched/missing skills and experience — producing a 0–100 score with a written justification a hiring manager can trust.',
  },
  {
    icon: <IconBolt />,
    title: 'Built for speed',
    body: 'Groq-backed inference returns a full screening pass in seconds, not minutes — extraction and matching are near-instant Python, so nothing waits on a slow model.',
  },
]

const STEPS = [
  { n: '01', title: 'Upload', body: 'Paste or upload a job description, then add one or more candidate resumes.' },
  { n: '02', title: 'Extract', body: 'Skills, experience, and education are pulled from every document.' },
  { n: '03', title: 'Match & score', body: 'Skills are compared deterministically, then scored 0–100 with a written rationale.' },
  { n: '04', title: 'Shortlist', body: 'Candidates above your threshold are flagged automatically, ranked by score.' },
]

export default function LandingPage({ onLaunch }) {
  return (
    <div className="landing">
      <div className="landing-container">
        <header className="landing-nav">
          <div className="landing-wordmark">
            <span className="landing-wordmark-mark">SRS</span>
            <span className="landing-wordmark-text">Smart Resume Screener</span>
          </div>
          <button className="landing-nav-cta" onClick={onLaunch}>
            Launch app
          </button>
        </header>

        <section className="landing-hero">
          <div className="landing-hero-copy">
            <h1>
              Structured Screening.
              <br />
              <span className="landing-accent-text">Grounded Scores.</span>
            </h1>
            <p className="landing-subhead">
              Extract structured data from resumes and job descriptions, match skills
              deterministically, and let an LLM explain the score — grounded in confirmed
              facts, never invented ones.
            </p>
            <div className="landing-hero-actions">
              <button className="landing-cta-primary" onClick={onLaunch}>
                Start screening
                <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M4 10h12M11 5l5 5-5 5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
          </div>

          <div className="landing-hero-visual" aria-hidden="true">
            <div className="landing-mock-card">
              <div className="landing-mock-row">
                <div>
                  <span className="landing-mock-name">Candidate — S. Rao</span>
                  <span className="landing-mock-meta">4.5 yrs · B.Tech CSE</span>
                </div>
                <span className="landing-mock-badge">Shortlisted</span>
              </div>
              <div className="landing-mock-score">
                <span className="landing-mock-score-num">87</span>
                <div className="landing-mock-bar-track">
                  <div className="landing-mock-bar-fill" style={{ width: '87%' }} />
                </div>
              </div>
              <div className="landing-mock-pills">
                <span className="landing-mock-pill">React</span>
                <span className="landing-mock-pill">Node.js</span>
                <span className="landing-mock-pill">PostgreSQL</span>
                <span className="landing-mock-pill muted">Docker (inferred)</span>
              </div>
              <p className="landing-mock-justification">
                "Strong overlap on required backend skills with 4.5 years exceeding the
                3-year minimum. Docker experience reasonably implied by containerized
                deployment work."
              </p>
            </div>
          </div>
        </section>

        <section className="landing-features">
          <h2 className="landing-section-label">Key Features</h2>
          <div className="landing-feature-grid">
            {FEATURES.map((f) => (
              <div className="landing-feature-card" key={f.title}>
                <div className="landing-feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.body}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="landing-steps">
          <h2 className="landing-section-label">How it works</h2>
          <div className="landing-steps-row">
            {STEPS.map((s, i) => (
              <div className="landing-step" key={s.n}>
                <span className="landing-step-num">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.body}</p>
                {i < STEPS.length - 1 && <span className="landing-step-connector" aria-hidden="true" />}
              </div>
            ))}
          </div>
        </section>

        <section className="landing-final-cta">
          <h2>Ready to screen your first batch?</h2>
          <p>Upload a job description and a few resumes — get ranked, justified results in seconds.</p>
          <button className="landing-cta-primary" onClick={onLaunch}>
            Launch the screener
          </button>
        </section>
      </div>
    </div>
  )
}