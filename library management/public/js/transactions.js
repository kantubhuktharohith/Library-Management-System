/**
 * Transactions page logic — Issue, Return, History
 */
(async () => {
    if (!(await Auth.requireAuth())) return;
    Nav.init();
    loadTransactions();
    document.getElementById('status-filter').addEventListener('change', loadTransactions);

    // Auto-open modals from query params
    const action = new URLSearchParams(location.search).get('action');
    if (action === 'issue') openIssueModal();
    if (action === 'return') openReturnModal();
})();

async function loadTransactions() {
    const status = document.getElementById('status-filter').value;
    const params = status ? `?status=${status}` : '';

    try {
        const data = await API.get(`/api/transactions${params}`);
        renderTransactions(data.transactions);
    } catch (err) {
        Toast.error('Failed to load transactions: ' + err.message);
    }
}

function renderTransactions(transactions) {
    const container = document.getElementById('transactions-container');

    if (!transactions.length) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
                <h3>No Transactions Found</h3>
                <p>Issue your first book to get started.</p>
            </div>`;
        return;
    }

    const today = new Date().toISOString().split('T')[0];

    let html = `<div class="table-container"><table class="data-table">
        <thead><tr>
            <th>ID</th>
            <th>Book</th>
            <th>Member</th>
            <th>Issue Date</th>
            <th>Due Date</th>
            <th>Return Date</th>
            <th>Status</th>
            <th>Fine</th>
        </tr></thead><tbody>`;

    for (const t of transactions) {
        let status = t.Status;
        if (status === 'issued' && t.DueDate < today) status = 'overdue';

        html += `<tr>
            <td>${t.TransactionID}</td>
            <td><strong>${Utils.escapeHtml(t.BookTitle)}</strong><br><span class="text-muted" style="font-size:var(--font-size-xs)">${Utils.escapeHtml(t.BookAuthor)}</span></td>
            <td>${Utils.escapeHtml(t.MemberName)}</td>
            <td>${Utils.formatDate(t.IssueDate)}</td>
            <td>${Utils.formatDate(t.DueDate)}</td>
            <td>${t.ReturnDate ? Utils.formatDate(t.ReturnDate) : '—'}</td>
            <td>${Utils.getStatusBadge(status)}</td>
            <td>${t.Fine > 0 ? Utils.formatCurrency(t.Fine) : '—'}</td>
        </tr>`;
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function openIssueModal() {
    document.getElementById('issue-form').reset();
    Modal.open('issue-modal');
}

function openReturnModal() {
    document.getElementById('return-form').reset();
    Modal.open('return-modal');
}

async function handleIssue(e) {
    e.preventDefault();
    const memberId = parseInt(document.getElementById('issue-member-id').value);
    const bookId = parseInt(document.getElementById('issue-book-id').value);

    try {
        const data = await API.post('/api/transactions/issue', { memberId, bookId });
        Toast.success(data.message);
        Modal.close('issue-modal');
        loadTransactions();
    } catch (err) {
        Toast.error(err.message);
    }
}

async function handleReturn(e) {
    e.preventDefault();
    const memberId = parseInt(document.getElementById('return-member-id').value);
    const bookId = parseInt(document.getElementById('return-book-id').value);

    try {
        const data = await API.post('/api/transactions/return', { memberId, bookId });
        let msg = data.message;
        if (data.fine > 0) {
            msg += ` | Fine: ${Utils.formatCurrency(data.fine)} (${data.overdueDays} days overdue)`;
        }
        Toast.success(msg);
        Modal.close('return-modal');
        loadTransactions();
    } catch (err) {
        Toast.error(err.message);
    }
}
