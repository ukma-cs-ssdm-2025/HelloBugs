document.addEventListener('DOMContentLoaded', function() {
    if (!window.authManager || !authManager.isAuthenticated()) {
        window.location.href = '/login';
        return;
    }

    loadProfile();

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
    try {
        const response = await authManager.makeAuthenticatedRequest('/api/v1/auth/me');
        const user = await response.json();

        updateProfileUI(user);
    } catch (error) {
        console.error('Помилка завантаження профілю:', error);
        window.location.href = '/login';
    }
}

function updateProfileUI(user) {
    const avatar = document.querySelector('.profile-avatar span');
    if (avatar && user.first_name && user.last_name) {
        avatar.textContent = user.first_name[0] + user.last_name[0];
    }

    const nameElement = document.querySelector('.profile-header h2');
    if (nameElement) nameElement.textContent = `${user.first_name} ${user.last_name}`;

    const roleElement = document.querySelector('.role-badge');
    if (roleElement && user.role) {
        const roleValue = typeof user.role === 'string' ? user.role : user.role.value;
        roleElement.textContent = roleValue;

        const adminLink = document.getElementById('adminLink');
        if (adminLink) {
            if (roleValue === 'ADMIN') {
                adminLink.style.display = 'inline-flex';
            } else {
                adminLink.style.display = 'none';
            }
        }
    }

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

    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
        const response = await authManager.makeAuthenticatedRequest('/api/v1/users/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const updatedUser = await response.json();
        localStorage.setItem('user', JSON.stringify(updatedUser));

        showAlert('Успішно!', 'Дані профілю оновлено', 'success');
        updateProfileUI(updatedUser);

        if (window.authManager) {
            window.authManager.user = updatedUser;
            window.authManager.updateNavigation();
        }
    } catch (error) {
        showAlert('Помилка', error.message, 'error');
    }
}

async function handlePasswordUpdate(e) {
    e.preventDefault();

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
        await authManager.makeAuthenticatedRequest('/api/v1/users/password', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: data.current_password,
                new_password: data.new_password
            })
        });

        showAlert('Успішно!', 'Пароль успішно змінено', 'success');
        e.target.reset();
    } catch (error) {
        showAlert('Помилка', error.message, 'error');
    }
}

function showAlert(title, message, type) {
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

    setTimeout(() => {
        alertDiv.style.opacity = '0';
        alertDiv.style.transition = 'opacity 0.5s';
        setTimeout(() => alertDiv.remove(), 500);
    }, 3000);
}
