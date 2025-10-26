document.addEventListener('DOMContentLoaded', () => {
    // Отримуємо код бронювання з URL
    const urlParams = new URLSearchParams(window.location.search);
    const bookingCode = urlParams.get('code');
    
    if (!bookingCode) {
        showError('Код бронювання не вказано');
        return;
    }
    
    loadBookingDetails(bookingCode);
});

async function loadBookingDetails(bookingCode) {
    try {
        const response = await fetch(`/api/v1/bookings/${bookingCode}`);
        
        if (!response.ok) {
            if (response.status === 404) {
                throw new Error('Бронювання не знайдено');
            }
            throw new Error('Помилка завантаження деталей бронювання');
        }
        
        const booking = await response.json();
        displayBookingDetails(booking);
        
        // Завантажуємо інформацію про номер
        loadRoomDetails(booking.room_id);
        
    } catch (error) {
        console.error('Error loading booking:', error);
        showError(error.message);
    }
}

async function loadRoomDetails(roomId) {
    try {
        const response = await fetch(`/api/v1/rooms/${roomId}`);
        
        if (response.ok) {
            const room = await response.json();
            document.getElementById('room-number').textContent = room.room_number || '-';
            document.getElementById('room-type').textContent = getRoomTypeName(room.room_type);
            document.getElementById('room-price').textContent = `${room.base_price} грн`;
        }
    } catch (error) {
        console.error('Error loading room details:', error);
    }
}

function displayBookingDetails(booking) {
    // Приховуємо loading
    document.getElementById('loading').style.display = 'none';
    document.getElementById('booking-content').style.display = 'block';
    
    // Код бронювання
    document.getElementById('booking-code').textContent = booking.booking_code;
    
    // Статус
    const statusBadge = document.getElementById('status-badge');
    const statusText = getStatusText(booking.status);
    statusBadge.textContent = statusText;
    statusBadge.className = `status-badge ${booking.status.toLowerCase()}`;
    
    // Інформація про гостя
    document.getElementById('guest-name').textContent = 
        `${booking.first_name} ${booking.last_name}`;
    document.getElementById('guest-email').textContent = booking.email;
    document.getElementById('guest-phone').textContent = booking.phone;
    
    // Дати
    const checkIn = new Date(booking.check_in_date);
    const checkOut = new Date(booking.check_out_date);
    const nights = Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24));
    
    document.getElementById('check-in-date').textContent = formatDate(checkIn);
    document.getElementById('check-out-date').textContent = formatDate(checkOut);
    document.getElementById('nights-count').textContent = `${nights} ${getNightsText(nights)}`;
    
    // Додаткова інформація
    document.getElementById('created-at').textContent = formatDateTime(booking.created_at);
    document.getElementById('updated-at').textContent = formatDateTime(booking.updated_at);
    
    // Особливі побажання
    if (booking.special_requests) {
        document.getElementById('special-requests-row').style.display = 'flex';
        document.getElementById('special-requests').textContent = booking.special_requests;
    }
    
    // Кнопка скасування (тільки для активних бронювань)
    if (booking.status === 'ACTIVE') {
        const cancelBtn = document.getElementById('cancel-booking-btn');
        cancelBtn.style.display = 'inline-flex';
        cancelBtn.onclick = () => cancelBooking(booking.booking_code);
    }
}

function getRoomTypeName(type) {
    const types = {
        'ECONOMY': 'Економ',
        'STANDARD': 'Стандарт',
        'DELUXE': 'Делюкс'
    };
    return types[type] || type;
}

function getStatusText(status) {
    const statuses = {
        'ACTIVE': 'Активне',
        'COMPLETED': 'Завершене',
        'CANCELLED': 'Скасоване'
    };
    return statuses[status] || status;
}

function formatDate(date) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        weekday: 'long'
    };
    return date.toLocaleDateString('uk-UA', options);
}

function formatDateTime(dateTimeStr) {
    const date = new Date(dateTimeStr);
    const dateOptions = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric'
    };
    const timeOptions = {
        hour: '2-digit',
        minute: '2-digit'
    };
    return `${date.toLocaleDateString('uk-UA', dateOptions)} о ${date.toLocaleTimeString('uk-UA', timeOptions)}`;
}

function getNightsText(nights) {
    if (nights === 1) return 'ніч';
    if (nights >= 2 && nights <= 4) return 'ночі';
    return 'ночей';
}

async function cancelBooking(bookingCode) {
    if (!confirm('Ви впевнені, що хочете скасувати це бронювання?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/bookings/${bookingCode}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert('Бронювання успішно скасовано');
            // Перезавантажуємо сторінку
            location.reload();
        } else {
            throw new Error('Помилка скасування бронювання');
        }
    } catch (error) {
        console.error('Error cancelling booking:', error);
        alert('Помилка: ' + error.message);
    }
}

function showError(message) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error-message').style.display = 'block';
    document.getElementById('error-text').textContent = message;
}
