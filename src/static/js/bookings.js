const BOOKINGS_PAGE_SIZE = 5;
const bookingsState = {
    all: [],
    filtered: [],
    status: 'all',
    page: 1,
    pageSize: BOOKINGS_PAGE_SIZE,
    isStaffOrAdmin: false
};

async function loadBookings(filterStatus = bookingsState.status) {
    const container = document.getElementById('bookings-container');
    const emptyState = document.getElementById('empty-state');
    const pagination = document.getElementById('bookings-pagination');
    const bookingsSection = document.querySelector('.bookings-section'); 

    if (!authManager.isAuthenticated()) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: #666;">
                <h2>Увійдіть для перегляду та редагування деталей бронювань</h2>
            </div>
        `;
        return;
    }

    if (bookingsSection) {
        bookingsSection.style.display = 'block';
    }

    bookingsState.status = filterStatus || 'all';
    bookingsState.page = 1;

    try {
        const response = await fetch('/api/v1/bookings/');
        if (!response.ok) throw new Error('Помилка завантаження');

        let bookings = await response.json();
        bookings = Array.isArray(bookings) ? bookings : [];

        const isStaffOrAdmin = authManager.user.role === 'ADMIN' || authManager.user.role === 'STAFF';
        bookingsState.isStaffOrAdmin = isStaffOrAdmin;

        if (!isStaffOrAdmin) {
            bookings = bookings.filter(b => b.user_id === authManager.user.id);
        }
        bookingsState.all = bookings;
        applyFiltersAndRender();
    } catch (error) {
        console.error('Error loading bookings:', error);
        container.innerHTML = '<p class="error-message">Помилка завантаження бронювань. Спробуйте пізніше.</p>';
        if (pagination) {
            pagination.style.display = 'none';
            pagination.innerHTML = '';
        }
    }
}

function createBookingCard(booking) {
    const checkIn = new Date(booking.check_in_date).toLocaleDateString('uk-UA');
    const checkOut = new Date(booking.check_out_date).toLocaleDateString('uk-UA');
    const created = new Date(booking.created_at).toLocaleDateString('uk-UA');
    const updated = booking.updated_at ? new Date(booking.updated_at).toLocaleDateString('uk-UA') : null;

    const nights = Math.ceil(
        (new Date(booking.check_out_date) - new Date(booking.check_in_date)) / (1000 * 60 * 60 * 24)
    );

    const statusText = {
        'ACTIVE': 'Активне',
        'COMPLETED': 'Завершене',
        'CANCELLED': 'Скасоване'
    };

    const canEdit = (() => {
        const u = authManager && authManager.user;
        if (!u) return false;
        const role = u.role;
        const isStaffOrAdmin = role === 'ADMIN' || role === 'STAFF';
        const isOwner = booking.user_id && u.id === booking.user_id;
        return (isStaffOrAdmin || isOwner) && booking.status === 'ACTIVE';
    })();

    return `
        <div class="booking-card" data-booking-code="${booking.booking_code}">
            <div class="booking-header">
                <div>
                    <div class="booking-code">Код бронювання: ${booking.booking_code}</div>
                    <div style="margin-top: 5px; color: var(--gray); font-size: 13px;">
                        Створено: ${created}${updated ? ` · Оновлено: ${updated}` : ''}
                    </div>
                </div>
                <span class="booking-status status-${booking.status}">
                    ${statusText[booking.status] || booking.status}
                </span>
            </div>

            <div class="booking-details">
                <div class="detail-item">
                    <span class="detail-label">Номер</span>
                    <span class="detail-value">#${booking.room_id}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Заїзд</span>
                    <span class="detail-value">${checkIn}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Виїзд</span>
                    <span class="detail-value">${checkOut}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Ночей</span>
                    <span class="detail-value">${nights}</span>
                </div>
            </div>

            ${booking.special_requests ? `
                <div class="booking-special">
                    <h4>Особливі побажання:</h4>
                    <p>${booking.special_requests}</p>
                </div>
            ` : ''}

            <div class="booking-actions">
                ${booking.status === 'ACTIVE' ? `
                    <button class="btn btn-small btn-secondary" onclick="viewBookingDetails('${booking.booking_code}')">
                        Детальніше
                    </button>
                    ${canEdit ? `
                    <button class="btn btn-small btn-primary" onclick='openEditBooking(${JSON.stringify(booking)})'>
                        Редагувати
                    </button>` : ''}
                    <button class="btn btn-small btn-danger" onclick="cancelBooking('${booking.booking_code}')">
                        Скасувати
                    </button>
                ` : `
                    <button class="btn btn-small btn-secondary" onclick="viewBookingDetails('${booking.booking_code}')">
                        Детальніше
                    </button>
                `}
            </div>
        </div>
    `;
}

function applyFiltersAndRender() {
    const container = document.getElementById('bookings-container');
    const emptyState = document.getElementById('empty-state');
    const pagination = document.getElementById('bookings-pagination');

    let filtered = bookingsState.all;
    if (bookingsState.status !== 'all') {
        filtered = filtered.filter(b => b.status === bookingsState.status);
    }

    bookingsState.filtered = filtered;

    if (!filtered || filtered.length === 0) {
        if (container) container.innerHTML = '';
        renderEmptyState(emptyState, bookingsState.status, bookingsState.isStaffOrAdmin);
        hidePagination(pagination);
        return;
    }

    if (emptyState) {
        emptyState.style.display = 'none';
    }

    renderPagedBookings(container, pagination);
}

function renderPagedBookings(container, pagination) {
    const totalPages = Math.max(1, Math.ceil(bookingsState.filtered.length / bookingsState.pageSize));
    if (bookingsState.page > totalPages) {
        bookingsState.page = totalPages;
    }

    const start = (bookingsState.page - 1) * bookingsState.pageSize;
    const pageItems = bookingsState.filtered.slice(start, start + bookingsState.pageSize);
    if (container) {
        container.innerHTML = pageItems.map(createBookingCard).join('');
    }
    renderPagination(pagination, totalPages);
}

function renderPagination(paginationEl, totalPages) {
    if (!paginationEl) return;

    if (totalPages <= 1) {
        hidePagination(paginationEl);
        return;
    }

    paginationEl.style.display = 'flex';
    const current = bookingsState.page;

    paginationEl.innerHTML = `
        <button class="page-btn" data-page="${current - 1}" ${current === 1 ? 'disabled' : ''}>Попередня</button>
        <span class="page-info">Сторінка ${current} з ${totalPages}</span>
        <button class="page-btn" data-page="${current + 1}" ${current >= totalPages ? 'disabled' : ''}>Наступна</button>
    `;

    paginationEl.querySelectorAll('button[data-page]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetPage = Number(e.currentTarget.dataset.page);
            setPage(targetPage);
        });
    });
}

function setPage(targetPage) {
    const totalPages = Math.max(1, Math.ceil(bookingsState.filtered.length / bookingsState.pageSize));
    bookingsState.page = Math.min(Math.max(1, targetPage), totalPages);
    const container = document.getElementById('bookings-container');
    const pagination = document.getElementById('bookings-pagination');
    renderPagedBookings(container, pagination);
}

function hidePagination(paginationEl) {
    if (!paginationEl) return;
    paginationEl.style.display = 'none';
    paginationEl.innerHTML = '';
}

function renderEmptyState(emptyState, filterStatus, isStaffOrAdmin) {
    if (!emptyState) return;
    emptyState.style.display = 'block';
    emptyState.innerHTML = `
        <div class="empty-state">
            <h3>Бронювання не знайдені</h3>
            <p>${filterStatus !== 'all' ? `Немає бронювань зі статусом "${filterStatus}"` : 'У вас ще немає бронювань'}</p>
            ${!isStaffOrAdmin ? `
                <button class="btn btn-primary" onclick="document.getElementById('create-booking-btn').click()">
                    Створити перше бронювання
                </button>
            ` : ''}
        </div>
    `;
}

async function cancelBooking(bookingCode) {
    if (!confirm('Ви впевнені, що хочете скасувати це бронювання?')) return;

    try {
        const response = await fetch(`/api/v1/bookings/${bookingCode}`, { method: 'DELETE' });
        if (response.ok) {
            alert('Бронювання успішно скасовано');
            loadBookings();
        } else {
            const error = await response.json();
            alert('Помилка скасування: ' + (error.message || 'Невідома помилка'));
        }
    } catch (error) {
        console.error('Error cancelling booking:', error);
        alert('Помилка зʼєднання з сервером');
    }
}

function viewBookingDetails(bookingCode) {
    globalThis.location.href = `/booking/details?code=${bookingCode}`;
}

function toggleGuestDataFields() {
    const isAuthenticated = authManager.isAuthenticated();
    const isStaffOrAdmin = isAuthenticated && 
        (authManager.user.role === 'ADMIN' || authManager.user.role === 'STAFF');
    
    const guestFields = [
        'guest_email',
        'guest_first_name', 
        'guest_last_name',
        'guest_phone'
    ];
    
    if (isStaffOrAdmin) {
        guestFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.removeAttribute('readonly');
                field.style.backgroundColor = '';
            }
        });
    } else if (isAuthenticated) {
        guestFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.setAttribute('readonly', 'readonly');
                field.style.backgroundColor = '#f5f5f5';
            }
        });
    }
}

function autofillGuestData() {
    if (!authManager.isAuthenticated()) return;

    const user = authManager.user;

    document.getElementById('user_id').value = user.id || '';
    document.getElementById('guest_email').value = user.email || '';
    document.getElementById('guest_first_name').value = user.first_name || '';
    document.getElementById('guest_last_name').value = user.last_name || '';
    document.getElementById('guest_phone').value = user.phone || '';
    
    toggleGuestDataFields();
}

document.addEventListener('DOMContentLoaded', () => {
    loadBookings();

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const status = e.target.dataset.status;
            filterByStatus(status, e);
        });
    });

    const modal = document.getElementById('create-booking-modal');
    const openBtn = document.getElementById('create-booking-btn');
    const closeBtn = document.getElementById('close-modal');
    const cancelModalBtn = document.getElementById('cancel-modal-btn');
    const form = document.getElementById('create-booking-form');
    const roomSelect = document.getElementById('room-select');

    const editModal = document.getElementById('edit-booking-modal');
    const editCloseBtn = document.getElementById('edit-close-modal');
    const editCancelBtn = document.getElementById('edit-cancel-modal-btn');
    const editForm = document.getElementById('edit-booking-form');
    const roomSelectEdit = document.getElementById('room-select-edit');

    openBtn.addEventListener('click', async () => {
        modal.style.display = 'flex';
        await loadAvailableRooms();
        autofillGuestData();
    });

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        form.reset();
    });

    cancelModalBtn.addEventListener('click', () => {
        modal.style.display = 'none';
        form.reset();
    });

    globalThis.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            form.reset();
        }
        if (e.target === editModal) {
            editModal.style.display = 'none';
            editForm.reset();
        }
    });

    editCloseBtn.addEventListener('click', () => {
        editModal.style.display = 'none';
        editForm.reset();
    });
    editCancelBtn.addEventListener('click', () => {
        editModal.style.display = 'none';
        editForm.reset();
    });

    async function loadAvailableRooms() {
        try {
            const res = await fetch('/api/v1/rooms/');
            if (!res.ok) throw new Error('Помилка завантаження кімнат');
            const rooms = await res.json();

            roomSelect.innerHTML = `
                <option value="">-- Оберіть номер --</option>
                ${rooms.map(r => `
                    <option value="${r.id}">
                        №${r.room_number} — ${r.room_type} (${r.max_guest} гостей) — ${r.base_price}₴/ніч
                    </option>
                `).join('')}
            `;
        } catch (err) {
            console.error(err);
            roomSelect.innerHTML = `<option>Помилка завантаження</option>`;
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        
        const data = {
            room_id: Number.parseInt(formData.get('room_id')),
            check_in_date: formData.get('check_in_date'),
            check_out_date: formData.get('check_out_date'),
            special_requests: formData.get('special_requests') || null
        };

        const isStaffOrAdmin = authManager.isAuthenticated() && 
            (authManager.user.role === 'ADMIN' || authManager.user.role === 'STAFF');
        
        if (isStaffOrAdmin) {
            data.email = formData.get('email') || null;
            data.first_name = formData.get('first_name') || null;
            data.last_name = formData.get('last_name') || null;
            data.phone = formData.get('phone') || null;
        } else if (authManager.isAuthenticated()) {
            data.user_id = authManager.user.id;
        } else {
            data.email = formData.get('email') || null;
            data.first_name = formData.get('first_name') || null;
            data.last_name = formData.get('last_name') || null;
            data.phone = formData.get('phone') || null;
        }

        try {
            const res = await fetch('/api/v1/bookings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                alert('Бронювання створено успішно!');
                modal.style.display = 'none';
                form.reset();
                loadBookings();
            } else {
                const error = await res.json();
                alert('Помилка створення: ' + (error.message || 'невідома помилка'));
            }
        } catch (err) {
            console.error(err);
            alert('Помилка зʼєднання з сервером');
        }
    });
    
    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(editForm);
        const code = fd.get('booking_code');
        const room_id = Number.parseInt(fd.get('room_id'));
        const check_in_date = fd.get('check_in_date');
        const check_out_date = fd.get('check_out_date');
        const special_requests = fd.get('special_requests') || null;

        if (!room_id || !check_in_date || !check_out_date) {
            alert('Будь ласка, заповніть усі обовʼязкові поля');
            return;
        }
        if (new Date(check_out_date) <= new Date(check_in_date)) {
            alert('Дата виїзду має бути пізніше дати заїзду');
            return;
        }

        try {
            const res = await fetch(`/api/v1/bookings/${code}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ room_id, check_in_date, check_out_date, special_requests })
            });
            if (res.ok) {
                alert('Зміни збережено');
                editModal.style.display = 'none';
                editForm.reset();
                loadBookings();
            } else {
                if (res.status === 409) {
                    alert('Обрані дати недоступні для цього номеру. Оберіть інший період або номер.');
                } else {
                    const err = await res.json().catch(() => ({}));
                    alert('Помилка оновлення: ' + (err.message || 'невідома помилка'));
                }
            }
        } catch (err) {
            console.error(err);
            alert('Помилка зʼєднання з сервером');
        }
    });
});

