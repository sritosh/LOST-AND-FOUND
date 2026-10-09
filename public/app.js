/**
 * CAMPUS LOST & FOUND SYSTEM - FRONTEND INTERACTIVITY & API INTEGRATION
 * DBMS Lab Project • Review 1 (50% Milestone)
 * Authors: Sritosh Rath (24BDS0001) & Jayant Sharma (24BAI0148)
 */

const API_BASE = '/api';

// Pre-defined Review Queries for Quick Faculty Demonstration
const PRESET_QUERIES = {
    "Q1": `-- Q1: Simple Selection & Projection
SELECT student_id, name, email, department 
FROM STUDENT 
ORDER BY name ASC;`,

    "Q2": `-- Q2: Multi-Table JOIN - Active Lost Items with Student Information
SELECT 
    l.lost_id,
    i.item_name,
    i.category,
    i.location AS lost_location,
    l.date_lost,
    l.status,
    s.name AS student_name,
    s.department,
    s.phone
FROM LOST_ITEM l
JOIN ITEM i ON l.item_id = i.item_id
JOIN STUDENT s ON l.student_id = s.student_id
WHERE l.status = 'Pending'
ORDER BY l.date_lost DESC;`,

    "Q3": `-- Q3: Multi-Table JOIN - Found Items with Finder & Custody Desk
SELECT 
    f.found_id,
    i.item_name,
    i.category,
    i.location AS found_location,
    f.date_found,
    f.storage_location,
    f.status,
    s.name AS found_by,
    s.email AS finder_email
FROM FOUND_ITEM f
JOIN ITEM i ON f.item_id = i.item_id
JOIN STUDENT s ON f.student_id = s.student_id
ORDER BY f.date_found DESC;`,

    "Q4": `-- Q4: JOIN - All Claims with Claimant Profile & Item
SELECT 
    c.claim_id,
    i.item_name,
    i.category,
    s.name AS claimant_name,
    s.student_id,
    c.claim_date,
    c.claim_status,
    c.proof_description
FROM CLAIM c
JOIN ITEM i ON c.item_id = i.item_id
JOIN STUDENT s ON c.student_id = s.student_id
ORDER BY c.claim_date DESC;`,

    "Q5": `-- Q5: LEFT OUTER JOIN - Items without any claims submitted
SELECT 
    i.item_id,
    i.item_name,
    i.category,
    i.location
FROM ITEM i
LEFT JOIN CLAIM c ON i.item_id = c.item_id
WHERE c.claim_id IS NULL;`,

    "Q6": `-- Q6: Aggregation & GROUP BY - Total Items per Category
SELECT 
    category, 
    COUNT(*) AS total_items 
FROM ITEM 
GROUP BY category 
ORDER BY total_items DESC;`,

    "Q7": `-- Q7: GROUP BY & HAVING - Departments with Items Reported
SELECT 
    s.department,
    COUNT(i.item_id) AS items_count
FROM STUDENT s
JOIN LOST_ITEM l ON s.student_id = l.student_id
JOIN ITEM i ON l.item_id = i.item_id
GROUP BY s.department
HAVING COUNT(i.item_id) >= 1;`,

    "Q8": `-- Q8: Nested Subquery - Students reporting both Lost & Found items
SELECT student_id, name, email, department
FROM STUDENT
WHERE student_id IN (SELECT student_id FROM LOST_ITEM)
  AND student_id IN (SELECT student_id FROM FOUND_ITEM);`,

    "Q9": `-- Q9: Querying Database VIEW 'vw_lost_items_detailed'
SELECT lost_id, item_name, category, location_lost, student_name, department, lost_status 
FROM vw_lost_items_detailed;`,

    "Q10": `-- Q10: Querying Database VIEW 'vw_claims_overview'
SELECT claim_id, item_name, claimant_name, claim_date, claim_status 
FROM vw_claims_overview;`
};

// Global application state
let studentsList = [];
let activeFoundItemsList = [];

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initDateInputs();
    refreshAllData();
    lucide.createIcons();

    // Event listener for DB Reset
    const resetBtn = document.getElementById('btn-reset-db');
    if (resetBtn) {
        resetBtn.addEventListener('click', handleResetDatabase);
    }
});

