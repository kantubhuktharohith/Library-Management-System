/**
 * Book Requests page logic
 */
(async () => {
    if (!(await Auth.requireAuth())) return;
    Nav.init();
    loadRequests();
    document.getElementById('status-filter').addEventListener('change', loadRequests);
})();

async function loadRequests() {
    const status = document.getElementById('status-filter').value;
    const params = status ? `?status=${status}` : '';

    try {
        const data = await API.get(`/api/requests${params}`);
        renderRequests(data.requests);
    } catch (err) {
        Toast.error('Failed to load requests: ' + err.message);
    }
}

function renderRequests(requests) {
    const container = document.getElementById('requests-container');
    const isAdmin = Auth.isAdmin();

    if (!requests.length) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <h3>No Requests Found</h3>
                <p>${isAdmin ? 'No pending requests from members.' : 'You have not made any book requests yet.'}</p>
            </div>`;
        return;
    }

    let html = `<div class="table-container"><table class="data-table">
        <thead><tr>
            <th>Date</th>
            <th>Book</th>
            ${isAdmin ? '<th>Member</th>' : ''}
            <th>Message</th>
            <th>Status</th>
            <th>Admin Note</th>
            <th>Actions</th>
        </tr></thead><tbody>`;

    for (const r of requests) {
        let statusBadge = '';
        if (r.Status === 'pending') statusBadge = '<span class="badge badge-warning">Pending</span>';
        else if (r.Status === 'approved') statusBadge = '<span class="badge badge-success">Approved/Issued</span>';
        else if (r.Status === 'rejected') statusBadge = '<span class="badge badge-danger">Rejected</span>';

        html += `<tr>
            <td>${Utils.formatDate(r.RequestDate)}</td>
            <td><strong>${Utils.escapeHtml(r.BookTitle)}</strong><br><span style="font-size:var(--font-size-xs)" class="text-muted">${Utils.escapeHtml(r.BookAuthor)}</span></td>
            ${isAdmin ? `<td>${Utils.escapeHtml(r.MemberName)}</td>` : ''}
            <td>${Utils.escapeHtml(r.Message || '—')}</td>
            <td>${statusBadge}</td>
            <td><span style="font-size:var(--font-size-xs)" class="text-muted">${Utils.escapeHtml(r.AdminResponse || '—')}</span></td>
            <td>
                <div class="action-btns">`;
        
        if (r.Status === 'pending') {
            if (isAdmin) {
                html += `
                    <button class="action-btn success" title="Approve & Issue" onclick="openResponseModal(${r.RequestID}, 'approve')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--success)"><polyline points="20 6 9 17 4 12"/></svg>
                    </button>
                    <button class="action-btn delete" title="Reject" onclick="openResponseModal(${r.RequestID}, 'reject')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color:var(--danger)"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>`;
            } else {
                html += `
                    <button class="action-btn delete" title="Cancel Request" onclick="cancelRequest(${r.RequestID})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                    </button>`;
            }
        }
        
        html += `</div></td></tr>`;
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function openResponseModal(id, action) {
    document.getElementById('response-request-id').value = id;
    document.getElementById('response-action').value = action;
    document.getElementById('response-message').value = '';
    
    document.getElementById('response-modal-title').textContent = action === 'approve' ? 'Approve & Issue Book' : 'Reject Request';
    document.getElementById('response-submit-btn').textContent = action === 'approve' ? 'Approve Request' : 'Reject Request';
    
    Modal.open('response-modal');
}

async function handleResponseSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('response-request-id').value;
    const action = document.getElementById('response-action').value;
    const message = document.getElementById('response-message').value;

    try {
        const data = await API.post(`/api/requests/${id}/${action}`, { response: message });
        Toast.success(data.message);
        Modal.close('response-modal');
        loadRequests();
    } catch (err) {
        Toast.error(err.message);
    }
}

async function cancelRequest(id) {
    const ok = await Modal.confirm('Are you sure you want to cancel this request?');
    if (!ok) return;

    try {
        await API.delete(`/api/requests/${id}`);
        Toast.success('Request cancelled');
        loadRequests();
    } catch (err) {
        Toast.error(err.message);
    }
}
