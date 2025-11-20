// Створення нового відгуку
document.addEventListener('DOMContentLoaded', () => {
    // Перевірка авторизації
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('Для створення відгуку необхідно увійти в систему');
        window.location.href = '/login';
        return;
    }
    
    loadRooms();
    setupStarRating();
    setupCharCounter();
    setupForm();
});

async function loadRooms() {
    try {
        const response = await fetch('/api/v1/rooms/');
        if (response.ok) {
            const rooms = await response.json();
            console.log('Loaded rooms:', rooms);
            const select = document.getElementById('room-select');
            
            if (!select) {
                console.error('Select element not found!');
                return;
            }
            
            rooms.forEach(room => {
                const option = document.createElement('option');
                option.value = room.id; // API повертає поле 'id', а не 'room_id'
                option.textContent = `Номер ${room.room_number} - ${room.room_type}`;
                select.appendChild(option);
            });
            
            console.log('Total options in select:', select.options.length);
            
            // Додаємо обробник зміни для діагностики
            select.addEventListener('change', (e) => {
                console.log('Room selected:', e.target.value);
            });
        } else {
            console.error('Failed to load rooms:', response.status);
        }
    } catch (error) {
        console.error('Помилка завантаження номерів:', error);
    }
}

function setupStarRating() {
    const stars = document.querySelectorAll('#star-rating .star');
    const ratingInput = document.getElementById('rating');
    const ratingText = document.getElementById('rating-text');
    
    const ratingLabels = {
        1: 'Погано',
        2: 'Незадовільно',
        3: 'Задовільно',
        4: 'Добре',
        5: 'Відмінно'
    };
    
    stars.forEach(star => {
        star.addEventListener('click', () => {
            const rating = parseInt(star.dataset.rating);
            ratingInput.value = rating;
            ratingText.textContent = ratingLabels[rating];
            
            stars.forEach((s, index) => {
                if (index < rating) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });
        });
        
        star.addEventListener('mouseenter', () => {
            const rating = parseInt(star.dataset.rating);
            stars.forEach((s, index) => {
                if (index < rating) {
                    s.classList.add('hover');
                } else {
                    s.classList.remove('hover');
                }
            });
        });
    });
    
    const container = document.getElementById('star-rating');
    container.addEventListener('mouseleave', () => {
        stars.forEach(s => s.classList.remove('hover'));
    });
}

function setupCharCounter() {
    const commentInput = document.getElementById('comment');
    const charCount = document.getElementById('char-count');
    
    commentInput.addEventListener('input', () => {
        const count = commentInput.value.length;
        charCount.textContent = count;
        
        if (count > 900) {
            charCount.style.color = 'var(--gold)';
        } else {
            charCount.style.color = '';
        }
    });
}

function setupForm() {
    const form = document.getElementById('create-review-form');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Отримуємо дані безпосередньо з елементів
        const roomSelect = document.getElementById('room-select');
        const roomId = roomSelect ? roomSelect.value : null;
        const rating = document.getElementById('rating').value;
        const comment = document.getElementById('comment').value.trim();
        
        console.log('Form data - room_id:', roomId, 'rating:', rating);
        console.log('Room select element:', roomSelect);
        console.log('Room select value:', roomSelect?.value);
        console.log('Room select selectedIndex:', roomSelect?.selectedIndex);
        
        await createReview(roomId, rating, comment);
    });
}

async function createReview(roomId, rating, comment) {
    rating = parseInt(rating);
    
    console.log('Room ID from select:', roomId);
    
    if (!roomId || roomId === '') {
        alert('Будь ласка, оберіть номер');
        return;
    }
    
    if (!rating) {
        alert('Будь ласка, оберіть рейтинг');
        return;
    }
    
    const token = localStorage.getItem('access_token');
    if (!token) {
        alert('Необхідна авторизація');
        window.location.href = '/login';
        return;
    }
    
    const parsedRoomId = parseInt(roomId, 10);
    if (isNaN(parsedRoomId)) {
        alert('Невірний ID номера');
        return;
    }
    
    const reviewData = {
        room_id: parsedRoomId,
        rating: rating
    };
    
    if (comment) {
        reviewData.comment = comment;
    }
    
    console.log('Sending review data:', reviewData);
    
    try {
        const response = await fetch('/api/v1/reviews/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(reviewData)
        });
        
        if (response.ok) {
            alert('Дякуємо за ваш відгук!');
            window.location.href = '/reviews';
        } else {
            const error = await response.json();
            console.error('Server error:', error);
            console.error('Status:', response.status);
            
            if (response.status === 422) {
                // Validation error
                const errorMsg = error.errors ? JSON.stringify(error.errors) : error.message;
                alert('Помилка валідації: ' + errorMsg);
            } else if (response.status === 400 && error.message && error.message.includes('вже залишили відгук')) {
                alert(error.message);
                window.location.href = '/reviews';
            } else {
                alert(error.message || 'Помилка створення відгуку');
            }
        }
    } catch (error) {
        console.error('Помилка:', error);
        alert('Не вдалося створити відгук. Спробуйте пізніше.');
    }
}
