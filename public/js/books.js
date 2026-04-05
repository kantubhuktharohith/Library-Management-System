/**
 * Books page logic — CRUD, search, filter
 */

let allBooks = [];

(async () => {
    if (!(await Auth.requireAuth())) return;
    Nav.init();
    loadBooks();
    loadCategories();

    // Search with debounce
    document.getElementById('book-search').addEventListener('input', Utils.debounce(loadBooks, 300));
    document.getElementById('category-filter').addEventListener('change', loadBooks);

    // Auto-open modal if ?action=add
    if (new URLSearchParams(location.search).get('action') === 'add') {
        openAddBookModal();
    }
})();

async function loadBooks() {
    const search = document.getElementById('book-search').value;
    const category = document.getElementById('category-filter').value;
    const params = new URLSearchParams();
    if (search) params.set('search', search);
    if (category) params.set('category', category);

    try {
        const data = await API.get(`/api/books?${params}`);
        allBooks = data.books;
        renderBooks(allBooks);
    } catch (err) {
        Toast.error('Failed to load books: ' + err.message);
    }
}

async function loadCategories() {
    try {
        const data = await API.get('/api/books/categories');
        const select = document.getElementById('category-filter');
        data.categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.textContent = cat;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error('Failed to load categories:', err);
    }
}

function renderBooks(books) {
    const container = document.getElementById('books-container');
    const isAdmin = Auth.isAdmin();

    if (!books.length) {
        container.innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                <h3>No Books Found</h3>
                <p>Try a different search or add new books.</p>
            </div>`;
        return;
    }

    let html = `<div class="table-container"><table class="data-table">
        <thead><tr>
            <th>ID</th>
            <th>Title</th>
            <th>Author</th>
            <th>Category</th>
            <th>ISBN</th>
            <th>Availability</th>
            ${isAdmin ? '<th>Actions</th>' : ''}
        </tr></thead><tbody>`;

    for (const b of books) {
        html += `<tr>
            <td>${b.BookID}</td>
            <td><strong>${Utils.escapeHtml(b.Title)}</strong>${b.Publisher ? `<br><span class="text-muted" style="font-size:var(--font-size-xs)">${Utils.escapeHtml(b.Publisher)}</span>` : ''}</td>
            <td>${Utils.escapeHtml(b.Author)}</td>
            <td><span class="badge badge-purple">${Utils.escapeHtml(b.Category)}</span></td>
            <td style="font-size:var(--font-size-xs)">${Utils.escapeHtml(b.ISBN || '—')}</td>
            <td>${Utils.getAvailabilityHtml(b.Quantity, b.IssuedCount)}</td>
            ${isAdmin ? `<td>
                <div class="action-btns">
                    <button class="action-btn edit" title="Edit" onclick="openEditBookModal(${b.BookID})">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                    </button>
                    <button class="action-btn delete" title="Delete" onclick="deleteBook(${b.BookID}, '${Utils.escapeHtml(b.Title)}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                    </button>
                </div>
            </td>` : `<td>
                <div class="action-btns">
                    <button class="btn btn-primary btn-sm" onclick="requestBook(${b.BookID}, '${Utils.escapeHtml(b.Title)}')">Request</button>
                </div>
            </td>`}
        </tr>`;
    }

    html += '</tbody></table></div>';
    container.innerHTML = html;
}

function openAddBookModal() {
    document.getElementById('book-modal-title').textContent = 'Add Book';
    document.getElementById('book-submit-btn').textContent = 'Add Book';
    document.getElementById('book-form').reset();
    document.getElementById('book-edit-id').value = '';
    Modal.open('book-modal');
}

function openEditBookModal(id) {
    const book = allBooks.find(b => b.BookID === id);
    if (!book) return;

    document.getElementById('book-modal-title').textContent = 'Edit Book';
    document.getElementById('book-submit-btn').textContent = 'Save Changes';
    document.getElementById('book-edit-id').value = id;
    document.getElementById('book-title').value = book.Title;
    document.getElementById('book-author').value = book.Author;
    document.getElementById('book-publisher').value = book.Publisher || '';
    document.getElementById('book-category').value = book.Category || '';
    document.getElementById('book-isbn').value = book.ISBN || '';
    document.getElementById('book-quantity').value = book.Quantity;
    Modal.open('book-modal');
}

async function handleBookSubmit(e) {
    e.preventDefault();
    const editId = document.getElementById('book-edit-id').value;
    const body = {
        title: document.getElementById('book-title').value,
        author: document.getElementById('book-author').value,
        publisher: document.getElementById('book-publisher').value,
        category: document.getElementById('book-category').value,
        isbn: document.getElementById('book-isbn').value,
        quantity: parseInt(document.getElementById('book-quantity').value),
    };

    try {
        if (editId) {
            await API.put(`/api/books/${editId}`, body);
            Toast.success('Book updated successfully');
        } else {
            await API.post('/api/books', body);
            Toast.success('Book added successfully');
        }
        Modal.close('book-modal');
        loadBooks();
    } catch (err) {
        Toast.error(err.message);
    }
}

async function deleteBook(id, title) {
    const ok = await Modal.confirm(`Are you sure you want to delete "<strong>${title}</strong>"? This action cannot be undone.`, 'Delete Book');
    if (!ok) return;

    try {
        await API.delete(`/api/books/${id}`);
        Toast.success('Book deleted successfully');
        loadBooks();
    } catch (err) {
        Toast.error(err.message);
    }
}

async function requestBook(id, title) {
    const ok = await Modal.confirm(`Do you want to send a request to the admin for the book "<strong>${title}</strong>"?`, 'Request Book');
    if (!ok) return;

    try {
        const data = await API.post('/api/requests', { bookId: id, message: '' });
        Toast.success(data.message);
    } catch (err) {
        Toast.error(err.message);
    }
}
