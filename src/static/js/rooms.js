
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


    fetch('/api/v1/rooms/')
        .then(res => res.json())
        .then(data => {
            allRooms = data;
            displayRooms(allRooms);
        })
        .catch(err => {
            roomsContainer.innerHTML = '<p class="error-message">Помилка завантаження номерів. Спробуйте пізніше.</p>';
            console.error(err);
        });
});

function displayRooms(rooms) {
    const roomsContainer = document.getElementById('rooms-container');
    roomsContainer.innerHTML = '';
    
    if (rooms.length === 0) {
        roomsContainer.innerHTML = '<p class="no-results">Немає номерів за обраними параметрами.</p>';
        return;
    }
    
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
                    <button class="btn btn-primary" onclick="bookRoom(${room.id})" ${room.status !== 'AVAILABLE' ? 'disabled' : ''}>
                        ${room.status === 'AVAILABLE' ? 'Забронювати' : 'Недоступний'}
                    </button>
                </div>
            </div>
        `;
        roomsContainer.appendChild(card);
    });
}

function bookRoom(roomId) {
    localStorage.setItem('selected_room_id', roomId);
    
    window.location.href = `/booking/create?room_id=${roomId}`;
}

function applyFilters() {
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
    
    let filteredRooms = allRooms.filter(room => {
        if (roomType && room.room_type !== roomType) {
            return false;
        }
        
        if (capacity && room.max_guest < parseInt(capacity)) {
            return false;
        }
        
        if (priceRange) {
            const price = parseFloat(room.base_price);
            if (priceRange.includes('+')) {
                const minPrice = parseInt(priceRange);
                if (price < minPrice) return false;
            } else {
                const [minPrice, maxPrice] = priceRange.split('-').map(Number);
                if (price < minPrice || price > maxPrice) return false;
            }
        }
        
        if (checkin && checkout && room.status !== 'AVAILABLE') {
            return false;
        }
        
        return true;
    });
    
    
    if (sortBy) {
        filteredRooms = sortRooms(filteredRooms, sortBy);
    }
        
    displayRooms(filteredRooms);
    
    showFilterResults(filteredRooms.length, allRooms.length);
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
    
   
    displayRooms(allRooms);
}


window.bookRoom = bookRoom;
window.applyFilters = applyFilters;
window.resetFilters = resetFilters;