import { useEffect, useMemo, useState } from 'react'
import dayjs from 'dayjs'
import { addTask, fetchTasks, markDone, removeTask, reopenTask } from './api'
import './App.css'

const initialForm = { description: '', details: '', due_date: '' }

function App() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)

  const hasTasks = useMemo(() => tasks.length > 0, [tasks])

  useEffect(() => {
    loadTasks()
  }, [])

  async function loadTasks() {
    setLoading(true)
    setError('')
    try {
      const data = await fetchTasks()
      setTasks(data.tasks || [])
    } catch (err) {
      setError(err.message || 'Failed to load tasks')
    } finally {
      setLoading(false)
    }
  }

  function handleChange(event) {
    const { name, value } = event.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  async function handleAdd(event) {
    event.preventDefault()
    if (!form.description.trim()) {
      setError('Description is required')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await addTask({
        description: form.description.trim(),
        details: form.details.trim(),
        due_date: form.due_date || null,
      })
      setForm(initialForm)
      await loadTasks()
    } catch (err) {
      setError(err.message || 'Failed to add task')
    } finally {
      setSubmitting(false)
    }
  }

  async function handleDone(id) {
    setError('')
    try {
      await markDone(id)
      await loadTasks()
    } catch (err) {
      setError(err.message || 'Failed to mark task as done')
    }
  }

  async function handleRemove(id) {
    setError('')
    try {
      await removeTask(id)
      await loadTasks()
    } catch (err) {
      setError(err.message || 'Failed to remove task')
    }
  }

  async function handleReopen(id) {
    setError('')
    try {
      await reopenTask(id)
      await loadTasks()
    } catch (err) {
      setError(err.message || 'Failed to reopen task')
    }
  }

  return (
    <div className="page">
      <header className="header">
        <div>
          <p className="eyebrow">Flask + SQLite</p>
          <h1>Todo Dashboard</h1>
          <p className="subtitle">
            Add tasks, mark them done, or remove them via the Flask API.
          </p>
        </div>
      </header>

      <section className="panel">
        <h2>Add a task</h2>
        <form className="form" onSubmit={handleAdd}>
          <label className="field">
            <span>Description*</span>
            <input
              type="text"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder="Walk the dog"
              required
            />
          </label>
          <label className="field">
            <span>Details</span>
            <textarea
              name="details"
              value={form.details}
              onChange={handleChange}
              placeholder="Add any notes…"
              rows={3}
            />
          </label>
          <label className="field">
            <span>Due date</span>
            <input
              type="date"
              name="due_date"
              value={form.due_date}
              onChange={handleChange}
            />
          </label>
          <div className="actions">
            <button type="submit" disabled={submitting}>
              {submitting ? 'Saving…' : 'Add task'}
            </button>
            <button type="button" className="ghost" onClick={loadTasks}>
              Refresh list
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Tasks</h2>
          {loading && <span className="pill">Loading…</span>}
        </div>
        {error && <div className="error">{error}</div>}
        {!loading && !hasTasks && <p className="muted">No tasks yet.</p>}
        <div className="task-grid">
          {tasks.map((task) => {
            const due = task.due_date
              ? dayjs(task.due_date).format('YYYY-MM-DD')
              : 'No due date'
            return (
              <article
                key={task.id}
                className={`task ${task.completed ? 'done' : ''}`}
              >
                <div className="task-head">
                  <div>
                    <p className="task-id">#{task.id}</p>
                    <h3>{task.description}</h3>
                  </div>
                  <span className="pill">
                    {task.completed ? 'Done' : 'Open'}
                  </span>
                </div>
                {task.details && <p className="muted">{task.details}</p>}
                <p className="due">Due: {due}</p>
                <div className="task-actions">
                  {!task.completed ? (
                    <button type="button" onClick={() => handleDone(task.id)}>
                      Mark done
                    </button>
                  ) : (
                    <button type="button" onClick={() => handleReopen(task.id)}>
                      Reopen
                    </button>
                  )}
                  <button
                    type="button"
                    className="ghost"
                    onClick={() => handleRemove(task.id)}
                  >
                    Remove
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}

export default App
