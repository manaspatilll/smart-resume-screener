import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export async function createJobFromFile(file, title) {
  const form = new FormData()
  form.append('file', file)
  if (title) form.append('title', title)
  const res = await api.post('/jobs', form)
  return res.data
}

export async function createJobFromText(text, title) {
  const form = new FormData()
  form.append('text', text)
  if (title) form.append('title', title)
  const res = await api.post('/jobs', form)
  return res.data
}

export async function uploadResumesBatch(files) {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  const res = await api.post('/resumes/batch', form)
  return res.data
}

export async function runScreening(jobId, resumeIds = null) {
  const res = await api.post('/screening/run', {
    job_id: jobId,
    resume_ids: resumeIds,
  })
  return res.data
}

export default api
