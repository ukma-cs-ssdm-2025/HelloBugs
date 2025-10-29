let allRooms = [];

document.addEventListener('DOMContentLoaded', () => {
    const roomsContainer = document.getElementById('rooms-container');
    
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('filter-checkin').min = today;
    document.getElementById('filter-checkout').min = today;
    
    document.getElementById('filter-checkin').addEventListener('change', (e) => {
        const checkinDate = e.target.value;
        document.getElementById('filter-checkout').min = checkinDate;
    });

    loadRooms();
    
    document.getElementById('roomForm').addEventListener('submit', handleRoomFormSubmit);
});

async function loadRooms(params = {}) {
    const roomsContainer = document.getElementById('rooms-container');
    
    try {
        const url = new URL('/api/v1/rooms/', window.location.origin);
        Object.entries(params).forEach(([k, v]) => {
            if (v !== undefined && v !== null && v !== '') {
                url.searchParams.set(k, v);
            }
        });
        const res = await fetch(url.toString());
        const data = await res.json();
        allRooms = data;
        displayRooms(allRooms);
    } catch (err) {
        roomsContainer.innerHTML = '<p class="error-message">Помилка завантаження номерів. Спробуйте пізніше.</p>';
        console.error(err);
    }
}

function displayRooms(rooms) {
    const roomsContainer = document.getElementById('rooms-container');
    roomsContainer.innerHTML = '';
    
    if (rooms.length === 0) {
        roomsContainer.innerHTML = '<p class="no-results">Немає номерів за обраними параметрами.</p>';
        return;
    }
    
    const isStaffOrAdmin = authManager.isAuthenticated() && 
        (authManager.user.role === 'ADMIN' || authManager.user.role === 'STAFF');

    const isGuest = !authManager.isAuthenticated() || authManager.user.role === 'GUEST';
    
    rooms.forEach(room => {
        const card = document.createElement('div');
        card.classList.add('room-card');
        card.dataset.roomType = room.room_type;
        card.dataset.maxGuest = room.max_guest;
        card.dataset.price = room.base_price;
        card.dataset.status = room.status;

        const roomTypeNames = {
            'ECONOMY': 'Економ',
            'STANDARD': 'Стандарт',
            'DELUXE': 'Делюкс'
        };
        
        const statusBadge = room.status === 'AVAILABLE' 
            ? '<span class="status-badge available">Доступний</span>'
            : '<span class="status-badge occupied">Зайнятий</span>';

        const adminButtons = isStaffOrAdmin ? `
            <div class="admin-actions" style="margin-top: 20px; display: flex; gap: 10px; justify-content: center;">
                <button class="btn btn-edit btn-lg" onclick="editRoom(${room.id})">Редагувати</button>
                <button class="btn btn-delete btn-lg" onclick="deleteRoom(${room.id})">Видалити</button>
             </div>
        ` : '';

        const bookingButton = isGuest
            ? `<button class="btn btn-primary" onclick="bookRoom(${room.id})" ${room.status !== 'AVAILABLE' ? 'disabled' : ''}>
                   ${room.status === 'AVAILABLE' ? 'Забронювати' : 'Недоступний'}
               </button>`
            : '';

        card.innerHTML = `
            <div class="room-image">
                <img src="${room.main_photo_url}" alt="Номер ${room.room_number}" onerror="this.src='https://via.placeholder.com/400x300?text=Номер+${room.room_number}'">
                ${statusBadge}
            </div>
            <div class="room-info">
                <h3>Номер ${room.room_number}</h3>
                <p class="room-type">${roomTypeNames[room.room_type] || room.room_type}</p>
                <p class="room-description">${room.description}</p>
                <div class="room-details">
                    <div class="detail-item">
                        <i class="icon-users"></i>
                        <span>До ${room.max_guest} гостей</span>
                    </div>
                    <div class="detail-item">
                        <i class="icon-size"></i>
                        <span>${room.size_sqm} м²</span>
                    </div>
                    <div class="detail-item">
                        <i class="icon-floor"></i>
                        <span>${room.floor} поверх</span>
                    </div>
                </div>
                <div class="room-footer">
                    <div class="price-info">
                        <span class="price-label">Від</span>
                        <span class="price">${room.base_price} грн</span>
                        <span class="price-period">/ніч</span>
                    </div>
                    ${bookingButton}
                </div>
                ${adminButtons}
            </div>
        `;
        roomsContainer.appendChild(card);
    });
}

