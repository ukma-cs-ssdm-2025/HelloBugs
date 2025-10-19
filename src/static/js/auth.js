class AuthManager {
    constructor() {
        this.token = this.getCookie('auth_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
        this.init();
    }

    init() {
        this.updateNavigation();
        this.showAdminElements(); 
        if (this.token) this.validateToken();
    }

    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    isAdmin() {
        return this.user && this.user.role === 'ADMIN';
    }

    showAdminElements() {
        const adminElements = document.querySelectorAll('.admin-only');
        if (this.isAdmin()) {
            adminElements.forEach(element => {
                element.style.display = 'block';
            });
        } else {
            adminElements.forEach(element => {
                element.style.display = 'none';
            });
        }
    }

    updateNavigation() {
        const loginBtn = document.querySelector('.login-btn');
        const navList = document.querySelector('.nav-list');

        if (this.isAuthenticated()) {
            if (loginBtn) loginBtn.style.display = 'none';
            this.addUserMenu(navList);
            this.showAdminElements();
        } else {
            if (loginBtn) loginBtn.style.display = 'flex';
            this.removeUserMenu(navList);
            this.showAdminElements(); 
        }
    }

    addUserMenu(navList) {
        this.removeUserMenu(navList);
        if (!navList) return;

        const userMenu = document.createElement('li');
        userMenu.className = 'dropdown';
        userMenu.innerHTML = `
            <a href="#" class="nav-link dropdown-toggle">
                ${this.user.first_name} ${this.user.last_name}
                <span class="dropdown-arrow">▼</span>
            </a>
            <ul class="dropdown-menu">
                <li><a href="/profile" class="dropdown-item">Мій профіль</a></li>
                <li><a href="/bookings" class="dropdown-item">Мої бронювання</a></li>
                ${this.isAdmin() ? '<li><a href="/admin" class="dropdown-item">Адмін панель</a></li>' : ''}
                ${this.isAdmin() ? '<li><a href="/users" class="dropdown-item">Користувачі</a></li>' : ''}
                <li><a href="#" class="dropdown-item" onclick="event.preventDefault(); authManager.logout()">Вийти</a></li>
            </ul>
        `;
        navList.appendChild(userMenu);

        const toggle = userMenu.querySelector('.dropdown-toggle');
        const menu = userMenu.querySelector('.dropdown-menu');
        const arrow = userMenu.querySelector('.dropdown-arrow');

        toggle.addEventListener('click', e => {
            e.preventDefault();
            const isOpen = menu.classList.contains('show');
            document.querySelectorAll('.dropdown-menu.show').forEach(m => {
                if (m !== menu) {
                    m.classList.remove('show');
                    m.closest('.dropdown').querySelector('.dropdown-arrow').classList.remove('rotated');
                }
            });
            menu.classList.toggle('show');
            arrow.classList.toggle('rotated', !isOpen);
        });

        document.addEventListener('click', e => {
            if (!userMenu.contains(e.target)) {
                menu.classList.remove('show');
                arrow.classList.remove('rotated');
            }
        });
    }

    removeUserMenu(navList) {
        if (!navList) return;
        const userMenu = navList.querySelector('.dropdown');
        if (userMenu) userMenu.remove();
    }

    async validateToken() {
        if (!this.token) return this.logout();
        try {
            const res = await fetch('/api/v1/auth/me', {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });
            if (!res.ok) return this.logout();
            const data = await res.json();
            this.user = data;
            localStorage.setItem('user', JSON.stringify(data));
            this.updateNavigation();
        } catch {
            this.logout();
        }
    }

    async login(email, password) {
        try {
            const res = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (res.ok) {
                this.token = data.token;
                this.user = data.user;
                localStorage.setItem('user', JSON.stringify(data.user));
                this.setCookie('auth_token', this.token, 1);
                this.updateNavigation();
                return { success: true };
            } else return { success: false, message: data.message };
        } catch {
            return { success: false, message: 'Server error' };
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('user');
        this.setCookie('auth_token', '', -1);
        this.updateNavigation();
        if (window.location.pathname !== '/') window.location.href = '/';
    }

    setCookie(name, value, days) {
        let expires = '';
        if (days) {
            const d = new Date();
            d.setTime(d.getTime() + days*24*60*60*1000);
            expires = "; expires=" + d.toUTCString();
        }
        document.cookie = `${name}=${value || ""}${expires}; path=/`;
    }

    getCookie(name) {
        const nameEQ = name + "=";
        const ca = document.cookie.split(';');
        for(let c of ca) {
            while (c.charAt(0)==' ') c = c.substring(1);
            if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length);
        }
        return null;
    }

    // Метод для всіх запитів з токеном
    async makeAuthenticatedRequest(url, options = {}) {
        if (!options.headers) options.headers = {};
        if (this.token) options.headers['Authorization'] = `Bearer ${this.token}`;
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        return res;
    }
}

const authManager = new AuthManager();
window.authManager = authManager;