// Helper: refresh icons whenever DOM updates
function updateIcons() {
    setTimeout(() => {
        if (window.lucide) {
            lucide.createIcons();
        }
    }, 50);
}

// Utility: Debounce for live search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let iconName = 'info';
    if (type === 'success') iconName = 'check-circle';
    if (type === 'error') iconName = 'alert-circle';
    
    toast.innerHTML = `<i data-lucide="${iconName}"></i> <span>${message}</span>`;
    container.appendChild(toast);
    updateIcons();

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Set default dates to today for date pickers
function initDateInputs() {
    const today = new Date().toISOString().split('T')[0];
    ['lost-date', 'found-date', 'claim-date', 'return-date'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = today;
    });
}

// ====================================================================
// NAVIGATION & TABS
// ====================================================================
function initNavigation() {
    const navTabs = document.querySelectorAll('.nav-tab');
    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            switchTab(target);
        });
    });
}

function switchTab(tabId) {
    // Update active nav button
    document.querySelectorAll('.nav-tab').forEach(t => {
        if (t.getAttribute('data-tab') === tabId) {
            t.classList.add('active');
        } else {
            t.classList.remove('active');
        }
    });

    // Update active tab pane
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });

    const targetPane = document.getElementById(`tab-${tabId}`);
    if (targetPane) {
        targetPane.classList.add('active');
    }

    // Refresh tab-specific data
    if (tabId === 'dashboard') loadDashboardStats();
    if (tabId === 'lost-items') loadLostItems();
    if (tabId === 'found-items') loadFoundItems();
    if (tabId === 'claims') { loadClaims(); loadReturns(); }
    if (tabId === 'students') loadStudents();
    if (tabId === 'sql-lab') loadSchemaInfo();

    updateIcons();
}

// Refresh all sections
function refreshAllData() {
    loadStudentsDropdown();
    loadDashboardStats();
    loadLostItems();
    loadFoundItems();
    loadClaims();
    loadReturns();
    loadStudents();
    loadSchemaInfo();
}

// ====================================================================
// 1. DASHBOARD & ANALYTICS
// ====================================================================
async function loadDashboardStats() {
    try {
        const res = await fetch(`${API_BASE}/stats`);
        const data = await res.json();

        // Update KPIs
        const lostPending = data.lost_breakdown['Pending'] || 0;
        const lostTotal = Object.values(data.lost_breakdown).reduce((a, b) => a + b, 0);
        document.getElementById('kpi-lost-pending').innerText = lostPending;
        document.getElementById('kpi-lost-total').innerText = `${lostTotal} total reported`;

        const foundPending = data.found_breakdown['Pending'] || 0;
        const foundTotal = Object.values(data.found_breakdown).reduce((a, b) => a + b, 0);
        document.getElementById('kpi-found-pending').innerText = foundPending;
        document.getElementById('kpi-found-total').innerText = `${foundTotal} total recorded`;

        const claimsPending = data.claims_breakdown['Pending'] || 0;
        document.getElementById('kpi-claims-pending').innerText = claimsPending;
        document.getElementById('kpi-total-returns').innerText = data.total_returns || 0;

        // Update sidebar badges
        document.getElementById('badge-lost-count').innerText = lostPending;
        document.getElementById('badge-found-count').innerText = foundPending;
        document.getElementById('badge-claim-count').innerText = claimsPending;

        // Render Category Breakdown
        const catContainer = document.getElementById('category-distribution-list');
        if (data.categories && data.categories.length > 0) {
            catContainer.innerHTML = data.categories.map(c => `
                <div class="category-item">
                    <div class="category-info">
                        <span class="category-badge">${c.category}</span>
                    </div>
                    <strong style="color: #cbd5e1;">${c.count} items</strong>
                </div>
            `).join('');
        } else {
            catContainer.innerHTML = '<p class="text-muted">No items recorded yet.</p>';
        }

        // Render Recent Activity
        const actContainer = document.getElementById('recent-activities-list');
        if (data.recent_activities && data.recent_activities.length > 0) {
            actContainer.innerHTML = data.recent_activities.map(a => `
                <div class="activity-item">
                    <span class="activity-badge ${a.type}">${a.type}</span>
                    <div class="activity-details">
                        <strong>${escapeHtml(a.item_name)}</strong>
                        <p>By ${escapeHtml(a.student_name)} • ${a.date} • <span class="status-badge ${a.status.toLowerCase()}">${a.status}</span></p>
                    </div>
                </div>
            `).join('');
        } else {
            actContainer.innerHTML = '<p class="text-muted">No recent activities.</p>';
        }

        updateIcons();
    } catch (err) {
        console.error('Error loading dashboard stats:', err);
    }
}

