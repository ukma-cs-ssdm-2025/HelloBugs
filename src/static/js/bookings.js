async function loadBookings(filterStatus = 'all') {
    const container = document.getElementById('bookings-container');
    const emptyState = document.getElementById('empty-state');
    const bookingsSection = document.querySelector('.bookings-section'); // Додайте цей селектор

    if (!authManager.isAuthenticated()) {
    container.innerHTML = `
        <div style="text-align: center; padding: 40px 20px; color: #666;">
            <h2>Увійдіть для перегляду та редагування деталей бронювань<\h2>
        </div>
    `;
    return;
    }

    if (bookingsSection) {
        bookingsSection.style.display = 'block';
    }

    try {
        const response = await fetch('/api/v1/bookings/');
        if (!response.ok) throw new Error('Помилка завантаження');

        let bookings = await response.json();

        const isStaffOrAdmin = authManager.user.role === 'ADMIN' || authManager.user.role === 'STAFF';

        if (!isStaffOrAdmin) {
            bookings = bookings.filter(b => b.user_id === authManager.user.id);
        }

        if (filterStatus !== 'all') {
            bookings = bookings.filter(b => b.status === filterStatus);
        }

        if (bookings.length === 0) {
            container.innerHTML = '';
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
            return;
        }

        emptyState.style.display = 'none';
        container.innerHTML = bookings.map(booking => createBookingCard(booking)).join('');
    } catch (error) {
        console.error('Error loading bookings:', error);
        container.innerHTML = '<p class="error-message">Помилка завантаження бронювань. Спробуйте пізніше.</p>';
    }
}

function createBookingCard(booking) {
    const checkIn = new Date(booking.check_in_date).toLocaleDateString('uk-UA');
    const checkOut = new Date(booking.check_out_date).toLocaleDateString('uk-UA');
    const created = new Date(booking.created_at).toLocaleDateString('uk-UA');

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
                        Створено: ${created}
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
    window.location.href = `/booking/details?code=${bookingCode}`;
}

function autofillGuestData() {
    if (!authManager.isAuthenticated()) return;

    const user = authManager.user;

    document.getElementById('user_id').value = user.id || '';
    document.getElementById('guest_email').value = user.email || '';
    document.getElementById('guest_first_name').value = user.first_name || '';
    document.getElementById('guest_last_name').value = user.last_name || '';
    document.getElementById('guest_phone').value = user.phone || '';
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

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            form.reset();
        }
        if (e.target === editModal) {
            editModal.style.display = 'none';
            editForm.reset();
        }
    });

    // Обробники для модалки редагування: закрити/скасувати
    editCloseBtn.addEventListener('click', () => {
        editModal.style.display = 'none';
        editForm.reset();
    });
    editCancelBtn.addEventListener('click', () => {
        editModal.style.display = 'none';
        editForm.reset();
    });

    // Edit modal: close/cancel
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
            room_id: parseInt(formData.get('room_id')),
            check_in_date: formData.get('check_in_date'),
            check_out_date: formData.get('check_out_date'),
            special_requests: formData.get('special_requests') || null,
            email: formData.get('email') || null,
            first_name: formData.get('first_name') || null,
            last_name: formData.get('last_name') || null,
            phone: formData.get('phone') || null
        };

        if (authManager.isAuthenticated()) {
            data.user_id = authManager.user.id;
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
    
    // Submit edit form -> PATCH booking
    editForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(editForm);
        const code = fd.get('booking_code');
        const room_id = parseInt(fd.get('room_id'));
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
                const err = await res.json().catch(() => ({}));
                alert('Помилка оновлення: ' + (err.message || 'невідома помилка'));
            }
        } catch (err) {
            console.error(err);
            alert('Помилка зʼєднання з сервером');
        }
    });
});

window.cancelBooking = cancelBooking;
window.viewBookingDetails = viewBookingDetails;
window.openEditBooking = function(booking) {
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
    loadBookings(status);
}