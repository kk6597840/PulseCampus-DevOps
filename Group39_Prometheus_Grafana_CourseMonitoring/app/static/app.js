"use strict";
const el = (id) => document.getElementById(id);
let demoToken = null;
let toastTimer;

function toast(message, error = false) {
  const box = el("toast");
  box.textContent = message;
  box.classList.toggle("error", error);
  box.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => box.classList.remove("show"), 3700);
}
async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    });
  } catch (_) {
    throw new Error("Cannot reach the Flask API. Check Docker Compose.");
  }
  const content = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(content.error || content.message || `HTTP ${response.status}`);
  return content;
}
function node(tag, text, className) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (className) n.className = className;
  return n;
}
function fillSelect(select, items, label) {
  const previous = select.value;
  select.replaceChildren(new Option(label, ""));
  items.forEach(item => select.add(new Option(item.label, item.value)));
  if (Array.from(select.options).some(option => option.value === previous)) select.value = previous;
}
async function refresh() {
  const [summary, courseData, studentData, enrollmentData] = await Promise.all([
    api("/api/summary"), api("/api/courses"), api("/api/students"), api("/api/enrollments"),
  ]);
  el("studentCount").textContent = summary.students;
  el("courseCount").textContent = summary.courses;
  el("enrollCount").textContent = summary.enrollments;
  el("activeCount").textContent = summary.active_users;
  const students = studentData.students.map(s => ({ label: `${s.name} (#${s.id})`, value: String(s.id) }));
  fillSelect(el("studentSelect"), students, "Choose a student");
  fillSelect(el("sessionStudent"), students, "Select a student");
  fillSelect(el("courseSelect"), courseData.courses.map(c => ({ label: `${c.code} — ${c.title}`, value: String(c.id) })), "Choose a course");
  const cards = el("courseList");
  cards.replaceChildren();
  courseData.courses.forEach(course => {
    const card = node("article", undefined, "course-card");
    card.append(node("div", course.code, "course-code"), node("h3", course.title), node("p", course.instructor));
    const meta = node("div", undefined, "course-meta");
    meta.append(node("span", "AVAILABLE SEATS"), node("strong", `${course.capacity - course.enrolled} / ${course.capacity}`));
    card.append(meta);
    cards.append(card);
  });
  const rows = el("enrollTable");
  rows.replaceChildren();
  if (!enrollmentData.enrollments.length) {
    const tr = node("tr");
    const td = node("td", "No enrollments yet. Add a student and choose a course.", "muted");
    td.colSpan = 4;
    tr.append(td);
    rows.append(tr);
  }
  enrollmentData.enrollments.forEach(r => {
    const tr = node("tr");
    const code = node("span", r.code, "course-tag");
    const codeTd = node("td"); codeTd.append(code);
    const action = node("button", "Remove", "small-danger"); action.type = "button";
    action.addEventListener("click", async () => {
      if (!confirm(`Remove ${r.student}'s enrollment in ${r.code}?`)) return;
      try { await api(`/api/enrollments/${r.id}`, { method: "DELETE" }); toast("Enrollment removed"); await refresh(); }
      catch (error) { toast(error.message, true); }
    });
    const actionTd = node("td"); actionTd.append(action);
    tr.append(node("td", r.student), codeTd, node("td", r.created_at), actionTd);
    rows.append(tr);
  });
  const status = el("apiState"); status.textContent = "● API online"; status.classList.remove("offline");
}

el("studentForm").addEventListener("submit", async event => {
  event.preventDefault();
  try {
    const result = await api("/api/students", { method: "POST", body: JSON.stringify({ name: el("studentName").value, email: el("studentEmail").value }) });
    toast(`Student ${result.name} registered successfully`); el("studentForm").reset(); await refresh();
  } catch (error) { toast(error.message, true); }
});
el("enrollForm").addEventListener("submit", async event => {
  event.preventDefault();
  try {
    await api("/api/enrollments", { method: "POST", body: JSON.stringify({ student_id: Number(el("studentSelect").value), course_id: Number(el("courseSelect").value) }) });
    toast("Course enrollment created successfully"); await refresh();
  } catch (error) { toast(error.message, true); }
});
el("refreshBtn").addEventListener("click", () => refresh().catch(error => toast(error.message, true)));
async function lab(path, label) {
  const start = performance.now();
  try {
    const response = await fetch(path);
    const milliseconds = Math.round(performance.now() - start);
    el("labLog").textContent = `${new Date().toLocaleTimeString()} · ${label} · HTTP ${response.status} · ${milliseconds} ms`;
    toast(`Sent ${label} (HTTP ${response.status})`, response.status >= 500);
  } catch (error) { toast(error.message, true); }
}
el("normalBtn").addEventListener("click", () => lab("/api/courses", "normal GET"));
el("slowBtn").addEventListener("click", () => lab("/api/demo/slow?delay_ms=1200", "slow GET"));
el("errorBtn").addEventListener("click", () => lab("/api/demo/error", "intentional 503"));
el("sessionStart").addEventListener("click", async () => {
  const studentId = el("sessionStudent").value;
  if (!studentId) return toast("Register or select a student first", true);
  try {
    if (demoToken) await api(`/api/sessions/${encodeURIComponent(demoToken)}`, {method:"DELETE"}).catch(() => {});
    const session = await api("/api/sessions", {method:"POST", body: JSON.stringify({student_id:Number(studentId)})});
    demoToken = session.token;
    el("sessionStop").disabled = false;
    toast("Live student session started; active_users Gauge increased"); await refresh();
  } catch (error) { toast(error.message, true); }
});
el("sessionStop").addEventListener("click", async () => {
  try {
    await api(`/api/sessions/${encodeURIComponent(demoToken)}`, {method:"DELETE"});
    demoToken = null; el("sessionStop").disabled = true;
    toast("Session ended; active_users Gauge decreased"); await refresh();
  } catch (error) { toast(error.message, true); }
});
refresh().catch(error => { const s = el("apiState"); s.textContent = "● API offline"; s.classList.add("offline"); toast(error.message, true); });
setInterval(() => refresh().catch(() => { const s = el("apiState"); s.textContent = "● API offline"; s.classList.add("offline"); }), 10000);