// ====================================================================
// 2. LOST ITEMS CATALOG
// ====================================================================
async function loadLostItems() {
    const search = document.getElementById('lost-search-input')?.value || '';
    const category = document.getElementById('lost-category-filter')?.value || 'All';
    const status = document.getElementById('lost-status-filter')?.value || 'All';

    const container = document.getElementById('lost-items-container');
    container.innerHTML = '<div class="empty-state-text">Loading lost items...</div>';

    try {
        const url = `${API_BASE}/lost-items?search=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}&status=${encodeURIComponent(status)}`;
        const res = await fetch(url);
        const items = await res.json();

        if (items.length === 0) {
            container.innerHTML = '<div class="empty-state-text">No lost items match your search criteria.</div>';
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="item-card">
                <div class="item-card-header">
                    <div>
                        <span class="item-category-tag">${escapeHtml(item.category)}</span>
                        <h4 class="item-title">${escapeHtml(item.item_name)}</h4>
                    </div>
                    <span class="status-badge ${item.status.toLowerCase()}">${item.status}</span>
                </div>
                <div class="item-card-body">
                    <p class="item-desc">${escapeHtml(item.description || 'No specific description provided.')}</p>
                    <div class="item-meta-list">
                        <div class="item-meta-row">
                            <i data-lucide="map-pin"></i>
                            <span>Lost At: <strong>${escapeHtml(item.location)}</strong></span>
                        </div>
                        <div class="item-meta-row">
                            <i data-lucide="calendar"></i>
                            <span>Date Lost: <strong>${item.date_lost}</strong></span>
                        </div>
                        <div class="item-meta-row">
                            <i data-lucide="user"></i>
                            <span>Reported By: <strong>${escapeHtml(item.student_name)}</strong> (${item.student_id})</span>
                        </div>
                        <div class="item-meta-row">
                            <i data-lucide="phone"></i>
                            <span>Contact: <strong>${escapeHtml(item.student_phone)}</strong></span>
                        </div>
                    </div>
                </div>
                <div class="item-card-footer">
                    <small class="text-muted">Item Ref #${item.item_id}</small>
                    <span class="badge badge-info">${escapeHtml(item.department)}</span>
                </div>
            </div>
        `).join('');

        updateIcons();
    } catch (err) {
        container.innerHTML = `<div class="empty-state-text error">Error fetching lost items: ${err.message}</div>`;
    }
}

// ====================================================================
// 3. FOUND ITEMS CATALOG
// ====================================================================
async function loadFoundItems() {
    const search = document.getElementById('found-search-input')?.value || '';
    const category = document.getElementById('found-category-filter')?.value || 'All';
    const status = document.getElementById('found-status-filter')?.value || 'All';

    const container = document.getElementById('found-items-container');
    container.innerHTML = '<div class="empty-state-text">Loading found items...</div>';

    try {
        const url = `${API_BASE}/found-items?search=${encodeURIComponent(search)}&category=${encodeURIComponent(category)}&status=${encodeURIComponent(status)}`;
        const res = await fetch(url);
        const items = await res.json();
        activeFoundItemsList = items;

        if (items.length === 0) {
            container.innerHTML = '<div class="empty-state-text">No found items match your filter criteria.</div>';
            return;
        }

        container.innerHTML = items.map(item => `
            <div class="item-card">
                <div class="item-card-header">
                    <div>
                        <span class="item-category-tag">${escapeHtml(item.category)}</span>
                        <h4 class="item-title">${escapeHtml(item.item_name)}</h4>
                    </div>
                    <span class="status-badge ${item.status.toLowerCase()}">${item.status}</span>
                </div>
                <div class="item-card-body">
                    <p class="item-desc">${escapeHtml(item.description || 'No detailed condition notes.')}</p>
                    <div class="item-meta-list">
                        <div class="item-meta-row">
                            <i data-lucide="map-pin"></i>
                            <span>Found At: <strong>${escapeHtml(item.location)}</strong></span>
                        </div>
                        <div class="item-meta-row">
                            <i data-lucide="building-2"></i>
                            <span>Custody Desk: <strong>${escapeHtml(item.storage_location)}</strong></span>
                        </div>
                        <div class="item-meta-row">
                            <i data-lucide="calendar"></i>
                            <span>Date Found: <strong>${item.date_found}</strong></span>
                        </div>
                        <div class="item-meta-row">
                            <i data-lucide="user-check"></i>
                            <span>Finder: <strong>${escapeHtml(item.finder_name)}</strong> (${item.finder_id})</span>
                        </div>
                    </div>
                </div>
                <div class="item-card-footer">
                    <small class="text-muted">Item #${item.item_id} • ${item.claim_count || 0} claims</small>
                    ${item.status === 'Pending' ? `
                        <button class="btn btn-primary-sm" onclick="openClaimModal(${item.item_id}, '${escapeHtml(item.item_name)}', '${escapeHtml(item.category)}')">
                            <i data-lucide="shield-check"></i> Claim This Item
                        </button>
                    ` : `
                        <span class="badge badge-info">${item.status}</span>
                    `}
                </div>
            </div>
        `).join('');

        updateIcons();
    } catch (err) {
        container.innerHTML = `<div class="empty-state-text error">Error fetching found items: ${err.message}</div>`;
    }
}

// ====================================================================
// 4. CLAIMS & RETURNS
// ====================================================================
async function loadClaims() {
    const tbody = document.getElementById('claims-table-body');
    tbody.innerHTML = '<tr><td colspan="7" class="empty-state-text">Loading claims...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/claims`);
        const claims = await res.json();

        document.getElementById('claims-count-badge').innerText = `${claims.length} claims`;

        if (claims.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-state-text">No claims submitted yet.</td></tr>';
            return;
        }

        tbody.innerHTML = claims.map(c => `
            <tr>
                <td><code>#CLM-${c.claim_id}</code></td>
                <td>
                    <strong>${escapeHtml(c.item_name)}</strong><br>
                    <small class="text-muted">${escapeHtml(c.category)} (Item #${c.item_id})</small>
                </td>
                <td>
                    <strong>${escapeHtml(c.claimant_name)}</strong><br>
                    <small class="text-muted">${c.claimant_id} • ${escapeHtml(c.claimant_dept)}</small>
                </td>
                <td>${c.claim_date}</td>
                <td>
                    <span title="${escapeHtml(c.proof_description)}" style="cursor:help; border-bottom: 1px dotted #94a3b8;">
                        ${escapeHtml(c.proof_description.substring(0, 50))}${c.proof_description.length > 50 ? '...' : ''}
                    </span>
                </td>
                <td><span class="status-badge ${c.claim_status.toLowerCase()}">${c.claim_status}</span></td>
                <td>
                    ${c.claim_status === 'Pending' ? `
                        <div style="display:flex; gap:0.35rem;">
                            <button class="btn btn-success-sm" onclick="updateClaimStatus(${c.claim_id}, 'Approved')" title="Approve Claim">
                                <i data-lucide="check"></i> Approve
                            </button>
                            <button class="btn btn-danger-sm" onclick="updateClaimStatus(${c.claim_id}, 'Rejected')" title="Reject Claim">
                                <i data-lucide="x"></i> Reject
                            </button>
                        </div>
                    ` : `
                        <span class="text-muted">Settled</span>
                    `}
                </td>
            </tr>
        `).join('');

        updateIcons();
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-state-text error">Error: ${err.message}</td></tr>`;
    }
}

