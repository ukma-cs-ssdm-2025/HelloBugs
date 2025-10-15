// Profile page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Перевіряємо, чи користувач авторизований
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        // Якщо токена немає, перенаправляємо на сторінку входу
        window.location.href = '/login';
        return;
    }
    
    // Завантажуємо дані профілю
    loadProfile();
    
    // Обробники форм
    const profileForm = document.getElementById('profileForm');
    const passwordForm = document.getElementById('passwordForm');
    
    if (profileForm) {
        profileForm.addEventListener('submit', handleProfileUpdate);
    }
    
    if (passwordForm) {
        passwordForm.addEventListener('submit', handlePasswordUpdate);
    }
});

async function loadProfile() {
    const token = localStorage.getItem('authToken');
    
    try {
        const response = await fetch('/api/v1/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Не вдалося завантажити профіль');
        }
        
        const user = await response.json();
        
        // Оновлюємо дані на сторінці
        updateProfileUI(user);
        
    } catch (error) {
        console.error('Помилка завантаження профілю:', error);
        // Перенаправляємо на сторінку входу
        window.location.href = '/login';
    }
}

function updateProfileUI(user) {
    // Оновлюємо аватар
    const avatar = document.querySelector('.profile-avatar span');
    if (avatar && user.first_name && user.last_name) {
        avatar.textContent = user.first_name[0] + user.last_name[0];
    }
    
    // Оновлюємо ім'я
    const nameElement = document.querySelector('.profile-header h2');
    if (nameElement) {
        nameElement.textContent = `${user.first_name} ${user.last_name}`;
    }
    
    // Оновлюємо роль
    const roleElement = document.querySelector('.role-badge');
    if (roleElement && user.role) {
        const roleValue = user.role.value || user.role;
        roleElement.textContent = roleValue;
        
        // Показуємо посилання на адмін-панель для адміністраторів
        const adminLink = document.getElementById('adminLink');
        if (adminLink && roleValue === 'ADMIN') {
            adminLink.style.display = 'inline-flex';
        }
    }
    
    // Заповнюємо форму
    const firstNameInput = document.querySelector('input[name="first_name"]');
    const lastNameInput = document.querySelector('input[name="last_name"]');
    const emailInput = document.querySelector('input[name="email"]');
    const phoneInput = document.querySelector('input[name="phone"]');
    
    if (firstNameInput) firstNameInput.value = user.first_name || '';
    if (lastNameInput) lastNameInput.value = user.last_name || '';
    if (emailInput) emailInput.value = user.email || '';
    if (phoneInput) phoneInput.value = user.phone || '';
}

async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const token = localStorage.getItem('authToken');
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch('/api/v1/users/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            const updatedUser = await response.json();
            
            // Оновлюємо дані користувача в localStorage
            const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
            const newUser = { ...currentUser, ...updatedUser };
            localStorage.setItem('user', JSON.stringify(newUser));
            
            showAlert('Успішно!', 'Дані профілю оновлено', 'success');
            
            // Оновлюємо UI
            updateProfileUI(newUser);
            
            // Оновлюємо навігацію
            if (window.authManager) {
                window.authManager.user = newUser;
                window.authManager.updateNavigation();
            }
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Помилка оновлення профілю');
        }
    } catch (error) {
        showAlert('Помилка', error.message, 'error');
    }
}

async function handlePasswordUpdate(e) {
    e.preventDefault();
    
    const token = localStorage.getItem('authToken');
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    if (data.new_password !== data.confirm_password) {
        showAlert('Помилка', 'Паролі не співпадають', 'error');
        return;
    }
    
    if (data.new_password.length < 8) {
        showAlert('Помилка', 'Пароль має містити мінімум 8 символів', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/users/password', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                current_password: data.current_password,
                new_password: data.new_password
            })
        });
        
        if (response.ok) {
            showAlert('Успішно!', 'Пароль успішно змінено', 'success');
            e.target.reset();
        } else {
            const error = await response.json();
            throw new Error(error.message || 'Помилка зміни пароля');
        }
    } catch (error) {
        showAlert('Помилка', error.message, 'error');
    }
}

function showAlert(title, message, type) {
    // Створюємо простий алерт
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${type === 'success' ? '#d4edda' : '#f8d7da'};
        color: ${type === 'success' ? '#155724' : '#721c24'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'};
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 10000;
        max-width: 300px;
    `;
    alertDiv.innerHTML = `<strong>${title}</strong><br>${message}`;
    
    document.body.appendChild(alertDiv);
    
    // Видаляємо через 3 секунди
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transition = 'opacity 0.5s';
        setTimeout(() => alertDiv.remove(), 500);
    }, 3000);
}