function bookRoom(roomId) {
    localStorage.setItem('selected_room_id', roomId);
    window.location.href = `/booking/create?room_id=${roomId}`;
}

function openAddRoomModal() {
    document.getElementById('modalTitle').textContent = 'Додати новий номер';
    document.getElementById('roomForm').reset();
    document.getElementById('roomId').value = '';
    document.getElementById('roomModal').style.display = 'block';
}

function closeRoomModal() {
    document.getElementById('roomModal').style.display = 'none';
}

async function editRoom(roomId) {
    try {
        const res = await authManager.makeAuthenticatedRequest(`/api/v1/rooms/${roomId}`);
        const room = await res.json();
        
        document.getElementById('modalTitle').textContent = 'Редагувати номер';
        document.getElementById('roomId').value = room.id;
        document.getElementById('roomNumber').value = room.room_number;
        document.getElementById('roomType').value = room.room_type;
        document.getElementById('maxGuest').value = room.max_guest;
        document.getElementById('basePrice').value = room.base_price;
        document.getElementById('roomStatus').value = room.status;
        document.getElementById('floor').value = room.floor;
        document.getElementById('sizeSqm').value = room.size_sqm || '';
        document.getElementById('description').value = room.description || '';
        document.getElementById('mainPhotoUrl').value = room.main_photo_url || '';
        
        document.getElementById('roomModal').style.display = 'block';
    } catch (err) {
        alert('Помилка завантаження даних номера');
        console.error(err);
    }
}

async function deleteRoom(roomId) {
    if (!confirm('Ви впевнені, що хочете видалити цей номер?')) {
        return;
    }
    
    try {
        const res = await authManager.makeAuthenticatedRequest(`/api/v1/rooms/${roomId}`, {
            method: 'DELETE'
        });
        
        if (res.ok || res.status === 204) {
            alert('Номер успішно видалено!');
            await loadRooms();
        } else {
            const data = await res.json();
            alert(data.message || 'Помилка видалення номера');
        }
    } catch (err) {
        alert('Помилка видалення номера');
        console.error(err);
    }
}

