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

export async function runScreening(jobId, resumeIds = null, shortlistThreshold = null) {
  const res = await api.post('/screening/run', {
    job_id: jobId,
    resume_ids: resumeIds,
    shortlist_threshold: shortlistThreshold,
  })
  return res.data
}

export async function exportResults(jobId, format = 'csv') {
  const res = await api.get(`/screening/export/${jobId}`, {
    params: { format },
    responseType: 'blob',
  })

  const disposition = res.headers['content-disposition'] || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : `results.${format}`

  const url = window.URL.createObjectURL(res.data)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export default api