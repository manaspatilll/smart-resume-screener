import re
from datetime import datetime
from dateutil import parser as date_parser


SKILL_KEYWORDS = [
    # Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C", "Go", "Golang",
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Perl",
    "SQL", "HTML", "CSS", "Bash", "Shell Scripting",
    # Frameworks / Libraries
    "React", "Angular", "Vue.js", "Next.js", "Node.js", "Express.js", "Express",
    "Django", "Flask", "FastAPI", "Spring", "Spring Boot", ".NET", "ASP.NET",
    "Ruby on Rails", "jQuery", "Bootstrap", "Tailwind", "Redux",
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Pandas", "NumPy",
    "OpenCV", "Hugging Face", "NLTK", "spaCy",
    # Databases
    "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Redis", "Oracle", "Cassandra",
    "DynamoDB", "Firebase", "Supabase", "MariaDB", "Elasticsearch", "Neo4j", "RDBMS",
    # Cloud / DevOps
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Jenkins",
    "CI/CD", "Terraform", "Ansible", "Git", "GitHub", "GitLab", "Bitbucket",
    "Linux", "Nginx", "Apache",
    # Concepts
    "OOP", "Object-Oriented Programming", "Data Structures", "Algorithms", "DSA",
    "REST API", "RESTful", "GraphQL", "Microservices", "Agile", "Scrum", "SDLC",
    "Waterfall", "TDD", "Unit Testing", "System Design", "Machine Learning",
    "Deep Learning", "NLP", "Computer Vision", "Neural Networks", "CNN", "RNN",
    "LSTM", "Random Forest", "Linear Regression", "Logistic Regression", "K-Means",
    "Clustering", "Zero-Shot Learning", "Reinforcement Learning", "Multi-threading",
    "Multithreading", "Concurrency", "Application Security", "Cybersecurity",
    "Code Analysis", "Operating System", "Networking", "Distributed Systems",
    "Blockchain", "Web Development", "Mobile Development", "Cloud Computing",
    "Big Data", "Data Engineering", "ETL", "Data Pipelines", "Data Analysis",
    "Data Visualization", "Business Intelligence", "QA", "Quality Assurance",
    "Manual Testing", "Automation Testing", "Selenium", "Postman", "JIRA",
    "Excel", "PowerBI", "Tableau",
    # Tools
    "Jupyter", "Google Colab", "VS Code", "IntelliJ", "Eclipse", "Figma",
]

_SKILL_KEYWORDS_LOWER = sorted(set(s.lower() for s in SKILL_KEYWORDS), key=len, reverse=True)

MONTH_YEAR_RANGE_RE = re.compile(
    r'([A-Za-z]{3,9}\.?\s+\d{4})\s*(?:-|–|—|to)\s*(Present|Current|Ongoing|[A-Za-z]{3,9}\.?\s+\d{4})',
    re.IGNORECASE,
)
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_RE = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?\d{10}\b')
YEARS_EXPERIENCE_RE = re.compile(
    r'(\d+)\s*(?:\+|-)?\s*(?:to\s*\d+)?\s*\+?\s*years?\s*(?:of)?\s*experience',
    re.IGNORECASE,
)
DEGREE_KEYWORDS = [
    "B.Tech", "B.E.", "BE", "BTech", "M.Tech", "MTech", "MBA", "Bachelor",
    "Master", "PhD", "B.Sc", "M.Sc", "BCA", "MCA", "Diploma", "B.A.", "M.A.",
]

SECTION_HEADER_RE = re.compile(r'^[A-Z][A-Z\s\-&/]{2,40}$')

REQUIRED_MARKERS = ["must have", "required", "mandatory", "essential"]
PREFERRED_MARKERS = ["nice to have", "preferred", "good to have", "desirable", "plus", "bonus", "optional"]


def _find_skills_in_text(text: str) -> list:
    """Whole-word/phrase match against the skill taxonomy — same lookaround
    technique used in the skill-matching logic elsewhere, so 'C' doesn't
    match inside 'concepts' and 'Java' doesn't match inside 'JavaScript'."""
    text_lower = text.lower()
    found = []
    for skill_lower in _SKILL_KEYWORDS_LOWER:
        pattern = r'(?<![a-z0-9])' + re.escape(skill_lower) + r'(?![a-z0-9])'
        if re.search(pattern, text_lower):
            for original in SKILL_KEYWORDS:
                if original.lower() == skill_lower:
                    found.append(original)
                    break
    return found


