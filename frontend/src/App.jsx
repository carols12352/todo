import { useEffect, useMemo, useRef, useState } from 'react'
import dayjs from 'dayjs'
import {
  addTask,
  fetchTasks,
  markDone,
  removeTask,
  reopenTask,
  updateTask,
  fetchSettings,
  saveSettings,
  parseAi,
  warmAi,
  unloadAi,
} from './api'
import './App.css'

const initialForm = {
  description: '',
  details: '',
  due_date: '',
  due_time: '',
  all_day: true,
  category: 'personal',
  priority: 'medium',
  color: '#0f766e',
}

const CATEGORY_LABELS = {
  en: {
    work: 'Work',
    study: 'Study',
    personal: 'Personal',
  },
  zh: {
    work: '工作',
    study: '学习',
    personal: '个人',
  },
}

const PRIORITY_LABELS = {
  en: {
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  },
  zh: {
    high: '高',
    medium: '中',
    low: '低',
  },
}

const PRIORITY_COLORS = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#10b981',
}

const STRINGS = {
  en: {
    eyebrow: 'Daily Focus',
    title: 'My Tasks',
    subtitle: 'Stay on top of work, study, and personal goals.',
    language: 'Language',
    addTask: 'Add task',
    titleLabel: 'Title*',
    titlePlaceholder: 'Prepare weekly report',
    details: 'Details',
    detailsPlaceholder: 'Add notes or links...',
    category: 'Category',
    priority: 'Priority',
    color: 'Color',
    quickDate: 'Quick date',
    quickDateNone: 'No shortcut',
    quickDateCustom: 'Custom',
    today: 'Today',
    tomorrow: 'Tomorrow',
    next3Days: 'Next 3 days',
    nextWeek: 'Next week',
    dueDate: 'Due date',
    add: 'Add task',
    saving: 'Saving...',
    refresh: 'Refresh list',
    tasks: 'Tasks',
    itemsCount: (count, open) => `${count} items • ${open} open`,
    all: 'All',
    open: 'Open',
    done: 'Done',
    searchPlaceholder: 'Search title or details...',
    allCategories: 'All categories',
    allPriorities: 'All priorities',
    loading: 'Loading...',
    noTasks: 'No tasks yet.',
    noDueDate: 'No due date',
    due: 'Due',
    complete: 'Complete',
    reopen: 'Reopen',
    edit: 'Edit',
    delete: 'Delete',
    save: 'Save',
    cancel: 'Cancel',
    pastDueConfirm: 'Due date is in the past. Add anyway and mark it done?',
    allDay: 'All day',
    time: 'Time',
    aiTitle: 'AI Assistant',
    aiHint: 'Describe your task or command...',
    aiSend: 'Send',
    aiEditTitle: 'Review AI Draft',
    aiApply: 'Apply',
    aiCancel: 'Cancel',
    aiAction: 'Suggested action',
    aiTarget: 'Target task',
    aiNoDraft: 'No editable fields for this action.',
    aiRunAction: 'Run action',
  },
  zh: {
    eyebrow: '日常管理',
    title: '我的任务',
    subtitle: '更清晰地管理工作、学习与生活。',
    language: '语言',
    addTask: '新增任务',
    titleLabel: '标题*',
    titlePlaceholder: '准备周报',
    details: '详情',
    detailsPlaceholder: '可填写备注或链接...',
    category: '分类',
    priority: '优先级',
    color: '颜色',
    quickDate: '快捷日期',
    quickDateNone: '不使用',
    quickDateCustom: '自定义',
    today: '今天',
    tomorrow: '明天',
    next3Days: '未来三天',
    nextWeek: '下周',
    dueDate: '截止日期',
    add: '添加任务',
    saving: '保存中...',
    refresh: '刷新列表',
    tasks: '任务列表',
    itemsCount: (count, open) => `${count} 条 • ${open} 未完成`,
    all: '全部',
    open: '未完成',
    done: '已完成',
    searchPlaceholder: '搜索标题或详情...',
    allCategories: '全部分类',
    allPriorities: '全部优先级',
    loading: '加载中...',
    noTasks: '暂无任务。',
    noDueDate: '无截止',
    due: '截止',
    complete: '完成',
    reopen: '重新打开',
    edit: '编辑',
    delete: '删除',
    save: '保存',
    cancel: '取消',
    pastDueConfirm: '截止日期早于今天，是否仍要添加并自动标记为完成？',
    allDay: '全天',
    time: '时间',
    aiTitle: 'AI 助手',
    aiHint: '描述你的任务或指令...',
    aiSend: '发送',
    aiEditTitle: '确认 AI 结果',
    aiApply: '应用',
    aiCancel: '取消',
    aiAction: '建议动作',
    aiTarget: '目标任务',
    aiNoDraft: '该动作没有可编辑内容。',
    aiRunAction: '执行动作',
  },
}

