/**
 * Auth JS — Handles login/register forms for CompilerFix.
 * FIXED: Uses relative URLs instead of hardcoded localhost.
 */

// Tab switching
function switchTab(tab) {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const slider = document.getElementById('tab-slider');
    const statusMsg = document.getElementById('status-msg');

    statusMsg.textContent = '';
    statusMsg.className = 'status-msg';

    if (tab === 'login') {
        loginForm.classList.add('active');
        registerForm.classList.remove('active');
        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');
        slider.style.transform = 'translateX(0)';
    } else {
        loginForm.classList.remove('active');
        registerForm.classList.add('active');
        tabLogin.classList.remove('active');
        tabRegister.classList.add('active');
        slider.style.transform = 'translateX(100%)';
    }
}

// Show status message
function showStatus(message, type) {
    const el = document.getElementById('status-msg');
    el.textContent = message;
    el.className = `status-msg ${type}`;
}

// Login handler
async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    if (!username || !password) {
        showStatus('Please fill in all fields', 'error');
        return;
    }

    const btn = document.getElementById('login-submit');
    btn.disabled = true;
    btn.querySelector('span').textContent = 'Logging in...';

    try {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (data.success) {
            localStorage.setItem('compilerfix_token', data.token);
            localStorage.setItem('compilerfix_user', data.username);
            showStatus('Login successful! Redirecting...', 'success');
            setTimeout(() => { window.location.href = '/editor'; }, 800);
        } else {
            showStatus(data.error || 'Login failed', 'error');
        }
    } catch (err) {
        showStatus('Could not connect to server', 'error');
    } finally {
        btn.disabled = false;
        btn.querySelector('span').textContent = 'Login';
    }
}

// Register handler
async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('reg-username').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirm = document.getElementById('reg-confirm').value;

    if (!username || !password || !confirm) {
        showStatus('Please fill in all fields', 'error');
        return;
    }

    if (password !== confirm) {
        showStatus('Passwords do not match', 'error');
        return;
    }

    if (username.length < 3) {
        showStatus('Username must be at least 3 characters', 'error');
        return;
    }

    if (password.length < 4) {
        showStatus('Password must be at least 4 characters', 'error');
        return;
    }

    const btn = document.getElementById('reg-submit');
    btn.disabled = true;
    btn.querySelector('span').textContent = 'Creating account...';

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await res.json();

        if (data.success) {
            localStorage.setItem('compilerfix_token', data.token);
            localStorage.setItem('compilerfix_user', data.username);
            showStatus('Account created! Redirecting...', 'success');
            setTimeout(() => { window.location.href = '/editor'; }, 800);
        } else {
            showStatus(data.error || 'Registration failed', 'error');
        }
    } catch (err) {
        showStatus('Could not connect to server', 'error');
    } finally {
        btn.disabled = false;
        btn.querySelector('span').textContent = 'Create Account';
    }
}

// If already logged in, redirect
window.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('compilerfix_token');
    if (token) {
        window.location.href = '/editor';
    }
});