def _split_into_sections(text: str) -> dict:
    """Split resume text into sections keyed by header name, based on the
    common resume convention of ALL-CAPS section headers on their own line
    (EDUCATION, EXPERIENCE, PROJECTS, EXTRA-CURRICULAR, etc.). This is what
    lets us structurally exclude extracurricular roles from experience
    calculations, rather than relying on an LLM to remember not to count
    them."""
    lines = text.split('\n')
    sections = {}
    current_header = "HEADER"
    current_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and SECTION_HEADER_RE.match(stripped) and len(stripped.split()) <= 6:
            sections[current_header] = '\n'.join(current_lines)
            current_header = stripped.upper()
            current_lines = []
        else:
            current_lines.append(line)
    sections[current_header] = '\n'.join(current_lines)
    return sections


def _parse_month_year(value: str):
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if value.lower() in ("present", "current", "now", "ongoing", "till date"):
        return datetime.today()
    try:
        return date_parser.parse(value, default=datetime(1900, 1, 1))
    except (ValueError, OverflowError):
        return None


def _compute_experience_years(experience_entries: list) -> float:
    total_months = 0
    for entry in experience_entries:
        start = _parse_month_year(entry.get("start_date", ""))
        end = _parse_month_year(entry.get("end_date", ""))
        if not start or not end:
            continue
        months = (end.year - start.year) * 12 + (end.month - start.month)
        if months > 0:
            total_months += months
    return round(total_months / 12, 2)


def extract_resume_fields(text: str) -> dict:
    sections = _split_into_sections(text)

    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    name = None
    for line in text.split('\n'):
        stripped = line.strip()
        if stripped and len(stripped) < 50 and not any(c.isdigit() for c in stripped) and '@' not in stripped:
            name = stripped
            break

    skills = _find_skills_in_text(text)

    # (EXPERIENCE / WORK EXPERIENCE / PROFESSIONAL EXPERIENCE) — explicitly
    # NOT from EXTRA-CURRICULAR, PROJECTS, or EDUCATION sections.
    experience_entries = []
    job_titles = []
    for header, content in sections.items():
        header_norm = header.upper()
        is_experience_section = "EXPERIENCE" in header_norm and "EXTRA" not in header_norm
        if not is_experience_section:
            continue
        lines = content.split('\n')
        for i, line in enumerate(lines):
            match = MONTH_YEAR_RANGE_RE.search(line)
            if match:
                role_text = line[:match.start()].strip(' -–—|\t')
                if not role_text and i > 0:
                    role_text = lines[i - 1].strip()
                if role_text:
                    job_titles.append(role_text)
                experience_entries.append({
                    "role": role_text or "Unspecified role",
                    "start_date": match.group(1),
                    "end_date": match.group(2),
                })

    total_experience_years = _compute_experience_years(experience_entries)

    # Education: degree-keyword lines within the EDUCATION section
    education = []
    edu_section = sections.get("EDUCATION", "")
    for line in edu_section.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        if any(kw.lower() in stripped.lower() for kw in DEGREE_KEYWORDS):
            year_match = re.search(r'(\d{4})', stripped)
            education.append({
                "degree": stripped,
                "institution": None,
                "year": year_match.group(1) if year_match else None,
            })
    if not education and edu_section.strip():
        first_line = next((l.strip() for l in edu_section.split('\n') if l.strip()), None)
        if first_line:
            education.append({"degree": first_line, "institution": None, "year": None})

    return {
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "skills": skills,
        "total_experience_years": total_experience_years,
        "job_titles": job_titles,
        "education": education,
        "raw_text": text,
    }


def extract_jd_fields(text: str) -> dict:
    lines = text.split('\n')
    required_skills = set()
    preferred_skills = set()

    for line in lines:
        line_lower = line.lower()
        line_skills = _find_skills_in_text(line)
        if not line_skills:
            continue
        if any(marker in line_lower for marker in PREFERRED_MARKERS):
            preferred_skills.update(line_skills)
        elif any(marker in line_lower for marker in REQUIRED_MARKERS):
            required_skills.update(line_skills)
        else:
            # no explicit marker — default to required, since most bare JD
            # bullets describe baseline expectations, not optional extras
            required_skills.update(line_skills)

    preferred_skills -= required_skills

    min_experience = 0
    exp_matches = YEARS_EXPERIENCE_RE.findall(text)
    if exp_matches:
        min_experience = min(int(m) for m in exp_matches if m)
    else:
        range_match = re.search(r'(\d+)\s*-\s*(\d+)\s*years?', text, re.IGNORECASE)
        if range_match:
            min_experience = int(range_match.group(1))

    education_requirement = None
    for kw in DEGREE_KEYWORDS:
        if kw.lower() in text.lower():
            for line in lines:
                if kw.lower() in line.lower():
                    education_requirement = line.strip()
                    break
            break

    title = next((line.strip() for line in lines if line.strip()), None)

    return {
        "title": title,
        "required_skills": sorted(required_skills),
        "preferred_skills": sorted(preferred_skills),
        "min_experience_years": min_experience,
        "education_requirement": education_requirement,
        "raw_text": text,
    }