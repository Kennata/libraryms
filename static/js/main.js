// ─── CONFIG ───────────────────────────────────────────────
const API = "/api";

// ─── UTILS ───────────────────────────────────────────────
function debounce(fn, ms) {
  let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
}

function showToast(msg, type = "success") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove("show"), 2800);
}

async function api(path, opts = {}) {
  const r = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || "Request failed");
  return data;
}

function initials(name) {
  return name.split(" ").slice(0, 2).map(w => w[0]).join("").toUpperCase();
}

const AVATAR_COLORS = [
  ["#dbeafe", "#1d4ed8"], ["#fce7f3", "#9d174d"], ["#d1fae5", "#065f46"],
  ["#ede9fe", "#5b21b6"], ["#fee2e2", "#b91c1c"], ["#fef3c7", "#b45309"]
];
function avatarColor(id) { return AVATAR_COLORS[id % AVATAR_COLORS.length]; }

function openModal(id)  { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }

// ─── NAVIGATION ──────────────────────────────────────────
const PAGES = ["books", "members", "borrow", "loans", "team", "settings"];
let currentPage = "books";

function showPage(name) {
  PAGES.forEach(p => document.getElementById("page-" + p).classList.toggle("active", p === name));
  document.querySelectorAll(".sidebar-nav .nav-item").forEach((btn, i) => {
    btn.classList.toggle("active", PAGES[i] === name);
  });
  currentPage = name;
  if (name === "books")   { loadStats(); loadBooks(1); }
  if (name === "members") { loadStats(); loadMembers(1); }
  if (name === "loans")   { loadStats(); loadLoans(1); }
  if (name === "borrow")  { loadBorrowSelects(); loadActivity(); }
}

// ─── STATS ───────────────────────────────────────────────
async function loadStats() {
  try {
    const d = await api("/stats");
    document.getElementById("stat-books").textContent        = d.books.toLocaleString();
    document.getElementById("stat-stock").textContent        = d.total_stock.toLocaleString();
    document.getElementById("stat-nostock").textContent      = d.out_of_stock.toLocaleString();
    document.getElementById("stat-members").textContent      = d.members.toLocaleString();
    document.getElementById("stat-borrowers").textContent    = d.active_borrowers.toLocaleString();
    document.getElementById("stat-total-loans").textContent  = d.total_loans.toLocaleString();
    document.getElementById("stat-active-loans").textContent = d.active_loans.toLocaleString();
    document.getElementById("stat-overdue").textContent      = d.overdue.toLocaleString();
    document.getElementById("stat-returns-today").textContent = d.returns_today.toLocaleString();
  } catch (e) { console.error(e); }
}

// ─── BOOKS ───────────────────────────────────────────────
let booksPage = 1;

async function loadBooks(page = 1) {
  booksPage = page;
  const q = document.getElementById("books-search").value;
  const tbody = document.getElementById("books-tbody");
  tbody.innerHTML = `<tr><td colspan="6" class="loading">Loading…</td></tr>`;
  try {
    const d = await api(`/books?page=${page}&per_page=8&q=${encodeURIComponent(q)}`);
    if (!d.books.length) { tbody.innerHTML = `<tr><td colspan="6" class="empty">No books found.</td></tr>`; return; }
    tbody.innerHTML = d.books.map(b => `
      <tr>
        <td class="id-cell">#B-${String(b.id).padStart(4, "0")}</td>
        <td><strong>${b.title}</strong></td>
        <td>${b.author}</td>
        <td><span class="badge badge-year">${b.year || "—"}</span></td>
        <td class="${b.stock === 0 ? "stock-zero" : "stock-ok"}">${b.stock}</td>
        <td><div class="action-btns">
          <button class="icon-btn" title="Edit" onclick='openBookModal(${JSON.stringify(b)})'>
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="icon-btn del" title="Delete" onclick="deleteBook(${b.id})">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
          </button>
        </div></td>
      </tr>`).join("");

    const total = d.total, perPage = d.per_page;
    const start = (page - 1) * perPage + 1, end = Math.min(page * perPage, total);
    document.getElementById("books-info").textContent = `Showing ${start}–${end} of ${total.toLocaleString()} books`;
    renderPagination("books-pagination", page, Math.ceil(total / perPage), loadBooks);
  } catch (e) { tbody.innerHTML = `<tr><td colspan="6" class="empty">Error loading books.</td></tr>`; }
}

