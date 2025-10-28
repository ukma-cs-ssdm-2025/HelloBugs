function loadRoomInfo() {
    const urlParams = new URLSearchParams(window.location.search);
    const roomId = urlParams.get('room_id');

    if (!roomId) {
        const savedRoomId = localStorage.getItem('selected_room_id');
        if (savedRoomId) {
            fetchRoomDetails(savedRoomId);
        } else {
            showNoRoomSelected();
        }
    } else {
        fetchRoomDetails(roomId);
    }
}

async function fetchRoomDetails(roomId) {
    try {
        const response = await fetch(`/api/v1/rooms/${roomId}`);
        if (!response.ok) throw new Error('Room not found');

        const room = await response.json();
        displayRoomInfo(room);
        document.getElementById('room_id').value = room.id;
        localStorage.setItem('selected_room_id', room.id); 
    } catch (error) {
        console.error('Error loading room:', error);
        showNoRoomSelected();
    }
}

function displayRoomInfo(room) {
    const roomDisplay = document.getElementById('selected-room-display');
    const roomInfo = document.getElementById('room-info');

    roomDisplay.textContent = `Номер ${room.room_number} - ${room.room_type}`;
    roomDisplay.classList.add('selected');

    roomInfo.innerHTML = `
        <div class="room-detail"><strong>Номер:</strong> ${room.room_number}</div>
        <div class="room-detail"><strong>Тип:</strong> ${room.room_type}</div>
        <div class="room-detail"><strong>Ціна:</strong> ${room.base_price} грн/ніч</div>
        <div class="room-detail"><strong>Макс. гостей:</strong> ${room.max_guest}</div>
        <div class="room-detail"><strong>Поверх:</strong> ${room.floor}</div>
        <div class="room-detail"><strong>Площа:</strong> ${room.size_sqm} м²</div>
    `;
}

function showNoRoomSelected() {
    const roomInfo = document.getElementById('room-info');
    roomInfo.innerHTML = `
        <p style="color: var(--gray); text-align: center; padding: 20px;">
            Номер не обрано
        </p>
    `;
}

function autofillGuestData() {
    if (window.authManager && authManager.isAuthenticated()) {
        const user = authManager.user;
        document.getElementById('user_id').value = user.id || '';
        document.getElementById('guest_email').value = user.email || '';
        document.getElementById('guest_first_name').value = user.first_name || '';
        document.getElementById('guest_last_name').value = user.last_name || '';
        document.getElementById('guest_phone').value = user.phone || '';
    } else {
        const userId = localStorage.getItem('user_id');
        if (!userId) return;

        document.getElementById('user_id').value = userId;
        const email = localStorage.getItem('user_email');
        const firstName = localStorage.getItem('user_first_name');
        const lastName = localStorage.getItem('user_last_name');
        const phone = localStorage.getItem('user_phone');

        if (email) document.getElementById('guest_email').value = email;
        if (firstName) document.getElementById('guest_first_name').value = firstName;
        if (lastName) document.getElementById('guest_last_name').value = lastName;
        if (phone) document.getElementById('guest_phone').value = phone;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadRoomInfo();
    autofillGuestData();

    const form = document.getElementById('create-booking-form');
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

        if (window.authManager && authManager.isAuthenticated()) {
            data.user_id = authManager.user.id;
        } else {
            const userId = localStorage.getItem('user_id');
            if (userId) data.user_id = parseInt(userId);
        }

        try {
            const res = await fetch('/api/v1/bookings/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                alert('Бронювання створено успішно!');
                form.reset();
                window.location.href = '/bookings';
            } else {
                const error = await res.json();
                alert('Помилка створення: ' + (error.message || 'невідома помилка'));
            }
        } catch (err) {
            console.error(err);
            alert('Помилка зʼєднання з сервером');
        }
    });
});