function App() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [language, setLanguage] = useState('en')
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [statusFilter, setStatusFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [priorityFilter, setPriorityFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editForm, setEditForm] = useState(initialForm)
  const [editing, setEditing] = useState(false)
  const [settingLang, setSettingLang] = useState(false)
  const [quickDatePreset, setQuickDatePreset] = useState('')
  const [aiOpen, setAiOpen] = useState(false)
  const [aiInput, setAiInput] = useState('')
  const [aiMessages, setAiMessages] = useState([])
  const [aiDraft, setAiDraft] = useState(null)
  const [aiDraftForm, setAiDraftForm] = useState(initialForm)
  const [aiBusy, setAiBusy] = useState(false)
  const [aiError, setAiError] = useState('')
  const [aiPosition, setAiPosition] = useState(null)
  const [aiPanelShift, setAiPanelShift] = useState({ x: 0, y: 0 })
  const aiWidgetRef = useRef(null)
  const aiPanelRef = useRef(null)
  const dragStateRef = useRef({ active: false, offsetX: 0, offsetY: 0 })
  const dragClickBlockRef = useRef(0)

  const hasTasks = useMemo(() => tasks.length > 0, [tasks])
  const completedCount = useMemo(
    () => tasks.filter((task) => task.completed).length,
    [tasks]
  )
  const openCount = useMemo(
    () => tasks.length - completedCount,
    [tasks, completedCount]
  )
  const filteredTasks = useMemo(() => {
    const keyword = searchTerm.trim().toLowerCase()
    return tasks.filter((task) => {
      if (statusFilter === 'open' && task.completed) return false
      if (statusFilter === 'done' && !task.completed) return false
      if (categoryFilter !== 'all' && task.category !== categoryFilter) return false
      if (priorityFilter !== 'all' && task.priority !== priorityFilter) return false
      if (!keyword) return true
      const haystack = `${task.description} ${task.details || ''}`.toLowerCase()
      return haystack.includes(keyword)
    })
  }, [tasks, statusFilter, categoryFilter, priorityFilter, searchTerm])

  const groupedTasks = useMemo(() => {
    const groups = {
      work: [],
      study: [],
      personal: [],
    }
    filteredTasks.forEach((task) => {
      const key = task.category || 'personal'
      if (!groups[key]) {
        groups[key] = []
      }
      groups[key].push(task)
    })
    return groups
  }, [filteredTasks])

  useEffect(() => {
    loadSettings()
    loadTasks()
  }, [])

  useEffect(() => {
    if (aiOpen) {
      warmAi().catch(() => {})
    } else {
      unloadAi().catch(() => {})
    }
  }, [aiOpen])


  useEffect(() => {
    function adjustPanelPosition() {
      if (!aiOpen || !aiPanelRef.current) return
      const rect = aiPanelRef.current.getBoundingClientRect()
      const overflowRight = Math.max(0, rect.right - (window.innerWidth - 8))
      const overflowLeft = Math.max(0, 8 - rect.left)
      const overflowBottom = Math.max(0, rect.bottom - (window.innerHeight - 8))
      const overflowTop = Math.max(0, 8 - rect.top)
      const shiftX = overflowRight > 0 ? overflowRight : overflowLeft > 0 ? -overflowLeft : 0
      const shiftY = overflowBottom > 0 ? overflowBottom : overflowTop > 0 ? -overflowTop : 0
      setAiPanelShift({ x: shiftX, y: shiftY })
    }

    adjustPanelPosition()
    window.addEventListener('resize', adjustPanelPosition)
    return () => {
      window.removeEventListener('resize', adjustPanelPosition)
    }
  }, [aiOpen, aiPosition])

  useEffect(() => {
    function handleMove(event) {
      if (!dragStateRef.current.active) return
      const x = event.clientX - dragStateRef.current.offsetX
      const y = event.clientY - dragStateRef.current.offsetY
      const moved =
        Math.abs(event.clientX - dragStateRef.current.startX) > 3 ||
        Math.abs(event.clientY - dragStateRef.current.startY) > 3
      if (moved) dragStateRef.current.moved = true
      const rect = aiWidgetRef.current?.getBoundingClientRect()
      const widgetWidth = rect?.width || 80
      const widgetHeight = rect?.height || 80
      const maxX = window.innerWidth - widgetWidth - 8
      const maxY = window.innerHeight - widgetHeight - 8
      const clampedX = Math.min(Math.max(8, x), Math.max(8, maxX))
      const clampedY = Math.min(Math.max(8, y), Math.max(8, maxY))
      setAiPosition({ x: clampedX, y: clampedY })
    }

    function handleUp() {
      if (dragStateRef.current.moved) {
        dragClickBlockRef.current = Date.now() + 200
      }
      dragStateRef.current.active = false
    }

    window.addEventListener('pointermove', handleMove)
    window.addEventListener('pointerup', handleUp)
    return () => {
      window.removeEventListener('pointermove', handleMove)
      window.removeEventListener('pointerup', handleUp)
    }
  }, [])

  function startAiDrag(event) {
    if (!aiWidgetRef.current) return
    const rect = aiWidgetRef.current.getBoundingClientRect()
    dragStateRef.current = {
      active: true,
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top,
      startX: event.clientX,
      startY: event.clientY,
      moved: false,
    }
  }

  async function loadSettings() {
    try {
      const data = await fetchSettings()
      if (data?.language) {
        setLanguage(data.language)
      }
    } catch (err) {
      setLanguage('en')
    }
  }

  async function persistLanguage(nextLanguage) {
    setLanguage(nextLanguage)
    try {
      await saveSettings(nextLanguage)
    } catch (err) {
      // Ignore write failures; UI still updates.
    }
  }

  async function loadTasks() {
    const scrollY = window.scrollY
    setLoading(true)
    setError('')
    try {
      const data = await fetchTasks()
      setTasks(data.tasks || [])
    } catch (err) {
      setError(err.message || 'Failed to load tasks')
    } finally {
      setLoading(false)
      requestAnimationFrame(() => {
        window.scrollTo({ top: scrollY })
      })
    }
  }

  function buildDatetimePayload({ due_date, due_time, all_day }) {
    if (!due_date) {
      return { all_day: null, datetime: null }
    }
    const hasTime = Boolean(due_time)
    let resolvedAllDay = all_day ?? !hasTime
    if (!hasTime && resolvedAllDay === false) {
      resolvedAllDay = true
    }
    if (resolvedAllDay) {
      return { all_day: true, datetime: due_date }
    }
    return { all_day: false, datetime: `${due_date}T${due_time}` }
  }

  function extractTime(datetimeValue) {
    if (!datetimeValue) return ''
    const parts = datetimeValue.split('T')
    if (parts.length < 2) return ''
    return parts[1].slice(0, 5)
  }

  function normalizeAiDraft(result) {
    const patch = result?.task_patch || {}
    const action = result?.action || 'add'
    const targetId = result?.target?.id ?? null
    const hasTime = Boolean(patch.due_time)
    const normalizedDueDate =
      !patch.due_date && hasTime ? dayjs().format('YYYY-MM-DD') : patch.due_date
    const resolvedAllDay =
      patch.all_day !== null && patch.all_day !== undefined
        ? patch.all_day
        : normalizedDueDate
          ? !hasTime
          : null

    return {
      action,
      targetId,
      form: {
        description: patch.description || '',
        details: patch.details || '',
        due_date: normalizedDueDate || '',
        due_time: patch.due_time || '',
        all_day:
          hasTime
            ? false
            : resolvedAllDay === null
              ? true
              : resolvedAllDay,
        category: patch.category || 'personal',
        priority: patch.priority || 'medium',
        color: patch.color || PRIORITY_COLORS[patch.priority] || '#0f766e',
      },
    }
  }

  function handleChange(event) {
    const { name, value, type, checked } = event.target
    const nextValue = type === 'checkbox' ? checked : value
    setForm((prev) => {
      const next = { ...prev, [name]: nextValue }
      if (name === 'all_day' && checked) {
        next.due_time = ''
      }
      if (name === 'all_day' && !checked && !next.due_date) {
        next.due_date = dayjs().format('YYYY-MM-DD')
      }
      if (name === 'due_time' && value) {
        next.all_day = false
        if (!next.due_date) {
          next.due_date = dayjs().format('YYYY-MM-DD')
        }
      }
      return next
    })
  }

  function handleEditChange(event) {
    const { name, value, type, checked } = event.target
    const nextValue = type === 'checkbox' ? checked : value
    setEditForm((prev) => {
      const next = { ...prev, [name]: nextValue }
      if (name === 'all_day' && checked) {
        next.due_time = ''
      }
      if (name === 'all_day' && !checked && !next.due_date) {
        next.due_date = dayjs().format('YYYY-MM-DD')
      }
      if (name === 'due_time' && value) {
        next.all_day = false
        if (!next.due_date) {
          next.due_date = dayjs().format('YYYY-MM-DD')
        }
      }
      return next
    })
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
      const today = dayjs().startOf('day')
      const hasPastDue =
        form.due_date && dayjs(form.due_date).isBefore(today, 'day')
      let markDoneAfterAdd = false
      if (hasPastDue) {
        const confirmPastDue = window.confirm(t('pastDueConfirm'))
        if (!confirmPastDue) {
          return
        }
        markDoneAfterAdd = true
      }
      const { all_day, datetime } = buildDatetimePayload(form)

      const result = await addTask({
        description: form.description.trim(),
        details: form.details.trim(),
        due_date: form.due_date || null,
        all_day,
        datetime,
        category: form.category,
        priority: form.priority,
        color: form.color || null,
      })
      if (markDoneAfterAdd && result?.task_id) {
        await markDone(result.task_id)
      }
      setForm(initialForm)
      setQuickDatePreset('')
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

  function startEdit(task) {
    setEditingId(task.id)
    const taskTime = extractTime(task.datetime)
    const resolvedAllDay =
      task.all_day !== null && task.all_day !== undefined
        ? task.all_day
        : taskTime
          ? false
          : true
    setEditForm({
      description: task.description || '',
      details: task.details || '',
      due_date: task.due_date || '',
      due_time: taskTime,
      all_day: resolvedAllDay,
      category: task.category || 'personal',
      priority: task.priority || 'medium',
      color: task.color || PRIORITY_COLORS[task.priority] || '#0f766e',
    })
  }

  function cancelEdit() {
    setEditingId(null)
    setEditForm(initialForm)
  }

  async function saveEdit(taskId) {
    if (!editForm.description.trim()) {
      setError('Description is required')
      return
    }
    setEditing(true)
    setError('')
    try {
      const { all_day, datetime } = buildDatetimePayload(editForm)
      await updateTask({
        id: taskId,
        description: editForm.description.trim(),
        details: editForm.details.trim(),
        due_date: editForm.due_date || null,
        all_day,
        datetime,
        category: editForm.category,
        priority: editForm.priority,
        color: editForm.color || null,
      })
      setEditingId(null)
      setEditForm(initialForm)
      await loadTasks()
    } catch (err) {
      setError(err.message || 'Failed to update task')
    } finally {
      setEditing(false)
    }
  }

  function handleAiDraftChange(event) {
    const { name, value, type, checked } = event.target
    const nextValue = type === 'checkbox' ? checked : value
    setAiDraftForm((prev) => {
      const next = { ...prev, [name]: nextValue }
      if (name === 'all_day' && checked) {
        next.due_time = ''
      }
      if (name === 'all_day' && !checked && !next.due_date) {
        next.due_date = dayjs().format('YYYY-MM-DD')
      }
      if (name === 'due_time' && value) {
        next.all_day = false
        if (!next.due_date) {
          next.due_date = dayjs().format('YYYY-MM-DD')
        }
      }
      return next
    })
  }

  async function handleAiSend() {
    const trimmed = aiInput.trim()
    if (!trimmed || aiBusy) return
    setAiBusy(true)
    setAiError('')
    setAiMessages((prev) => [...prev, { role: 'user', text: trimmed }])
    setAiInput('')
    try {
      const result = await parseAi(trimmed)
      const normalized = normalizeAiDraft(result)
      setAiDraft(normalized)
      setAiDraftForm(normalized.form)
      const dueSummary = normalized.form.due_date
        ? `${normalized.form.due_date}${
            normalized.form.all_day
              ? ` · ${t('allDay')}`
              : normalized.form.due_time
                ? ` ${normalized.form.due_time}`
                : ''
          }`
        : t('noDueDate')
      const summaryLines = [
        `${t('aiAction')}: ${normalized.action}${
          normalized.targetId ? ` (#${normalized.targetId})` : ''
        }`,
        normalized.form.description
          ? `${t('titleLabel')}: ${normalized.form.description}`
          : null,
        `${t('due')}: ${dueSummary}`,
        `${t('category')}: ${categoryLabels[normalized.form.category] || normalized.form.category}`,
        `${t('priority')}: ${
          priorityLabels[normalized.form.priority] || priorityLabels.medium
        }`,
      ].filter(Boolean)
      const assistantText = `${summaryLines.join('\n')}\n\n${t(
        'aiEditTitle'
      )} — ${t('aiApply')}?`
      setAiMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: assistantText,
        },
      ])
    } catch (err) {
      setAiError(err.message || 'AI request failed')
    } finally {
      setAiBusy(false)
    }
  }

  function closeAiDraft() {
    setAiDraft(null)
    setAiDraftForm(initialForm)
  }

  async function applyAiDraft() {
    if (!aiDraft) return
    setAiBusy(true)
    setAiError('')
    try {
      const action = aiDraft.action
      const targetId = aiDraft.targetId
      if (action === 'done' && targetId) {
        await markDone(targetId)
      } else if (action === 'reopen' && targetId) {
        await reopenTask(targetId)
      } else if (action === 'remove' && targetId) {
        await removeTask(targetId)
      } else {
        const { all_day, datetime } = buildDatetimePayload(aiDraftForm)
        const payload = {
          description: aiDraftForm.description.trim(),
          details: aiDraftForm.details.trim(),
          due_date: aiDraftForm.due_date || null,
          all_day,
          datetime,
          category: aiDraftForm.category,
          priority: aiDraftForm.priority,
          color: aiDraftForm.color || null,
        }
        if (action === 'update' && targetId) {
          await updateTask({ id: targetId, ...payload })
        } else {
          await addTask(payload)
        }
      }
      closeAiDraft()
      await loadTasks()
    } catch (err) {
      setAiError(err.message || 'AI action failed')
    } finally {
      setAiBusy(false)
    }
  }

  function getTagColor(task) {
    if (task.color) return task.color
    if (task.priority && PRIORITY_COLORS[task.priority]) {
      return PRIORITY_COLORS[task.priority]
    }
    return '#0f766e'
  }

  function formatDue(task) {
    if (!task.due_date) return t('noDueDate')
    const dateLabel = dayjs(task.due_date).format('YYYY-MM-DD')
    const timeLabel = extractTime(task.datetime)
    if (task.all_day) {
      return `${dateLabel} · ${t('allDay')}`
    }
    if (timeLabel) {
      return `${dateLabel} ${timeLabel}`
    }
    return dateLabel
  }

  const t = (key, ...args) => {
    const dict = STRINGS[language] || STRINGS.en
    const value = dict[key] ?? STRINGS.en[key] ?? key
    return typeof value === 'function' ? value(...args) : value
  }

  const categoryLabels = CATEGORY_LABELS[language] || CATEGORY_LABELS.en
  const priorityLabels = PRIORITY_LABELS[language] || PRIORITY_LABELS.en
  const aiPrimaryLabel =
    aiDraft && (aiDraft.action === 'add' || aiDraft.action === 'update')
      ? t('aiApply')
      : t('aiRunAction')
  const quickDateOptions = useMemo(() => {
    const today = dayjs()
    return [
      { value: '', label: t('quickDateNone') },
      { value: today.format('YYYY-MM-DD'), label: t('today') },
      { value: today.add(1, 'day').format('YYYY-MM-DD'), label: t('tomorrow') },
      { value: today.add(3, 'day').format('YYYY-MM-DD'), label: t('next3Days') },
      { value: today.add(7, 'day').format('YYYY-MM-DD'), label: t('nextWeek') },
      { value: 'custom', label: t('quickDateCustom') },
    ]
  }, [language])

  return (
    <div className="page-root">
      <div className="page">
      <header className="header">
        <div>
          <p className="eyebrow">{t('eyebrow')}</p>
          <h1>{t('title')}</h1>
          <p className="subtitle">{t('subtitle')}</p>
        </div>
        <div className="header-actions">
          <div className="summary">
            <div className="summary-card">
              <p className="summary-label">{t('open')}</p>
              <p className="summary-value">{openCount}</p>
            </div>
            <div className="summary-card muted-card">
              <p className="summary-label">{t('done')}</p>
              <p className="summary-value">{completedCount}</p>
            </div>
          </div>
          <div className="settings">
            <label className="field">
              <span>{t('language')}</span>
              <select
                value={language}
                onChange={async (event) => {
                  if (settingLang) return
                  setSettingLang(true)
                  await persistLanguage(event.target.value)
                  setSettingLang(false)
                }}
              >
                <option value="en">English</option>
                <option value="zh">中文</option>
              </select>
            </label>
          </div>
        </div>
      </header>

      <section className="panel">
        <h2>{t('addTask')}</h2>
        <form className="form" onSubmit={handleAdd}>
          <label className="field">
            <span>{t('titleLabel')}</span>
            <input
              type="text"
              name="description"
              value={form.description}
              onChange={handleChange}
              placeholder={t('titlePlaceholder')}
              required
            />
          </label>
          <label className="field">
            <span>{t('details')}</span>
            <textarea
              name="details"
              value={form.details}
              onChange={handleChange}
              placeholder={t('detailsPlaceholder')}
              rows={3}
            />
          </label>
          <div className="row">
            <label className="field">
              <span>{t('category')}</span>
              <select name="category" value={form.category} onChange={handleChange}>
                <option value="work">{categoryLabels.work}</option>
                <option value="study">{categoryLabels.study}</option>
                <option value="personal">{categoryLabels.personal}</option>
              </select>
            </label>
            <label className="field">
              <span>{t('priority')}</span>
              <select name="priority" value={form.priority} onChange={handleChange}>
                <option value="high">{priorityLabels.high}</option>
                <option value="medium">{priorityLabels.medium}</option>
                <option value="low">{priorityLabels.low}</option>
              </select>
            </label>
            <label className="field">
              <span>{t('color')}</span>
              <input
                type="color"
                name="color"
                value={form.color}
                onChange={handleChange}
              />
            </label>
            <label className="field">
              <span>{t('quickDate')}</span>
              <select
                value={quickDatePreset}
                onChange={(event) => {
                  const value = event.target.value
                  setQuickDatePreset(value)
                  if (value && value !== 'custom') {
                    setForm((prev) => ({
                      ...prev,
                      due_date: value,
                      due_time: '',
                      all_day: true,
                    }))
                  }
                }}
              >
                {quickDateOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>{t('dueDate')}</span>
              <input
                type="date"
                name="due_date"
                value={form.due_date}
                onChange={(event) => {
                  setQuickDatePreset('custom')
                  handleChange(event)
                }}
              />
            </label>
            <label className="field">
              <span>{t('time')}</span>
              <input
                type="time"
                name="due_time"
                value={form.due_time}
                onChange={handleChange}
                disabled={form.all_day}
              />
            </label>
            <label className="field field-inline">
              <span>{t('allDay')}</span>
              <input
                type="checkbox"
                name="all_day"
                checked={form.all_day}
                onChange={handleChange}
              />
            </label>
          </div>
          <div className="actions">
            <button type="submit" disabled={submitting}>
              {submitting ? t('saving') : t('add')}
            </button>
            <button type="button" className="ghost" onClick={loadTasks}>
              {t('refresh')}
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <div>
            <h2>{t('tasks')}</h2>
            <p className="muted small">
              {t('itemsCount', filteredTasks.length, openCount)}
            </p>
          </div>
          <div className="filters">
            <button
              type="button"
              className={`filter ${statusFilter === 'all' ? 'active' : ''}`}
              onClick={() => setStatusFilter('all')}
            >
              {t('all')}
            </button>
            <button
              type="button"
              className={`filter ${statusFilter === 'open' ? 'active' : ''}`}
              onClick={() => setStatusFilter('open')}
            >
              {t('open')}
            </button>
            <button
              type="button"
              className={`filter ${statusFilter === 'done' ? 'active' : ''}`}
              onClick={() => setStatusFilter('done')}
            >
              {t('done')}
            </button>
          </div>
        </div>
        <div className="toolbar">
          <input
            className="search"
            placeholder={t('searchPlaceholder')}
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <select
            className="select"
            value={categoryFilter}
            onChange={(event) => setCategoryFilter(event.target.value)}
          >
            <option value="all">{t('allCategories')}</option>
            <option value="work">{categoryLabels.work}</option>
            <option value="study">{categoryLabels.study}</option>
            <option value="personal">{categoryLabels.personal}</option>
          </select>
          <select
            className="select"
            value={priorityFilter}
            onChange={(event) => setPriorityFilter(event.target.value)}
          >
            <option value="all">{t('allPriorities')}</option>
            <option value="high">{priorityLabels.high}</option>
            <option value="medium">{priorityLabels.medium}</option>
            <option value="low">{priorityLabels.low}</option>
          </select>
          {loading && <span className="pill">{t('loading')}</span>}
        </div>
        {error && <div className="error">{error}</div>}
        {!loading && !hasTasks && <p className="muted">{t('noTasks')}</p>}
        {!loading &&
          hasTasks &&
          Object.entries(groupedTasks).map(([group, items]) => {
            if (items.length === 0) {
              return null
            }
            return (
              <div className="group" key={group}>
                <div className="group-header">
                  <div className="group-title">
                    <span className="group-dot" />
                    <h3>{categoryLabels[group] || group}</h3>
                  </div>
                  <span className="pill subtle">{items.length}</span>
                </div>
                <div className="task-grid">
                  {items.map((task, index) => {
                    const due = formatDue(task)
                    const isEditing = editingId === task.id
                    const tagColor = getTagColor(task)
                    return (
                      <article
                        key={task.id}
                        className={`task ${task.completed ? 'done' : ''}`}
                      >
                        <div className="task-head">
                          <div>
                            {!isEditing ? (
                              <h3>
                                <span className="task-index">#{index + 1}</span>
                                {task.description}
                              </h3>
                            ) : (
                              <input
                                className="inline-input"
                                name="description"
                                value={editForm.description}
                                onChange={handleEditChange}
                              />
                            )}
                          </div>
                          <span className="pill">
                            {task.completed ? t('done') : t('open')}
                          </span>
                        </div>
                        <div className="meta">
                          <span
                            className="tag"
                            style={{ background: tagColor }}
                          >
                            {priorityLabels[task.priority] || priorityLabels.medium}
                          </span>
                          <span className="meta-text">{t('due')} {due}</span>
                        </div>
                        {!isEditing ? (
                          task.details && <p className="muted">{task.details}</p>
                        ) : (
                          <textarea
                            className="inline-textarea"
                            name="details"
                            value={editForm.details}
                            onChange={handleEditChange}
                            rows={3}
                          />
                        )}
                        {isEditing && (
                          <div className="row">
                            <label className="field">
                              <span>{t('category')}</span>
                              <select
                                name="category"
                                value={editForm.category}
                                onChange={handleEditChange}
                              >
                                <option value="work">{categoryLabels.work}</option>
                                <option value="study">{categoryLabels.study}</option>
                                <option value="personal">{categoryLabels.personal}</option>
                              </select>
                            </label>
                            <label className="field">
                              <span>{t('priority')}</span>
                              <select
                                name="priority"
                                value={editForm.priority}
                                onChange={handleEditChange}
                              >
                                <option value="high">{priorityLabels.high}</option>
                                <option value="medium">{priorityLabels.medium}</option>
                                <option value="low">{priorityLabels.low}</option>
                              </select>
                            </label>
                            <label className="field">
                              <span>{t('color')}</span>
                              <input
                                type="color"
                                name="color"
                                value={editForm.color}
                                onChange={handleEditChange}
                              />
                            </label>
                            <label className="field">
                              <span>{t('dueDate')}</span>
                              <input
                                type="date"
                                name="due_date"
                                value={editForm.due_date}
                                onChange={handleEditChange}
                              />
                            </label>
                            <label className="field">
                              <span>{t('time')}</span>
                              <input
                                type="time"
                                name="due_time"
                                value={editForm.due_time}
                                onChange={handleEditChange}
                                disabled={editForm.all_day}
                              />
                            </label>
                            <label className="field field-inline">
                              <span>{t('allDay')}</span>
                              <input
                                type="checkbox"
                                name="all_day"
                                checked={editForm.all_day}
                                onChange={handleEditChange}
                              />
                            </label>
                          </div>
                        )}
                        <div className="task-actions">
                          {!isEditing ? (
                            <>
                              {!task.completed ? (
                                <button
                                  type="button"
                                  onClick={() => handleDone(task.id)}
                                >
                                  {t('complete')}
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  onClick={() => handleReopen(task.id)}
                                >
                                  {t('reopen')}
                                </button>
                              )}
                              <button
                                type="button"
                                className="ghost"
                                onClick={() => startEdit(task)}
                              >
                                {t('edit')}
                              </button>
                              <button
                                type="button"
                                className="ghost danger"
                                onClick={() => handleRemove(task.id)}
                              >
                                {t('delete')}
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                type="button"
                                onClick={() => saveEdit(task.id)}
                                disabled={editing}
                              >
                                {editing ? t('saving') : t('save')}
                              </button>
                              <button
                                type="button"
                                className="ghost"
                                onClick={cancelEdit}
                              >
                                {t('cancel')}
                              </button>
                            </>
                          )}
                        </div>
                      </article>
                    )
                  })}
                </div>
              </div>
            )
          })}
      </section>
      </div>
      <div
        className={`ai-widget ${aiOpen ? 'open' : ''}`}
        ref={aiWidgetRef}
        style={
          aiPosition
            ? { left: `${aiPosition.x}px`, top: `${aiPosition.y}px`, right: 'auto', transform: 'none' }
            : undefined
        }
      >
        <button
          type="button"
          className="ai-fab"
          onPointerDown={startAiDrag}
          onClick={() => {
            if (Date.now() < dragClickBlockRef.current) return
            setAiOpen((prev) => !prev)
          }}
          aria-expanded={aiOpen}
        >
          AI
        </button>
        {aiOpen && (
          <div
            className="ai-panel"
            ref={aiPanelRef}
            style={{
              transform: `translate(${-aiPanelShift.x}px, ${-aiPanelShift.y}px)`,
            }}
          >
            <div className="ai-header">
              <h3 className="ai-drag-handle">{t('aiTitle')}</h3>
              <button
                type="button"
                className="ghost"
                onClick={() => setAiOpen(false)}
              >
                {t('aiCancel')}
              </button>
            </div>
            <div className="ai-messages">
              {aiMessages.length === 0 && (
                <p className="muted">{t('aiHint')}</p>
              )}
              {aiMessages.map((msg, index) => (
                <div
                  key={`${msg.role}-${index}`}
                  className={`ai-bubble ${msg.role}`}
                >
                  {msg.text}
                </div>
              ))}
            </div>
            {aiBusy && (
              <div className="ai-loading">
                <span className="ai-dot" />
                <span className="ai-dot" />
                <span className="ai-dot" />
                <span className="muted">{t('saving')}</span>
              </div>
            )}
            {aiError && <div className="error">{aiError}</div>}
            <div className="ai-input">
              <input
                type="text"
                placeholder={t('aiHint')}
                value={aiInput}
                onChange={(event) => setAiInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') handleAiSend()
                }}
                disabled={aiBusy}
              />
              <button type="button" onClick={handleAiSend} disabled={aiBusy}>
                {aiBusy ? t('saving') : t('aiSend')}
              </button>
            </div>
          </div>
        )}
      </div>
      {aiDraft && (
        <div className="modal">
          <div className="modal-backdrop" onClick={closeAiDraft} />
          <div className="modal-card">
            <div className="modal-header">
              <h3>{t('aiEditTitle')}</h3>
            </div>
            <div className="modal-body">
              <div className="ai-summary">
                <p className="muted">
                  {t('aiAction')}: {aiDraft.action}
                </p>
                {aiDraft.targetId && (
                  <p className="muted">
                    {t('aiTarget')}: #{aiDraft.targetId}
                  </p>
                )}
              </div>
              {(aiDraft.action === 'add' || aiDraft.action === 'update') && (
                <div className="form ai-form">
                  <label className="field">
                    <span>{t('titleLabel')}</span>
                    <input
                      type="text"
                      name="description"
                      value={aiDraftForm.description}
                      onChange={handleAiDraftChange}
                    />
                  </label>
                  <label className="field">
                    <span>{t('details')}</span>
                    <textarea
                      name="details"
                      value={aiDraftForm.details}
                      onChange={handleAiDraftChange}
                      rows={3}
                    />
                  </label>
                  <div className="row">
                    <label className="field">
                      <span>{t('category')}</span>
                      <select
                        name="category"
                        value={aiDraftForm.category}
                        onChange={handleAiDraftChange}
                      >
                        <option value="work">{categoryLabels.work}</option>
                        <option value="study">{categoryLabels.study}</option>
                        <option value="personal">{categoryLabels.personal}</option>
                      </select>
                    </label>
                    <label className="field">
                      <span>{t('priority')}</span>
                      <select
                        name="priority"
                        value={aiDraftForm.priority}
                        onChange={handleAiDraftChange}
                      >
                        <option value="high">{priorityLabels.high}</option>
                        <option value="medium">{priorityLabels.medium}</option>
                        <option value="low">{priorityLabels.low}</option>
                      </select>
                    </label>
                    <label className="field">
                      <span>{t('color')}</span>
                      <input
                        type="color"
                        name="color"
                        value={aiDraftForm.color}
                        onChange={handleAiDraftChange}
                      />
                    </label>
                    <label className="field">
                      <span>{t('dueDate')}</span>
                      <input
                        type="date"
                        name="due_date"
                        value={aiDraftForm.due_date}
                        onChange={handleAiDraftChange}
                      />
                    </label>
                    <label className="field">
                      <span>{t('time')}</span>
                      <input
                        type="time"
                        name="due_time"
                        value={aiDraftForm.due_time}
                        onChange={handleAiDraftChange}
                        disabled={aiDraftForm.all_day}
                      />
                    </label>
                    <label className="field field-inline">
                      <span>{t('allDay')}</span>
                      <input
                        type="checkbox"
                        name="all_day"
                        checked={aiDraftForm.all_day}
                        onChange={handleAiDraftChange}
                      />
                    </label>
                  </div>
                </div>
              )}
              {aiDraft.action !== 'add' && aiDraft.action !== 'update' && (
                <p className="muted">{t('aiNoDraft')}</p>
              )}
            </div>
            <div className="actions">
              <button type="button" onClick={applyAiDraft} disabled={aiBusy}>
                {aiBusy ? t('saving') : aiPrimaryLabel}
              </button>
              <button type="button" className="ghost" onClick={closeAiDraft}>
                {t('aiCancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
