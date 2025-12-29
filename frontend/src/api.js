const API_BASE = 'http://127.0.0.1:5000';

async function handleResponse(res) {
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export async function fetchTasks() {
  const res = await fetch(`${API_BASE}/api/list`);
  return handleResponse(res);
}

export async function addTask(task) {
  const res = await fetch(`${API_BASE}/api/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(task),
  });
  return handleResponse(res);
}

export async function markDone(id) {
  const res = await fetch(`${API_BASE}/api/done`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  });
  return handleResponse(res);
}

export async function removeTask(id) {
  const res = await fetch(`${API_BASE}/api/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  });
  return handleResponse(res);
}

export async function reopenTask(id) {
  const res = await fetch(`${API_BASE}/api/reopen`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  });
  return handleResponse(res);
}