function openBookModal(book = null) {
  document.getElementById("book-modal-title").textContent = book ? "Edit Book" : "Add New Book";
  document.getElementById("book-id").value     = book?.id     || "";
  document.getElementById("book-title").value  = book?.title  || "";
  document.getElementById("book-author").value = book?.author || "";
  document.getElementById("book-year").value   = book?.year   || "";
  document.getElementById("book-stock").value  = book?.stock  ?? 0;
  document.getElementById("book-isbn").value   = book?.isbn   || "";
  openModal("book-modal");
}

async function saveBook() {
  const id = document.getElementById("book-id").value;
  const payload = {
    title:  document.getElementById("book-title").value.trim(),
    author: document.getElementById("book-author").value.trim(),
    year:   parseInt(document.getElementById("book-year").value) || null,
    stock:  parseInt(document.getElementById("book-stock").value) || 0,
    isbn:   document.getElementById("book-isbn").value.trim(),
  };
  if (!payload.title || !payload.author) { showToast("Title and Author are required", "error"); return; }
  try {
    if (id) {
      await api(`/books/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      showToast("Book updated");
    } else {
      await api("/books", { method: "POST", body: JSON.stringify(payload) });
      showToast("Book added");
    }
    closeModal("book-modal");
    loadBooks(booksPage);
    loadStats();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteBook(id) {
  if (!confirm("Delete this book?")) return;
  try {
    await api(`/books/${id}`, { method: "DELETE" });
    showToast("Book deleted");
    loadBooks(booksPage);
    loadStats();
  } catch (e) { showToast(e.message, "error"); }
}

// ─── MEMBERS ─────────────────────────────────────────────
let membersPage = 1, membersTotalPages = 1;

async function loadMembers(page = 1) {
  membersPage = page;
  const q = document.getElementById("members-search").value;
  const tbody = document.getElementById("members-tbody");
  tbody.innerHTML = `<tr><td colspan="6" class="loading">Loading…</td></tr>`;
  try {
    const d = await api(`/members?page=${page}&per_page=8&q=${encodeURIComponent(q)}`);
    membersTotalPages = Math.ceil(d.total / d.per_page);
    if (!d.members.length) { tbody.innerHTML = `<tr><td colspan="6" class="empty">No members found.</td></tr>`; return; }
    tbody.innerHTML = d.members.map(m => {
      const [bg, fg] = avatarColor(m.id);
      const lc = m.active_loans === 0 ? "gray" : m.active_loans >= 4 ? "orange" : "blue";
      return `<tr>
        <td class="id-cell">#M-${String(m.id).padStart(4, "0")}</td>
        <td><div style="display:flex;align-items:center;gap:8px">
          <div class="member-avatar" style="background:${bg};color:${fg}">${initials(m.name)}</div>${m.name}
        </div></td>
        <td style="color:var(--gray-500)">${m.email}</td>
        <td style="color:var(--gray-500)">${m.phone || "—"}</td>
        <td><span class="loan-count ${lc}">${m.active_loans}</span></td>
        <td><div class="action-btns">
          <button class="icon-btn" onclick='openMemberModal(${JSON.stringify(m)})'>
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="icon-btn del" onclick="deleteMember(${m.id})">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
          </button>
        </div></td>
      </tr>`;
    }).join("");
    const start = (page - 1) * d.per_page + 1, end = Math.min(page * d.per_page, d.total);
    document.getElementById("members-info").textContent = `Showing ${start}–${end} of ${d.total.toLocaleString()} members`;
    document.getElementById("members-prev").disabled = page <= 1;
    document.getElementById("members-next").disabled = page >= membersTotalPages;
  } catch (e) { tbody.innerHTML = `<tr><td colspan="6" class="empty">Error loading members.</td></tr>`; }
}

function openMemberModal(m = null) {
  document.getElementById("member-modal-title").textContent = m ? "Edit Member" : "Register Member";
  document.getElementById("member-id").value    = m?.id    || "";
  document.getElementById("member-name").value  = m?.name  || "";
  document.getElementById("member-email").value = m?.email || "";
  document.getElementById("member-phone").value = m?.phone || "";
  openModal("member-modal");
}

async function saveMember() {
  const id = document.getElementById("member-id").value;
  const payload = {
    name:  document.getElementById("member-name").value.trim(),
    email: document.getElementById("member-email").value.trim(),
    phone: document.getElementById("member-phone").value.trim(),
  };
  if (!payload.name || !payload.email) { showToast("Name and Email are required", "error"); return; }
  try {
    if (id) {
      await api(`/members/${id}`, { method: "PUT", body: JSON.stringify(payload) });
      showToast("Member updated");
    } else {
      await api("/members", { method: "POST", body: JSON.stringify(payload) });
      showToast("Member registered");
    }
    closeModal("member-modal");
    loadMembers(membersPage);
    loadStats();
  } catch (e) { showToast(e.message, "error"); }
}

async function deleteMember(id) {
  if (!confirm("Delete this member?")) return;
  try {
    await api(`/members/${id}`, { method: "DELETE" });
    showToast("Member deleted");
    loadMembers(membersPage);
    loadStats();
  } catch (e) { showToast(e.message, "error"); }
}

// ─── BORROW ──────────────────────────────────────────────
async function loadBorrowSelects() {
  try {
    const [md, bd] = await Promise.all([
      api("/members?per_page=200"),
      api("/books?per_page=200")
    ]);
    document.getElementById("borrow-member").innerHTML =
      `<option value="">— Select Member —</option>` +
      md.members.map(m => `<option value="${m.id}">${m.name} (#M-${String(m.id).padStart(4, "0")})</option>`).join("");
    document.getElementById("borrow-book").innerHTML =
      `<option value="">— Select Book —</option>` +
      bd.books.map(b => `<option value="${b.id}" data-stock="${b.stock}">${b.title} (Stock: ${b.stock})</option>`).join("");

    const due = new Date(); due.setDate(due.getDate() + 14);
    document.getElementById("borrow-due").value = due.toISOString().split("T")[0];
  } catch (e) { showToast("Failed to load form data", "error"); }
}

function updateBookStock() {
  const sel   = document.getElementById("borrow-book");
  const opt   = sel.options[sel.selectedIndex];
  const stock = opt?.dataset?.stock;
  const hint  = document.getElementById("borrow-stock-hint");
  if (stock !== undefined && stock !== "") {
    hint.innerHTML = `<svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
      Current Stock: <strong>${stock}</strong> units`;
    hint.style.color = parseInt(stock) === 0 ? "var(--red)" : "var(--blue)";
  } else { hint.innerHTML = ""; }
}

async function processLoan() {
  const member_id  = document.getElementById("borrow-member").value;
  const book_id    = document.getElementById("borrow-book").value;
  const dueDateVal = document.getElementById("borrow-due").value;
  if (!member_id || !book_id || !dueDateVal) { showToast("Please fill all fields", "error"); return; }
  const [y, m, d] = dueDateVal.split("-");
  const due_date = `${d}/${m}/${y}`;
  try {
    await api("/loans", { method: "POST", body: JSON.stringify({ member_id: parseInt(member_id), book_id: parseInt(book_id), due_date }) });
    showToast("Loan processed successfully!");
    resetBorrowForm();
    loadBorrowSelects();
    loadActivity();
    loadStats();
  } catch (e) { showToast(e.message, "error"); }
}

function resetBorrowForm() {
  document.getElementById("borrow-member").value = "";
  document.getElementById("borrow-book").value   = "";
  document.getElementById("borrow-stock-hint").innerHTML = "";
  const due = new Date(); due.setDate(due.getDate() + 14);
  document.getElementById("borrow-due").value = due.toISOString().split("T")[0];
}

async function loadActivity() {
  try {
    const acts = await api("/activity");
    const el = document.getElementById("borrow-activity");
    el.innerHTML = acts.map(a => {
      const action = a.status === "returned"
        ? `<strong>${a.member_name}</strong> returned <strong>"${a.book_title}"</strong>`
        : `<strong>${a.member_name}</strong> borrowed <strong>"${a.book_title}"</strong>`;
      return `<div class="activity-item"><p>${action}</p><div class="activity-time">${a.borrow_date}</div></div>`;
    }).join("") || `<div class="empty">No activity yet.</div>`;
  } catch (e) { document.getElementById("borrow-activity").innerHTML = `<div class="empty">Error loading activity.</div>`; }
}

// ─── LOANS ───────────────────────────────────────────────
let loansPage = 1, currentLoanTab = "active";

function setLoanTab(tab, btn) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  currentLoanTab = tab;
  loadLoans(1);
}

async function loadLoans(page = 1) {
  loansPage = page;
  const q = document.getElementById("loans-search").value;
  const tbody = document.getElementById("loans-tbody");
  tbody.innerHTML = `<tr><td colspan="7" class="loading">Loading…</td></tr>`;
  try {
    const d = await api(`/loans?page=${page}&per_page=8&status=${currentLoanTab}&q=${encodeURIComponent(q)}`);
    if (!d.loans.length) { tbody.innerHTML = `<tr><td colspan="7" class="empty">No records found.</td></tr>`; return; }
    tbody.innerHTML = d.loans.map(l => {
      const [bg, fg]  = avatarColor(l.member_id);
      const statusCls = l.status === "active" ? "active" : l.status === "returned" ? "returned" : "overdue";
      const dueCls    = l.status === "overdue" ? ' class="overdue-red"' : "";
      const action    = l.status === "returned"
        ? `<button class="icon-btn" title="View"><svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></button>`
        : `<button class="btn-return" onclick="returnLoan(${l.id})">Return</button>`;
      return `<tr>
        <td class="id-cell">#L-${String(l.id).padStart(4, "0")}</td>
        <td><div style="display:flex;align-items:center;gap:8px">
          <div class="member-avatar" style="background:${bg};color:${fg}">${initials(l.member_name)}</div>${l.member_name}
        </div></td>
        <td>${l.book_title}</td>
        <td>${l.borrow_date}</td>
        <td${dueCls}>${l.due_date}</td>
        <td><span class="status-pill ${statusCls}">${l.status.charAt(0).toUpperCase() + l.status.slice(1)}</span></td>
        <td>${action}</td>
      </tr>`;
    }).join("");
    const start = (page - 1) * d.per_page + 1, end = Math.min(page * d.per_page, d.total);
    document.getElementById("loans-info").textContent = `Showing ${start}–${end} of ${d.total.toLocaleString()} records`;
    renderPagination("loans-pagination", page, Math.ceil(d.total / d.per_page), loadLoans);
  } catch (e) { tbody.innerHTML = `<tr><td colspan="7" class="empty">Error loading loans.</td></tr>`; }
}

async function returnLoan(id) {
  if (!confirm("Mark this loan as returned?")) return;
  try {
    await api(`/loans/${id}/return`, { method: "POST" });
    showToast("Book returned successfully!");
    loadLoans(loansPage);
    loadStats();
  } catch (e) { showToast(e.message, "error"); }
}

// ─── PAGINATION HELPER ───────────────────────────────────
function renderPagination(containerId, page, totalPages, loadFn) {
  const el = document.getElementById(containerId);
  if (totalPages <= 1) { el.innerHTML = ""; return; }
  let html = `<button class="page-btn" ${page <= 1 ? "disabled" : ""} onclick="(${loadFn.name})(${page - 1})">‹</button>`;
  const range = [];
  for (let i = Math.max(1, page - 1); i <= Math.min(totalPages, page + 1); i++) range.push(i);
  range.forEach(p => {
    html += `<button class="page-btn ${p === page ? "active" : ""}" onclick="(${loadFn.name})(${p})">${p}</button>`;
  });
  html += `<button class="page-btn" ${page >= totalPages ? "disabled" : ""} onclick="(${loadFn.name})(${page + 1})">›</button>`;
  el.innerHTML = html;
}

// ─── INIT ────────────────────────────────────────────────
showPage("books");
