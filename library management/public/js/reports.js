/**
 * Reports page logic — Issued, Overdue, Activity reports
 */
let currentReport = 'issued';
let currentReportData = [];

(async () => {
    if (!(await Auth.requireAuth())) return;
    Nav.init();
    loadReport('issued');
})();

function switchReport(type) {
    currentReport = type;
    ['issued', 'overdue', 'activity'].forEach(t => {
        document.getElementById(`tab-${t}`).classList.toggle('active', t === type);
    });
    loadReport(type);
}

async function loadReport(type) {
    const container = document.getElementById('report-container');
    container.innerHTML = '<div class="loader"><div class="spinner"></div></div>';

    try {
        let data;
        switch (type) {
            case 'issued':
                data = await API.get('/api/reports/issued');
                currentReportData = data.report;
                renderIssuedReport(data.report);
                break;
            case 'overdue':
                data = await API.get('/api/reports/overdue');
                currentReportData = data.report;
                renderOverdueReport(data.report);
                break;
            case 'activity':
                data = await API.get('/api/reports/activity');
                currentReportData = data.report;
                renderActivityReport(data.report);
                break;
        }
    } catch (err) {
        Toast.error('Failed to load report: ' + err.message);
    }
}

function renderIssuedReport(items) {
    const container = document.getElementById('report-container');

    if (!items.length) {
        container.innerHTML = '<div class="empty-state"><h3>No books currently issued</h3><p>All books are available in the library.</p></div>';
        return;
    }

    let html = `<div class="table-container"><table class="data-table">
        <thead><tr>
            <th>Book</th>
            <th>Author</th>
            <th>Member</th>
            <th>Email</th>
            <th>Issue Date</th>
            <th>Due Date</th>
            <th>Status</th>
        </tr></thead><tbody>`;

    const today = new Date().toISOString().split('T')[0];

    for (const t of items) {
        const isOverdue = t.DueDate < today;
        html += `<tr>
            <td><strong>${Utils.escapeHtml(t.BookTitle)}</strong></td>
            <td>${Utils.escapeHtml(t.BookAuthor)}</td>
            <td>${Utils.escapeHtml(t.MemberName)}</td>
            <td>${Utils.escapeHtml(t.MemberEmail)}</td>
            <td>${Utils.formatDate(t.IssueDate)}</td>
            <td>${Utils.formatDate(t.DueDate)}</td>
            <td>${isOverdue ? Utils.getStatusBadge('overdue') : Utils.getStatusBadge('issued')}</td>
        </tr>`;
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function renderOverdueReport(items) {
    const container = document.getElementById('report-container');

    if (!items.length) {
        container.innerHTML = '<div class="empty-state"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg><h3>No Overdue Books</h3><p>All issued books are within their due dates.</p></div>';
        return;
    }

    let html = `<div class="table-container"><table class="data-table">
        <thead><tr>
            <th>Book</th>
            <th>Member</th>
            <th>Phone</th>
            <th>Issue Date</th>
            <th>Due Date</th>
            <th>Days Overdue</th>
            <th>Fine (₹)</th>
        </tr></thead><tbody>`;

    for (const t of items) {
        html += `<tr>
            <td><strong>${Utils.escapeHtml(t.BookTitle)}</strong></td>
            <td>${Utils.escapeHtml(t.MemberName)}</td>
            <td>${Utils.escapeHtml(t.MemberPhone || '—')}</td>
            <td>${Utils.formatDate(t.IssueDate)}</td>
            <td>${Utils.formatDate(t.DueDate)}</td>
            <td><span class="badge badge-danger">${t.overdueDays} days</span></td>
            <td><strong class="text-danger">${Utils.formatCurrency(t.currentFine)}</strong></td>
        </tr>`;
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function renderActivityReport(items) {
    const container = document.getElementById('report-container');

    if (!items.length) {
        container.innerHTML = '<div class="empty-state"><h3>No Member Activity</h3><p>No members have any transactions yet.</p></div>';
        return;
    }

    let html = `<div class="table-container"><table class="data-table">
        <thead><tr>
            <th>Member</th>
            <th>Email</th>
            <th>Type</th>
            <th>Total Transactions</th>
            <th>Currently Issued</th>
            <th>Total Returned</th>
            <th>Total Fines</th>
        </tr></thead><tbody>`;

    for (const m of items) {
        html += `<tr>
            <td><strong>${Utils.escapeHtml(m.Name)}</strong></td>
            <td>${Utils.escapeHtml(m.Email)}</td>
            <td><span class="badge badge-purple">${m.MembershipType}</span></td>
            <td>${m.totalTransactions}</td>
            <td>${m.currentlyIssued || 0}</td>
            <td>${m.totalReturned || 0}</td>
            <td>${m.totalFines > 0 ? Utils.formatCurrency(m.totalFines) : '—'}</td>
        </tr>`;
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function exportReport() {
    if (!currentReportData.length) {
        Toast.warning('No data to export');
        return;
    }
    Utils.downloadCSV(currentReportData, `${currentReport}_report`);
    Toast.success('Report exported successfully');
}