async function updateClaimStatus(claimId, newStatus) {
    if (!confirm(`Are you sure you want to mark Claim #${claimId} as '${newStatus}'?`)) return;

    try {
        const res = await fetch(`${API_BASE}/claims/${claimId}/status`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message, 'success');
            loadClaims();
            loadFoundItems();
            loadDashboardStats();
        } else {
            showToast(data.error || 'Failed to update status', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

async function loadReturns() {
    const tbody = document.getElementById('returns-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="empty-state-text">Loading return records...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/returns`);
        const returns = await res.json();

        document.getElementById('returns-count-badge').innerText = `${returns.length} returns`;

        if (returns.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state-text">No return handovers recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = returns.map(r => `
            <tr>
                <td><code>#RET-${r.return_id}</code></td>
                <td><strong>${escapeHtml(r.item_name)}</strong> <small class="text-muted">(${escapeHtml(r.category)})</small></td>
                <td>
                    <strong>${escapeHtml(r.student_name)}</strong><br>
                    <small class="text-muted">${r.student_id} • ${escapeHtml(r.department)}</small>
                </td>
                <td>${r.return_date}</td>
                <td>${escapeHtml(r.verified_by)}</td>
                <td><small>${escapeHtml(r.remarks || 'Handed over.')}</small></td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty-state-text error">Error: ${err.message}</td></tr>`;
    }
}

// ====================================================================
// 5. STUDENT DIRECTORY
// ====================================================================
async function loadStudents() {
    const tbody = document.getElementById('students-table-body');
    tbody.innerHTML = '<tr><td colspan="9" class="empty-state-text">Loading students...</td></tr>';

    try {
        const res = await fetch(`${API_BASE}/students`);
        const students = await res.json();
        studentsList = students;

        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="empty-state-text">No students registered.</td></tr>';
            return;
        }

        tbody.innerHTML = students.map(s => `
            <tr>
                <td><code>${s.student_id}</code></td>
                <td><strong>${escapeHtml(s.name)}</strong></td>
                <td><span class="badge badge-info">${escapeHtml(s.department)}</span></td>
                <td>${escapeHtml(s.email)}</td>
                <td>${escapeHtml(s.phone)}</td>
                <td><span class="status-badge ${s.lost_count > 0 ? 'pending' : ''}">${s.lost_count} lost</span></td>
                <td><span class="status-badge ${s.found_count > 0 ? 'approved' : ''}">${s.found_count} found</span></td>
                <td><span class="status-badge ${s.claim_count > 0 ? 'claimed' : ''}">${s.claim_count} claims</span></td>
                <td>
                    <button class="btn btn-outline-sm" onclick="showStudentHistory('${s.student_id}')">
                        <i data-lucide="eye"></i> History
                    </button>
                </td>
            </tr>
        `).join('');

        updateIcons();
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" class="empty-state-text error">Error: ${err.message}</td></tr>`;
    }
}

async function loadStudentsDropdown() {
    try {
        const res = await fetch(`${API_BASE}/students`);
        const students = await res.json();
        studentsList = students;

        const optionsHtml = students.map(s => `
            <option value="${s.student_id}">${s.name} (${s.student_id} - ${s.department})</option>
        `).join('');

        ['lost-student-id', 'found-student-id', 'claim-student-id', 'return-student-id'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.innerHTML = optionsHtml;
        });

        // Load items for return modal
        loadReturnItemsDropdown();
    } catch (err) {
        console.error('Error populating students dropdown:', err);
    }
}

async function loadReturnItemsDropdown() {
    try {
        const res = await fetch(`${API_BASE}/found-items`);
        const items = await res.json();
        const returnSelect = document.getElementById('return-item-id');
        if (returnSelect) {
            returnSelect.innerHTML = items.map(item => `
                <option value="${item.item_id}">#${item.item_id} - ${item.item_name} (${item.category}) [Status: ${item.status}]</option>
            `).join('');
        }
    } catch (err) {
        console.error('Error populating items for return dropdown:', err);
    }
}

async function showStudentHistory(studentId) {
    try {
        const res = await fetch(`${API_BASE}/students/${studentId}`);
        const data = await res.json();
        if (data.error) {
            showToast(data.error, 'error');
            return;
        }

        const s = data.student;
        const msg = `Student Profile: ${s.name} (${s.student_id})\nDept: ${s.department}\nEmail: ${s.email}\nPhone: ${s.phone}\n\nActivity Summary:\n• Lost items reported: ${data.lost_items.length}\n• Found items reported: ${data.found_items.length}\n• Claims submitted: ${data.claims.length}`;
        alert(msg);
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// ====================================================================
// 6. INTERACTIVE SQL QUERY LAB
// ====================================================================
function applyPresetQuery(presetKey) {
    const editor = document.getElementById('sql-query-input');
    if (presetKey && PRESET_QUERIES[presetKey]) {
        editor.value = PRESET_QUERIES[presetKey];
    }
}

function clearQueryEditor() {
    document.getElementById('sql-query-input').value = '';
    document.getElementById('query-preset-select').value = '';
}

async function executeUserQuery() {
    const query = document.getElementById('sql-query-input').value.trim();
    if (!query) {
        showToast('Please enter an SQL query to execute.', 'error');
        return;
    }

    const resultWrap = document.getElementById('sql-result-wrap');
    const metaSpan = document.getElementById('result-meta');
    const statsPill = document.getElementById('query-stats-pill');

    resultWrap.innerHTML = '<div class="empty-state-text">Executing query on database...</div>';
    statsPill.innerText = 'Executing...';

    try {
        const res = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await res.json();

        if (!data.success) {
            resultWrap.innerHTML = `
                <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 1rem; border-radius: 8px; color: #f87171; font-family: var(--font-mono); font-size: 0.85rem;">
                    <strong><i data-lucide="alert-triangle"></i> SQL Error:</strong><br>${escapeHtml(data.error)}
                </div>
            `;
            metaSpan.innerText = 'Execution Failed';
            statsPill.innerText = 'Error';
            updateIcons();
            return;
        }

        statsPill.innerText = `⏱ ${data.execution_time_ms} ms`;
        metaSpan.innerText = `${data.row_count} row(s) returned (${data.execution_time_ms} ms)`;

        if (data.is_select) {
            if (data.rows.length === 0) {
                resultWrap.innerHTML = '<div class="empty-state-text">Query executed successfully. 0 rows returned.</div>';
                return;
            }

            let tableHtml = '<table class="data-table"><thead><tr>';
            data.columns.forEach(col => {
                tableHtml += `<th>${escapeHtml(col)}</th>`;
            });
            tableHtml += '</tr></thead><tbody>';

            data.rows.forEach(row => {
                tableHtml += '<tr>';
                row.forEach(val => {
                    const displayVal = val === null ? '<span class="text-muted">NULL</span>' : escapeHtml(String(val));
                    tableHtml += `<td>${displayVal}</td>`;
                });
                tableHtml += '</tr>';
            });
            tableHtml += '</tbody></table>';

            resultWrap.innerHTML = tableHtml;
        } else {
            resultWrap.innerHTML = `
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); padding: 1.25rem; border-radius: 8px; color: #34d399;">
                    <i data-lucide="check-circle-2"></i> Query executed successfully. Rows affected: <strong>${data.row_count}</strong>.
                </div>
            `;
        }

        updateIcons();
    } catch (err) {
        resultWrap.innerHTML = `<div class="empty-state-text error">Execution Error: ${err.message}</div>`;
        statsPill.innerText = 'Failed';
    }
}

// Load Schema Explorer
async function loadSchemaInfo() {
    const grid = document.getElementById('schema-explorer-grid');
    if (!grid) return;

    try {
        const res = await fetch(`${API_BASE}/schema`);
        const schema = await res.json();

        grid.innerHTML = schema.map(tbl => `
            <div class="schema-table-card">
                <div class="schema-table-header">
                    <strong>${tbl.table_name}</strong>
                    <span class="badge badge-info">${tbl.row_count} rows</span>
                </div>
                <div class="schema-cols-list">
                    ${tbl.columns.map(c => `
                        <div class="schema-col-row">
                            <span class="${c.pk ? 'col-pk' : ''}">${c.pk ? '🔑 ' : ''}${c.name}</span>
                            <span class="col-type">${c.type}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `).join('');
    } catch (err) {
        grid.innerHTML = `<p class="text-muted">Error loading schema: ${err.message}</p>`;
    }
}

// ====================================================================
// 7. FORM SUBMISSIONS & MODAL HANDLERS
// ====================================================================
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        initDateInputs();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

function openClaimModal(itemId, itemName, itemCategory) {
    document.getElementById('claim-item-id').value = itemId;
    document.getElementById('claim-item-banner').innerHTML = `
        <strong>Claiming:</strong> ${escapeHtml(itemName)} <span class="badge badge-info">${escapeHtml(itemCategory)}</span> (Item #${itemId})
    `;
    openModal('modal-claim-item');
}

// Submit Report Lost Item
async function handleReportLost(e) {
    e.preventDefault();
    const payload = {
        student_id: document.getElementById('lost-student-id').value,
        item_name: document.getElementById('lost-item-name').value,
        category: document.getElementById('lost-category').value,
        location: document.getElementById('lost-location').value,
        date_lost: document.getElementById('lost-date').value,
        description: document.getElementById('lost-description').value
    };

    try {
        const res = await fetch(`${API_BASE}/lost-items`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Lost item reported successfully!', 'success');
            closeModal('modal-report-lost');
            document.getElementById('form-report-lost').reset();
            loadLostItems();
            loadDashboardStats();
            loadSchemaInfo();
        } else {
            showToast(data.error || 'Failed to report item', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// Submit Report Found Item
async function handleReportFound(e) {
    e.preventDefault();
    const payload = {
        student_id: document.getElementById('found-student-id').value,
        item_name: document.getElementById('found-item-name').value,
        category: document.getElementById('found-category').value,
        location: document.getElementById('found-location').value,
        date_found: document.getElementById('found-date').value,
        storage_location: document.getElementById('found-storage-location').value,
        description: document.getElementById('found-description').value
    };

    try {
        const res = await fetch(`${API_BASE}/found-items`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Found item reported successfully!', 'success');
            closeModal('modal-report-found');
            document.getElementById('form-report-found').reset();
            loadFoundItems();
            loadDashboardStats();
            loadSchemaInfo();
            loadReturnItemsDropdown();
        } else {
            showToast(data.error || 'Failed to record found item', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// Submit Ownership Claim
async function handleSubmitClaim(e) {
    e.preventDefault();
    const payload = {
        student_id: document.getElementById('claim-student-id').value,
        item_id: parseInt(document.getElementById('claim-item-id').value),
        claim_date: document.getElementById('claim-date').value,
        proof_description: document.getElementById('claim-proof').value
    };

    try {
        const res = await fetch(`${API_BASE}/claims`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Claim submitted successfully!', 'success');
            closeModal('modal-claim-item');
            document.getElementById('form-claim-item').reset();
            loadClaims();
            loadDashboardStats();
            loadSchemaInfo();
        } else {
            showToast(data.error || 'Failed to submit claim', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// Process Item Return Handover
async function handleProcessReturn(e) {
    e.preventDefault();
    const payload = {
        item_id: parseInt(document.getElementById('return-item-id').value),
        student_id: document.getElementById('return-student-id').value,
        return_date: document.getElementById('return-date').value,
        verified_by: document.getElementById('return-verified-by').value,
        remarks: document.getElementById('return-remarks').value
    };

    try {
        const res = await fetch(`${API_BASE}/returns`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast('Item return recorded and status updated across tables!', 'success');
            closeModal('modal-process-return');
            document.getElementById('form-process-return').reset();
            loadReturns();
            loadLostItems();
            loadFoundItems();
            loadClaims();
            loadDashboardStats();
            loadSchemaInfo();
        } else {
            showToast(data.error || 'Failed to process return', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// Register Student
async function handleAddStudent(e) {
    e.preventDefault();
    const payload = {
        student_id: document.getElementById('new-student-id').value,
        name: document.getElementById('new-student-name').value,
        email: document.getElementById('new-student-email').value,
        phone: document.getElementById('new-student-phone').value,
        department: document.getElementById('new-student-dept').value
    };

    try {
        const res = await fetch(`${API_BASE}/students`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            showToast(data.message, 'success');
            closeModal('modal-add-student');
            document.getElementById('form-add-student').reset();
            loadStudents();
            loadStudentsDropdown();
            loadDashboardStats();
            loadSchemaInfo();
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (err) {
        showToast(`Error: ${err.message}`, 'error');
    }
}

// Reset Database to Fresh Sample Dataset
async function handleResetDatabase() {
    if (!confirm('Are you sure you want to reset the database to its pristine Review 1 sample state? Any added records will be replaced.')) {
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/reset-demo`, { method: 'POST' });
        const data = await res.json();
        showToast(data.message, 'success');
        refreshAllData();
    } catch (err) {
        showToast(`Error resetting DB: ${err.message}`, 'error');
    }
}

// HTML escape helper
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
