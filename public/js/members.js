/**
 * Members page logic — CRUD, search
 */
let allMembers = [];

(async () => {
    if (!(await Auth.requireAuth())) return;
    Nav.init();
    loadMembers();
    document.getElementById('member-search').addEventListener('input', Utils.debounce(loadMembers, 300));

    if (new URLSearchParams(location.search).get('action') === 'add') {
        openAddMemberModal();
    }
})();

async function loadMembers() {
    const search = document.getElementById('member-search').value;
    const params = search ? `?search=${encodeURIComponent(search)}` : '';

    try {
        const data = await API.get(`/api/members${params}`);
        allMembers = data.members;
        renderMembers(allMembers);
    } catch (err) {
        Toast.error('Failed to load members: ' + err.message);
    }
}

function renderMembers(members) {
    const container = document.getElementById('members-container');

    if (!members.length) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
                <h3>No Members Found</h3>
                <p>Try a different search or add new members.</p>
            </div>`;
        return;
    }

    let html = `<div class="table-container"><table class="data-table">
        <thead><tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Type</th>
            <th>Books Issued</th>
            <th>Expiry</th>
            <th>Actions</th>
        </tr></thead><tbody>`;

    for (const m of members) {
        const typeClass = m.MembershipType === 'Faculty' ? 'badge-info' : m.MembershipType === 'Guest' ? 'badge-warning' : 'badge-purple';
        html += `<tr>
            <td>${m.MemberID}</td>
            <td><strong>${Utils.escapeHtml(m.Name)}</strong></td>
            <td>${Utils.escapeHtml(m.Email)}</td>
            <td>${Utils.escapeHtml(m.Phone)}</td>
            <td><span class="badge ${typeClass}">${m.MembershipType}</span></td>
            <td>${m.BooksIssuedCount}</td>
            <td>${Utils.formatDate(m.ExpiryDate)}</td>
            <td>
                <div class="action-btns">
                    <button class="action-btn edit" title="Edit" onclick="openEditMemberModal(${m.MemberID})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="action-btn delete" title="Delete" onclick="deleteMember(${m.MemberID}, '${Utils.escapeHtml(m.Name)}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </td>
        </tr>`;
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function openAddMemberModal() {
    document.getElementById('member-modal-title').textContent = 'Add Member';
    document.getElementById('member-submit-btn').textContent = 'Add Member';
    document.getElementById('member-form').reset();
    document.getElementById('member-edit-id').value = '';
    document.getElementById('member-email-group').style.display = '';
    document.getElementById('member-password-group').style.display = '';
    Modal.open('member-modal');
}

function openEditMemberModal(id) {
    const member = allMembers.find(m => m.MemberID === id);
    if (!member) return;

    document.getElementById('member-modal-title').textContent = 'Edit Member';
    document.getElementById('member-submit-btn').textContent = 'Save Changes';
    document.getElementById('member-edit-id').value = id;
    document.getElementById('member-name').value = member.Name;
    document.getElementById('member-email').value = member.Email;
    document.getElementById('member-phone').value = member.Phone;
    document.getElementById('member-type').value = member.MembershipType;
    document.getElementById('member-email-group').style.display = 'none'; // Can't change email
    document.getElementById('member-password-group').style.display = 'none';
    Modal.open('member-modal');
}

async function handleMemberSubmit(e) {
    e.preventDefault();
    const editId = document.getElementById('member-edit-id').value;

    if (editId) {
        try {
            await API.put(`/api/members/${editId}`, {
                name: document.getElementById('member-name').value,
                phone: document.getElementById('member-phone').value,
                membershipType: document.getElementById('member-type').value,
            });
            Toast.success('Member updated successfully');
            Modal.close('member-modal');
            loadMembers();
        } catch (err) {
            Toast.error(err.message);
        }
    } else {
        const password = document.getElementById('member-password').value || 'member123';
        try {
            await API.post('/api/members', {
                name: document.getElementById('member-name').value,
                email: document.getElementById('member-email').value,
                phone: document.getElementById('member-phone').value,
                membershipType: document.getElementById('member-type').value,
                password: password,
            });
            Toast.success('Member added successfully');
            Modal.close('member-modal');
            loadMembers();
        } catch (err) {
            Toast.error(err.message);
        }
    }
}

async function deleteMember(id, name) {
    const ok = await Modal.confirm(`Are you sure you want to delete member "<strong>${name}</strong>"? All their transaction history will also be removed.`, 'Delete Member');
    if (!ok) return;

    try {
        await API.delete(`/api/members/${id}`);
        Toast.success('Member deleted successfully');
        loadMembers();
    } catch (err) {
        Toast.error(err.message);
    }
}
