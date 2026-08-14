// Meds API Client Layer
const API_BASE_URL = (window.location.port === '5000' || window.location.host.includes(':5000'))
  ? window.location.origin 
  : 'http://localhost:5000';

let authToken = localStorage.getItem('meds_jwt_token') || null;
let currentUser = JSON.parse(localStorage.getItem('meds_user_info') || 'null');

// Toast Notification Engine
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerText = message;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Authenticated Fetch Wrapper
async function apiCall(endpoint, method = 'GET', body = null) {
  // If not logged in, don't execute protected API calls silently
  if (!authToken && endpoint !== '/auth/login' && endpoint !== '/auth/register' && endpoint !== '/outlet/public-list' && endpoint !== '/') {
    return { success: false, error: 'Authentication required' };
  }

  const headers = {
    'Content-Type': 'application/json'
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  try {
    const options = { method, headers };
    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (response.status === 401) {
      if (authToken) {
        // Token expired or invalid while logged in
        logoutUser();
        showToast('Session expired. Please sign in again.', 'error');
      }
      const data = await response.json().catch(() => ({}));
      return { success: false, error: data.error || 'Invalid password' };
    }

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      return { success: false, error: data.error || data.message || `HTTP ${response.status}` };
    }

    return { success: true, data };
  } catch (err) {
    console.error(`API Error [${method} ${endpoint}]:`, err.message);
    return { success: false, error: err.message };
  }
}

// Check Backend Connection Status
async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/`);
    const statusText = document.getElementById('systemStatusText');
    const statusBadge = document.getElementById('systemStatusBadge');
    
    if (res.ok) {
      if (statusText) statusText.innerText = 'API Connected';
      if (statusBadge) statusBadge.className = 'status-badge connected';
      return true;
    } else {
      throw new Error('API server returned non-200');
    }
  } catch (e) {
    const statusText = document.getElementById('systemStatusText');
    const statusBadge = document.getElementById('systemStatusBadge');
    if (statusText) statusText.innerText = 'Offline Mode';
    if (statusBadge) statusBadge.className = 'status-badge demo';
    return false;
  }
}
