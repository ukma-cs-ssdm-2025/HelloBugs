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
            Номер не обрано. <br><br>
            <a href="/rooms" class="btn btn-small btn-primary">Обрати номер</a>
        </p>
    `;
}

function setMinDates() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('check_in_date').min = today;
    document.getElementById('check_out_date').min = today;
}

function calculateNights() {
    const checkIn = document.getElementById('check_in_date').value;
    const checkOut = document.getElementById('check_out_date').value;
    
    if (checkIn && checkOut) {
        const start = new Date(checkIn);
        const end = new Date(checkOut);
        const nights = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        
        document.getElementById('nights-count').textContent = nights > 0 ? nights : '0';
    }
}

function validateDates(checkIn, checkOut) {
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (start < today) {
        alert('Дата заїзду не може бути в минулому');
        return false;
    }
    
    if (end <= start) {
        alert('Дата виїзду має бути пізніше дати заїзду');
        return false;
    }
    
    return true;
}

async function createBooking(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const data = {
        room_id: parseInt(formData.get('room_id')),
        check_in_date: formData.get('check_in_date'),
        check_out_date: formData.get('check_out_date'),
        special_requests: formData.get('special_requests') || null
    };
    
    const userId = localStorage.getItem('user_id');
    if (userId) {
        data.user_id = parseInt(userId);
    }
    
    if (!data.room_id) {
        alert('Оберіть номер для бронювання');
        return;
    }
    
    if (!validateDates(data.check_in_date, data.check_out_date)) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/bookings/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const booking = await response.json();
            alert(`Бронювання успішно створено!\nКод бронювання: ${booking.booking_code}`);
            
            localStorage.removeItem('selected_room_id');
            
            window.location.href = '/booking';
        } else {
            const error = await response.json();
            alert('Помилка створення бронювання:\n' + (error.message || 'Невідома помилка'));
        }
    } catch (error) {
        console.error('Error creating booking:', error);
        alert('Помилка з\'єднання з сервером');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setMinDates();
    loadRoomInfo();
    
    document.getElementById('check_in_date').addEventListener('change', function() {
        const checkIn = this.value;
        document.getElementById('check_out_date').min = checkIn;
        calculateNights();
    });
    
    document.getElementById('check_out_date').addEventListener('change', calculateNights);
    
    document.getElementById('create-booking-form').addEventListener('submit', createBooking);
});

