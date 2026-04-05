/**
 * Dashboard page logic
 */
(async () => {
    if (!(await Auth.requireAuth())) return;
    Nav.init();
    loadDashboard();
})();

async function loadDashboard() {
    try {
        const data = await API.get('/api/reports/dashboard');
        const s = data.stats;

        document.getElementById('stat-books').textContent = s.totalBooks;
        document.getElementById('stat-copies').textContent = `${s.totalCopies} total copies`;
        document.getElementById('stat-members').textContent = s.totalMembers;
        document.getElementById('stat-issued').textContent = s.totalIssued;
        document.getElementById('stat-overdue').textContent = s.totalOverdue;
        document.getElementById('stat-returned').textContent = s.totalReturned;
        document.getElementById('stat-fines').textContent = Utils.formatCurrency(s.totalFines);

        // Update overdue badge in nav
        if (s.totalOverdue > 0) {
            const navTxn = document.getElementById('nav-transactions');
            if (navTxn) {
                const badge = document.createElement('span');
                badge.className = 'nav-badge';
                badge.textContent = s.totalOverdue;
                navTxn.appendChild(badge);
            }
        }

        renderRecentTransactions(data.recentTransactions);
    } catch (err) {
        Toast.error('Failed to load dashboard: ' + err.message);
    }
}

function renderRecentTransactions(transactions) {
    const container = document.getElementById('recent-table-container');

    if (!transactions.length) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                <h3>No Transactions Yet</h3>
                <p>Issue your first book to get started.</p>
            </div>`;
        return;
    }

    let html = `<table class="data-table">
        <thead><tr>
            <th>Book</th>
            <th>Member</th>
            <th>Issue Date</th>
            <th>Due Date</th>
            <th>Status</th>
            <th>Fine</th>
        </tr></thead><tbody>`;

    for (const t of transactions) {
        const today = new Date().toISOString().split('T')[0];
        let status = t.Status;
        if (status === 'issued' && t.DueDate < today) status = 'overdue';

        html += `<tr>
            <td><strong>${Utils.escapeHtml(t.BookTitle)}</strong></td>
            <td>${Utils.escapeHtml(t.MemberName)}</td>
            <td>${Utils.formatDate(t.IssueDate)}</td>
            <td>${Utils.formatDate(t.DueDate)}</td>
            <td>${Utils.getStatusBadge(status)}</td>
            <td>${t.Fine > 0 ? Utils.formatCurrency(t.Fine) : '—'}</td>
        </tr>`;
    }

    html += '</tbody></table>';
    container.innerHTML = html;
}