async function handleRoomFormSubmit(e) {
    e.preventDefault();
    
    const roomId = document.getElementById('roomId').value;
    
    const basePrice = document.getElementById('basePrice').value;
    const sizeSqm = document.getElementById('sizeSqm').value;
    
    if (!basePrice || parseFloat(basePrice) <= 0) {
        alert('Будь ласка, вкажіть коректну базову ціну');
        return;
    }
    
    const roomData = {
        room_number: document.getElementById('roomNumber').value.trim(),
        room_type: document.getElementById('roomType').value,
        max_guest: parseInt(document.getElementById('maxGuest').value),
        base_price: basePrice.toString(),
        status: document.getElementById('roomStatus').value,
        floor: parseInt(document.getElementById('floor').value),
        size_sqm: sizeSqm ? sizeSqm.toString() : null,
        description: document.getElementById('description').value.trim(),
        main_photo_url: document.getElementById('mainPhotoUrl').value.trim() || null,
        photo_urls: []
    };
    
    if (!roomData.room_number) {
        alert('Будь ласка, вкажіть номер кімнати');
        return;
    }
    
    if (!roomData.description || roomData.description.length < 10) {
        alert('Будь ласка, вкажіть опис (мінімум 10 символів)');
        return;
    }
    
    console.log('Відправка даних:', roomData); 
    
    try {
        let res;
        if (roomId) {
            res = await authManager.makeAuthenticatedRequest(`/api/v1/rooms/${roomId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(roomData)
            });
        } else {
            res = await authManager.makeAuthenticatedRequest('/api/v1/rooms/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(roomData)
            });
        }
        
        if (res.ok) {
            alert(roomId ? 'Номер успішно оновлено!' : 'Номер успішно створено!');
            closeRoomModal();
            await loadRooms();
        } else {
            const errorData = await res.json();
            console.error('Помилка від сервера:', errorData);
            
            if (errorData.errors) {
                const errorMessages = Object.entries(errorData.errors)
                    .map(([field, messages]) => `${field}: ${messages.join(', ')}`)
                    .join('\n');
                alert('Помилки валідації:\n' + errorMessages);
            } else {
                alert(errorData.message || 'Помилка збереження номера');
            }
        }
    } catch (err) {
        console.error('Помилка збереження номера:', err);
        alert('Помилка збереження номера. Перевірте консоль для деталей.');
    }
}

async function applyFilters() {
    const checkin = document.getElementById('filter-checkin').value;
    const checkout = document.getElementById('filter-checkout').value;
    const roomType = document.getElementById('filter-type').value;
    const capacity = document.getElementById('filter-capacity').value;
    const priceRange = document.getElementById('filter-price').value;
    const sortBy = document.getElementById('filter-sort').value;
    
    if (checkin && checkout && new Date(checkin) >= new Date(checkout)) {
        alert('Дата виїзду має бути пізніше дати заїзду!');
        return;
    }
    let min_price;
    let max_price;
    if (priceRange) {
        if (priceRange.includes('+')) {
            min_price = parseInt(priceRange);
        } else {
            const parts = priceRange.split('-').map(Number);
            if (parts.length === 2) {
                min_price = parts[0];
                max_price = parts[1];
            }
        }
    }

    let guests;
    if (capacity) {
        guests = parseInt(capacity);
    }

    const params = {
        check_in: checkin || undefined,
        check_out: checkout || undefined,
        room_type: roomType || undefined,
        min_price: min_price !== undefined ? min_price : undefined,
        max_price: max_price !== undefined ? max_price : undefined,
        guests: guests !== undefined ? guests : undefined,
    };

    await loadRooms(params);

    let result = [...allRooms];
    if (sortBy) {
        result = sortRooms(result, sortBy);
    }
    displayRooms(result);
    showFilterResults(result.length, allRooms.length);
}

function sortRooms(rooms, sortBy) {
    const sorted = [...rooms];
    
    switch(sortBy) {
        case 'price-asc':
            return sorted.sort((a, b) => parseFloat(a.base_price) - parseFloat(b.base_price));
        case 'price-desc':
            return sorted.sort((a, b) => parseFloat(b.base_price) - parseFloat(a.base_price));
        case 'capacity-asc':
            return sorted.sort((a, b) => a.max_guest - b.max_guest);
        case 'capacity-desc':
            return sorted.sort((a, b) => b.max_guest - a.max_guest);
        default:
            return sorted;
    }
}

function showFilterResults(filtered, total) {
    const existingMessage = document.querySelector('.filter-results-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    if (filtered < total) {
        const message = document.createElement('div');
        message.className = 'filter-results-message';
        message.innerHTML = `
            <p>Знайдено <strong>${filtered}</strong> з <strong>${total}</strong> номерів</p>
        `;
        message.style.textAlign = 'center';
        message.style.padding = '15px';
        message.style.marginBottom = '20px';
        message.style.backgroundColor = '#f5f5f5';
        message.style.borderRadius = '8px';
        message.style.color = '#2c3e50';
        
        const container = document.getElementById('rooms-container');
        container.parentElement.insertBefore(message, container);
    }
}

function resetFilters() {
    document.getElementById('filter-checkin').value = '';
    document.getElementById('filter-checkout').value = '';
    document.getElementById('filter-type').value = '';
    document.getElementById('filter-capacity').value = '';
    document.getElementById('filter-price').value = '';
    document.getElementById('filter-sort').value = '';
    
    const message = document.querySelector('.filter-results-message');
    if (message) {
        message.remove();
    }
    
    loadRooms();
}

window.bookRoom = bookRoom;
window.applyFilters = applyFilters;
window.resetFilters = resetFilters;
window.openAddRoomModal = openAddRoomModal;
window.closeRoomModal = closeRoomModal;
window.editRoom = editRoom;
window.deleteRoom = deleteRoom;

window.onclick = function(event) {
    const modal = document.getElementById('roomModal');
    if (event.target === modal) {
        closeRoomModal();
    }
}