function showRegister() {
    document.getElementById('registerModal').style.display = 'block';
}

function closeModal() {
    document.getElementById('registerModal').style.display = 'none';
}

function showToast(message, isError = false) {
    let el = document.getElementById('toast');
    if (!el) {
        el = document.createElement('div');
        el.id = 'toast';
        el.style.position = 'fixed';
        el.style.top = '16px';
        el.style.right = '16px';
        el.style.maxWidth = '360px';
        el.style.padding = '12px 14px';
        el.style.borderRadius = '10px';
        el.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
        el.style.zIndex = '9999';
        el.style.display = 'none';
        el.style.color = '#fff';
        document.body.appendChild(el);
    }
    el.style.background = isError ? '#dc2626' : '#16a34a';
    el.textContent = message;
    el.style.display = 'block';
    clearTimeout(window.__toastTimer);
    window.__toastTimer = setTimeout(() => {
        el.style.display = 'none';
    }, 2200);
}

window.onclick = function(event) {
    const modal = document.getElementById('registerModal');
    if (event.target === modal) {
        closeModal();
    }
}

async function registerUser(event) {
    event.preventDefault();
    
    const form = event.target;
    if (!form) {
        showToast('Ошибка: форма не найдена', true);
        return;
    }
    
    const fullName = form.regFullName?.value?.trim() || '';
    const email = form.regEmail?.value || '';
    const phone = form.regPhone?.value || '';
    const password = form.regPassword?.value || '';
    const role = form.regRole?.value || 'client';
    
    if (!fullName) {
        showToast('Пожалуйста, введите ФИО', true);
        return;
    }
    
    const nameParts = fullName.split(' ').filter(part => part.length > 0);
    const firstName = nameParts[0] || '';
    const lastName = nameParts.length > 1 ? nameParts[nameParts.length - 1] : '';
    const middleName = nameParts.length > 2 ? nameParts.slice(1, -1).join(' ') : null;
    
    if (!firstName || !lastName) {
        showToast('Пожалуйста, введите имя и фамилию', true);
        return;
    }
    
    const userData = {
        email: email,
        phone: phone,
        password: password,
        first_name: firstName,
        last_name: lastName,
        middle_name: middleName || null,
        role: role
    };
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        const data = await response.json();
        
        if (response.ok || response.status === 201) {
            showToast(`Пользователь ${data.email} успешно зарегистрирован`);
            closeModal();
            form.reset();
            window.location.href = '/login';
        } else {
            showToast(data.detail || 'Ошибка при регистрации', true);
        }
    } catch (error) {
        showToast('Ошибка при регистрации', true);
    }
}

async function loginUser(event) {
    event.preventDefault();
    
    const credentials = {
        email: document.getElementById('username').value,
        password: document.getElementById('password').value
    };
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials)
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            window.location.href = '/dashboard';
        } else {
            const error = await response.json();
            showToast(error.detail || 'Ошибка входа', true);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showToast('Ошибка при входе', true);
    }
}

function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token && window.location.pathname !== '/' && window.location.pathname !== '/login') {
        window.location.href = '/login';
    }
    return token;
}

async function getCurrentUser() {
    const token = checkAuth();
    if (!token) return null;
    
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return null;
        }
    } catch (error) {
        console.error('Ошибка:', error);
        return null;
    }
}

function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/';
}

async function loadClientDashboard(user) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/clients/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const clientData = await response.json();
            document.getElementById('visitsLeft').textContent = clientData.visits_left;
            document.getElementById('hasSubscription').textContent = 
                clientData.has_subscription ? 'Активен' : 'Неактивен';
        }
    } catch (error) {
        console.error('Ошибка при загрузке данных клиента:', error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname === '/dashboard') {
        loadDashboard();
    }
});