globalThis.cancelBooking = cancelBooking;
globalThis.viewBookingDetails = viewBookingDetails;
globalThis.openEditBooking = function(booking) {
    const editModal = document.getElementById('edit-booking-modal');
    const editForm = document.getElementById('edit-booking-form');
    const roomSelectEdit = document.getElementById('room-select-edit');
    const inInput = document.getElementById('edit-check-in');
    const outInput = document.getElementById('edit-check-out');
    const reqTextarea = document.getElementById('edit-special-requests');

    editForm.reset();
    document.getElementById('edit_booking_code').value = booking.booking_code;
    inInput.value = (booking.check_in_date || '').slice(0,10);
    outInput.value = (booking.check_out_date || '').slice(0,10);
    reqTextarea.value = booking.special_requests || '';

    (async () => {
        await (async function(target){
            try {
                const res = await fetch('/api/v1/rooms/');
                if (!res.ok) throw new Error('Помилка завантаження кімнат');
                const rooms = await res.json();
                target.innerHTML = `
                    <option value="">-- Оберіть номер --</option>
                    ${rooms.map(r => `
                        <option value="${r.id}">№${r.room_number} — ${r.room_type} (${r.max_guest} гостей) — ${r.base_price}₴/ніч</option>
                    `).join('')}
                `;
                target.value = booking.room_id;
            } catch (e) {
                console.error(e);
                target.innerHTML = `<option>Помилка завантаження</option>`;
            }
        })(roomSelectEdit);
        editModal.style.display = 'flex';
    })();
};

function filterByStatus(status, e) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');
    bookingsState.status = status;
    bookingsState.page = 1;
    applyFiltersAndRender();
}