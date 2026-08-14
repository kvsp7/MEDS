// Meds Pharmacy Platform - Main Application Controller
let appState = {
  activeTab: 'dashboard',
  authMode: 'login',
  medicines: [],
  batches: [],
  outlets: [],
  customers: [],
  sales: [],
  revenueChart: null,
  outletChart: null,
  topMedsChart: null
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigation();
  initAuthState();
  await checkBackendHealth();
  await loadPublicOutlets();
});

async function loadPublicOutlets() {
  const select = document.getElementById('authOutletSelect');
  if (!select) return;
  
  const res = await apiCall('/outlet/public-list');
  if (res.success && Array.isArray(res.data) && res.data.length > 0) {
    select.innerHTML = `<option value="all">🏢 All Outlets (Global Access)</option>` + 
      res.data.map(o => `<option value="${o.id}">${o.name} (${o.location})</option>`).join('');
  } else {
    select.innerHTML = `<option value="all">🏢 All Outlets (Global Access)</option>
      <option value="1">Store A - Main Pharmacy</option>
      <option value="2">Store B - Downtown Branch</option>`;
  }
}

function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetTab = item.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  appState.activeTab = tabId;
  
  // Update sidebar active state
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });

  // Update tab pane active state
  document.querySelectorAll('.tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
  });

  // Re-render tab specific views
  if (tabId === 'dashboard') renderDashboard();
  if (tabId === 'pos') renderPOSView();
  if (tabId === 'inventory') renderInventoryView();
  if (tabId === 'outlets') renderOutletsView();
  if (tabId === 'reports') renderReportsView();
  if (tabId === 'ai-hub') renderAIHubView();
}

function showSubTab(subTabId, btnEl) {
  document.querySelectorAll('.sub-tab-btn').forEach(b => b.classList.remove('active'));
  btnEl.classList.add('active');

  document.querySelectorAll('.subtab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === `subtab-${subTabId}`);
  });
}

// ==================== AUTHENTICATION & UI GATE ====================
function initAuthState() {
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', logoutUser);

  const authTabLogin = document.getElementById('authTabLogin');
  if (authTabLogin) {
    authTabLogin.addEventListener('click', () => toggleAuthMode('login'));
  }

  const authTabRegister = document.getElementById('authTabRegister');
  if (authTabRegister) {
    authTabRegister.addEventListener('click', () => toggleAuthMode('register'));
  }

  updateAuthGateUI();
}


function updateAuthGateUI() {
  const landingScreen = document.getElementById('authLandingScreen');
  const mainWrapper = document.getElementById('mainAppWrapper');
  const avatar = document.getElementById('userAvatar');
  const nameDisp = document.getElementById('userNameDisplay');
  const roleDisp = document.getElementById('userRoleDisplay');
  const outletSelect = document.getElementById('currentOutletSelect');

  if (currentUser && authToken) {
    if (landingScreen) landingScreen.classList.add('hidden');
    if (mainWrapper) mainWrapper.classList.remove('hidden');
    
    if (avatar) avatar.innerText = currentUser.username.charAt(0).toUpperCase();
    if (nameDisp) nameDisp.innerText = currentUser.username;
    
    const outletLabel = currentUser.outlet_name ? ` • ${currentUser.outlet_name}` : '';
    if (roleDisp) roleDisp.innerText = `${currentUser.role || 'admin'}${outletLabel}`;

    // Update active store selector permissions
    if (outletSelect) {
      if (currentUser.role !== 'admin' && currentUser.outlet_id) {
        outletSelect.disabled = true;
      } else {
        outletSelect.disabled = false;
      }
    }
    
    // Refresh live data after unlocking portal
    refreshAllData();
  } else {
    if (landingScreen) landingScreen.classList.remove('hidden');
    if (mainWrapper) mainWrapper.classList.add('hidden');
  }
}

function setAuthError(msg) {
  const errContainer = document.getElementById('authErrorMessage');
  const errText = document.getElementById('authErrorText');
  if (errContainer && errText) {
    if (msg) {
      errText.innerText = msg;
      errContainer.classList.remove('hidden');
    } else {
      errText.innerText = '';
      errContainer.classList.add('hidden');
    }
  }
}

function toggleAuthMode(mode) {
  setAuthError(null);
  appState.authMode = mode;
  document.getElementById('authTabLogin').classList.toggle('active', mode === 'login');
  document.getElementById('authTabRegister').classList.toggle('active', mode === 'register');
  document.getElementById('authRoleGroup').classList.toggle('hidden', mode === 'login');
  document.getElementById('authOutletGroup').classList.toggle('hidden', mode === 'login');
  
  document.getElementById('authSubmitBtn').innerText = mode === 'login' ? '🚀 Enter Meds Operations Portal' : '✨ Register New Account';
}

async function handleAuthSubmit(event) {
  if (event) event.preventDefault();
  setAuthError(null);
  
  const submitBtn = document.getElementById('authSubmitBtn');
  if (submitBtn && submitBtn.disabled) return;
  
  const usernameInput = document.getElementById('authUsername');
  const passwordInput = document.getElementById('authPassword');
  
  const username = usernameInput ? usernameInput.value.trim() : '';
  const password = passwordInput ? passwordInput.value.trim() : '';
  const role = document.getElementById('authRole') ? document.getElementById('authRole').value : 'admin';

  if (!username || !password) {
    const errMsg = 'Please enter both username and password';
    setAuthError(errMsg);
    showToast(errMsg, 'error');
    return;
  }

  const originalBtnText = submitBtn ? submitBtn.innerText : '';
  if (submitBtn) {
    submitBtn.innerText = '⏳ Authenticating...';
    submitBtn.disabled = true;
  }

  try {
    if (appState.authMode === 'register') {
      const selectedOutletVal = document.getElementById('authOutletSelect') ? document.getElementById('authOutletSelect').value : 'all';
      const outlet_id = (selectedOutletVal && selectedOutletVal !== 'all') ? parseInt(selectedOutletVal) : null;

      const res = await apiCall('/auth/register', 'POST', { username, password, role, outlet_id });
      if (res.success) {
        showToast('Account created! Auto signing in...', 'success');
        const loginRes = await apiCall('/auth/login', 'POST', { username, password });
        if (loginRes.success && loginRes.data.token) {
          authToken = loginRes.data.token;
          currentUser = loginRes.data.user || { username, role, outlet_id };
          localStorage.setItem('meds_jwt_token', authToken);
          localStorage.setItem('meds_user_info', JSON.stringify(currentUser));
          updateAuthGateUI();
          showToast(`Welcome to Meds Operations, ${currentUser.username}!`, 'success');
        } else {
          toggleAuthMode('login');
        }
      } else {
        const errMsg = res.error || 'Registration failed. Try a different username.';
        setAuthError(errMsg);
        showToast(errMsg, 'error');
      }
    } else {
      const res = await apiCall('/auth/login', 'POST', { username, password });
      if (res.success && res.data.token) {
        authToken = res.data.token;
        currentUser = res.data.user || { username, role: 'admin' };
        
        localStorage.setItem('meds_jwt_token', authToken);
        localStorage.setItem('meds_user_info', JSON.stringify(currentUser));
        
        updateAuthGateUI();
        showToast(`Welcome back to Meds Operations, ${currentUser.username}!`, 'success');
      } else {
        const errMsg = res.error || 'Login failed. Please check credentials.';
        setAuthError(errMsg);
        showToast(errMsg, 'error');
      }
    }
  } finally {
    if (submitBtn) {
      submitBtn.innerText = originalBtnText || (appState.authMode === 'login' ? '🚀 Enter Meds Operations Portal' : '✨ Register New Account');
      submitBtn.disabled = false;
    }
  }
}



function logoutUser() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('meds_jwt_token');
  localStorage.removeItem('meds_user_info');
  updateAuthGateUI();
  showToast('Signed out of Meds Operations Portal', 'info');
}

// ==================== DATA FETCHING (STRICT LIVE DATA) ====================
async function refreshAllData() {
  if (!authToken) return;

  await Promise.all([
    fetchOutlets(),
    fetchMedicines(),
    fetchBatches(),
    fetchCustomers(),
    fetchSalesHistory()
  ]);

  populateDropdowns();

  if (appState.activeTab === 'dashboard') renderDashboard();
  if (appState.activeTab === 'pos') renderPOSView();
  if (appState.activeTab === 'inventory') renderInventoryView();
  if (appState.activeTab === 'outlets') renderOutletsView();
  if (appState.activeTab === 'reports') renderReportsView();
  if (appState.activeTab === 'ai-hub') renderAIHubView();
}

async function fetchOutlets() {
  const res = await apiCall('/outlet/all');
  if (res.success && Array.isArray(res.data)) {
    appState.outlets = res.data;
  } else {
    appState.outlets = [];
  }
}

async function fetchMedicines() {
  const res = await apiCall('/medicine/all');
  if (res.success && Array.isArray(res.data)) {
    appState.medicines = res.data;
  } else {
    appState.medicines = [];
  }
}

async function fetchBatches() {
  const res = await apiCall('/batch/all');
  if (res.success && Array.isArray(res.data)) {
    appState.batches = res.data;
  } else {
    appState.batches = [];
  }
}

async function fetchCustomers() {
  const res = await apiCall('/customer/all');
  if (res.success && Array.isArray(res.data)) {
    appState.customers = res.data;
  } else {
    appState.customers = [];
  }
}

function getActiveOutletParam() {
  const select = document.getElementById('currentOutletSelect');
  if (select && select.value) {
    if (select.value === 'all') return '';
    return `?outlet_id=${select.value}`;
  }
  if (currentUser && currentUser.outlet_id && currentUser.role !== 'admin') {
    return `?outlet_id=${currentUser.outlet_id}`;
  }
  return '';
}

async function fetchSalesHistory() {
  const param = getActiveOutletParam();
  const res = await apiCall(`/sales/all${param}`);
  if (res.success && Array.isArray(res.data)) {
    appState.sales = res.data;
  } else {
    appState.sales = [];
  }
}

function populateDropdowns() {
  // Outlets select
  const outletSelect = document.getElementById('currentOutletSelect');
  const batchOutletSelect = document.getElementById('batchOutlet');
  
  if (appState.outlets.length === 0) {
    if (outletSelect) outletSelect.innerHTML = `<option value="all">🏢 All Outlets (Global View)</option>`;
    if (batchOutletSelect) batchOutletSelect.innerHTML = `<option value="">No Outlets Available</option>`;
  } else {
    const previousVal = outletSelect ? outletSelect.value : null;

    const allOpt = (currentUser && currentUser.role === 'admin') ? `<option value="all">🏢 All Outlets (Global View)</option>` : '';
    const opts = allOpt + appState.outlets.map(o => 
      `<option value="${o.id}">${o.name} (${o.location || 'Main'})</option>`
    ).join('');
    const batchOpts = appState.outlets.map(o => 
      `<option value="${o.id}">${o.name} (${o.location || 'Main'})</option>`
    ).join('');

    if (outletSelect) {
      outletSelect.innerHTML = opts;
      if (previousVal && (previousVal === 'all' || appState.outlets.some(o => o.id == previousVal))) {
        outletSelect.value = previousVal;
      } else if (currentUser && currentUser.outlet_id && currentUser.role !== 'admin') {
        outletSelect.value = currentUser.outlet_id;
      } else {
        outletSelect.value = 'all';
      }
    }
    if (batchOutletSelect) batchOutletSelect.innerHTML = batchOpts;
  }

  // Medicines select for POS & Batch & AI Predict
  const posMedSelect = document.getElementById('posMedicine');
  const batchMedSelect = document.getElementById('batchMedicine');
  const aiPredictMedSelect = document.getElementById('aiPredictMedSelect');

  if (appState.medicines.length === 0) {
    if (posMedSelect) posMedSelect.innerHTML = `<option value="">No Medicines Registered Yet</option>`;
    if (batchMedSelect) batchMedSelect.innerHTML = `<option value="">No Medicines Available</option>`;
    if (aiPredictMedSelect) aiPredictMedSelect.innerHTML = `<option value="">No Medicines Available</option>`;
  } else {
    const medOptions = appState.medicines.map(m => 
      `<option value="${m.id}">${m.name} - ₹${m.price.toFixed(2)} (${m.category})</option>`
    ).join('');

    if (posMedSelect) posMedSelect.innerHTML = `<option value="">-- Choose Medicine --</option>` + medOptions;
    if (batchMedSelect) batchMedSelect.innerHTML = medOptions;
    if (aiPredictMedSelect) aiPredictMedSelect.innerHTML = medOptions;
  }

  // Customers select for POS
  const posCustSelect = document.getElementById('posCustomer');
  if (posCustSelect) {
    posCustSelect.innerHTML = `<option value="">Walk-in Customer</option>` + 
      appState.customers.map(c => `<option value="${c.id}">${c.name} (${c.type})</option>`).join('');
  }
}

// ==================== DASHBOARD VIEW ====================
async function renderDashboard() {
  if (!authToken) return;
  const param = getActiveOutletParam();

  // Fetch Revenue
  const revRes = await apiCall(`/report/revenue${param}`);
  const revenue = (revRes.success && revRes.data.total_revenue !== undefined) 
    ? (revRes.data.total_revenue || 0) 
    : calculateTotalRevenueLive();
  document.getElementById('kpiRevenue').innerText = `₹${revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  // Fetch Profit
  const profitRes = await apiCall(`/report/profit${param}`);
  const profit = (profitRes.success && profitRes.data.total_profit !== undefined) 
    ? (profitRes.data.total_profit || 0) 
    : calculateTotalProfitLive();
  document.getElementById('kpiProfit').innerText = `₹${profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

  // Sales count & medicines count
  document.getElementById('kpiSalesCount').innerText = appState.sales.length;
  document.getElementById('kpiMedicinesCount').innerText = appState.medicines.length;

  // Fast Moving List
  renderFastMovingList();

  // Low stock alerts
  renderDashboardReplenishment();

  // Render Charts
  renderDashboardCharts(revenue, profit);
}

function calculateTotalRevenueLive() {
  return appState.sales.reduce((sum, s) => sum + (s.total_price || 0), 0);
}

function calculateTotalProfitLive() {
  return appState.sales.reduce((sum, s) => {
    const med = appState.medicines.find(m => m.id === s.medicine_id);
    const cost = med ? (med.cost_price * s.quantity) : 0;
    return sum + (s.total_price - cost);
  }, 0);
}

async function renderFastMovingList() {
  const container = document.getElementById('fastMovingList');
  if (!container) return;

  const param = getActiveOutletParam();
  const res = await apiCall(`/report/fast-moving${param}`);
  let items = [];
  if (res.success && Array.isArray(res.data)) {
    items = res.data;
  }

  if (items.length === 0) {
    container.innerHTML = `<p class="text-muted p-3">No sales transactions recorded yet.</p>`;
    return;
  }

  container.innerHTML = items.map((item, idx) => `
    <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
      <div>
        <strong>#${idx + 1} ${item.medicine_name}</strong>
      </div>
      <span class="badge badge-success">${item.total_sold || item.quantity_sold} units sold</span>
    </div>
  `).join('');
}

async function renderDashboardReplenishment() {
  const container = document.getElementById('dashboardReplenishmentAlerts');
  if (!container) return;

  const res = await apiCall('/ai/replenishment');
  let suggestions = [];
  if (res.success && Array.isArray(res.data)) {
    suggestions = res.data;
  }

  if (suggestions.length === 0) {
    container.innerHTML = `<p class="text-success p-3">✅ All stock levels across stores are clear!</p>`;
    return;
  }

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>AI Admin Low Stock Notification</th>
          <th>Store & Location</th>
          <th>Medicine</th>
          <th>Stock Left</th>
          <th>Suggested Reorder</th>
        </tr>
      </thead>
      <tbody>
        ${suggestions.map(s => `
          <tr>
            <td><strong class="text-amber" style="font-size:0.85rem;">⚠️ "${s.message || `hi. admin the store ${s.outlet_name || 'Store'} in ${s.outlet_location || 'Main'} has low stock in ${s.medicine} ${s.current_stock} quantity left`}"</strong></td>
            <td><strong>${s.outlet_name || 'Store'}</strong><br><span class="text-muted fs-sm">📍 ${s.outlet_location || 'Main'}</span></td>
            <td><strong>${s.medicine}</strong></td>
            <td><span class="badge badge-danger">${s.current_stock} units left</span></td>
            <td><span class="badge badge-success">+${s.suggested_reorder} units</span></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function renderDashboardCharts(revenue, profit) {
  const ctx = document.getElementById('dashboardRevenueChart');
  if (!ctx) return;

  if (appState.revenueChart) appState.revenueChart.destroy();

  appState.revenueChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Current Live Period'],
      datasets: [
        {
          label: 'Live Revenue (₹)',
          data: [revenue],
          backgroundColor: 'rgba(6, 182, 212, 0.75)',
          borderRadius: 6
        },
        {
          label: 'Net Estimated Profit (₹)',
          data: [profit],
          backgroundColor: 'rgba(16, 185, 129, 0.75)',
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8' } }
      },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

// ==================== POS BILLING VIEW ====================
function renderPOSView() {
  updatePOSPriceInfo();
  renderRecentSalesTable();
}

function updatePOSPriceInfo() {
  const medId = parseInt(document.getElementById('posMedicine').value);
  const med = appState.medicines.find(m => m.id === medId);
  const selectedOutletVal = document.getElementById('currentOutletSelect') ? document.getElementById('currentOutletSelect').value : '';

  const warningEl = document.getElementById('posAllOutletsWarning');
  const breakdownEl = document.getElementById('posStoreBreakdown');
  const submitBtn = document.getElementById('posSubmitBtn');

  const isAllOutlets = (selectedOutletVal === 'all' || !selectedOutletVal);

  if (isAllOutlets) {
    if (warningEl) warningEl.classList.remove('hidden');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = '⚠️ Billing Disabled for "All Outlets"';
    }
  } else {
    if (warningEl) warningEl.classList.add('hidden');
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerText = '✅ Complete Checkout & Print Invoice';
    }
  }

  if (!med) {
    document.getElementById('posUnitPrice').innerText = '₹0.00';
    document.getElementById('posCostPrice').innerText = '₹0.00';
    document.getElementById('posAvailableStock').innerText = '0 units';
    if (breakdownEl) {
      breakdownEl.style.display = 'none';
      breakdownEl.innerHTML = '';
    }
    updatePOSTotal();
    return;
  }

  document.getElementById('posUnitPrice').innerText = `₹${med.price.toFixed(2)}`;
  document.getElementById('posCostPrice').innerText = `₹${med.cost_price ? med.cost_price.toFixed(2) : '0.00'}`;

  if (isAllOutlets) {
    // Sum stock across ALL outlets
    const allBatches = appState.batches.filter(b => b.medicine_id === medId);
    const totalStock = allBatches.reduce((sum, b) => sum + b.quantity, 0);

    const stockEl = document.getElementById('posAvailableStock');
    stockEl.innerText = `${totalStock} units (All Stores Combined)`;
    stockEl.className = totalStock > 10 ? 'text-success' : 'text-danger';

    // Build store-by-store breakdown
    if (breakdownEl) {
      breakdownEl.style.display = 'block';
      let breakdownHtml = `<p style="margin-bottom:6px; font-weight:600; color:#06b6d4;">🏬 Stock Quantity Breakdown by Store:</p><ul style="padding-left:18px; margin:0;">`;
      
      if (appState.outlets.length === 0) {
        breakdownHtml += `<li>No outlets configured</li>`;
      } else {
        appState.outlets.forEach(o => {
          const storeBatches = allBatches.filter(b => b.outlet_id === o.id);
          const storeQty = storeBatches.reduce((sum, b) => sum + b.quantity, 0);
          const badgeClass = storeQty > 5 ? 'badge-success' : (storeQty > 0 ? 'badge-warning' : 'badge-danger');
          breakdownHtml += `<li style="margin-bottom:4px;"><strong>${o.name}</strong> (${o.location || 'Main'}): <span class="badge ${badgeClass}">${storeQty} units</span></li>`;
        });
      }
      breakdownHtml += `</ul>`;
      breakdownEl.innerHTML = breakdownHtml;
    }
  } else {
    // Specific outlet selected
    const outletId = parseInt(selectedOutletVal);
    const outletBatches = appState.batches.filter(b => b.medicine_id === medId && b.outlet_id === outletId);
    const stock = outletBatches.reduce((sum, b) => sum + b.quantity, 0);

    const stockEl = document.getElementById('posAvailableStock');
    stockEl.innerText = `${stock} units`;
    stockEl.className = stock > 10 ? 'text-success' : 'text-danger';

    if (breakdownEl) {
      breakdownEl.style.display = 'none';
      breakdownEl.innerHTML = '';
    }
  }

  updatePOSTotal();
}

function updatePOSTotal() {
  const medId = parseInt(document.getElementById('posMedicine').value);
  const qty = parseInt(document.getElementById('posQuantity').value) || 1;
  const med = appState.medicines.find(m => m.id === medId);

  const price = med ? med.price : 0;
  const total = price * qty;

  document.getElementById('posSubtotal').innerText = `₹${total.toFixed(2)}`;
  document.getElementById('posGrandTotal').innerText = `₹${total.toFixed(2)}`;
}

async function handlePOSSubmit(event) {
  event.preventDefault();
  const selectedOutletVal = document.getElementById('currentOutletSelect') ? document.getElementById('currentOutletSelect').value : '';

  if (selectedOutletVal === 'all' || !selectedOutletVal) {
    showToast('Cannot perform billing operation when "All Outlets" is selected. Please select a specific store.', 'error');
    return;
  }

  const medId = parseInt(document.getElementById('posMedicine').value);
  const qty = parseInt(document.getElementById('posQuantity').value);
  const customerId = parseInt(document.getElementById('posCustomer').value) || null;
  const outletId = parseInt(selectedOutletVal);

  if (!outletId) {
    showToast('Please create or select an outlet first!', 'error');
    return;
  }

  if (!medId || !qty || qty <= 0) {
    showToast('Please select a medicine and valid quantity', 'error');
    return;
  }

  const res = await apiCall('/sales/sell', 'POST', {
    medicine_id: medId,
    quantity: qty,
    outlet_id: outletId,
    customer_id: customerId
  });

  if (res.success && res.data.invoice) {
    showToast('Sale completed successfully!', 'success');
    renderInvoiceModal(res.data.invoice);
    await refreshAllData();
  } else {
    showToast(res.error || 'Sale transaction failed', 'error');
  }
}

function renderInvoiceModal(inv) {
  const modalBody = document.getElementById('invoiceModalBody');
  modalBody.innerHTML = `
    <div style="text-align:center; padding:10px; border-bottom:1px dashed rgba(255,255,255,0.15);">
      <h2>✚ Meds Pharmacy</h2>
      <p>Tax Invoice #: <strong>${inv.invoice_id || inv.invoice_number}</strong></p>
      <p class="text-muted fs-sm">Date: ${inv.timestamp}</p>
    </div>
    <div style="padding:16px 0;">
      <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
        <span>Item Purchased:</span>
        <strong>${inv.medicine_name}</strong>
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
        <span>Quantity:</span>
        <span>${inv.quantity} units</span>
      </div>
      <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
        <span>Unit Price:</span>
        <span>₹${inv.price_per_unit || (inv.total_price / inv.quantity)}</span>
      </div>
      <hr style="border-color:rgba(255,255,255,0.1); margin:12px 0;">
      <div style="display:flex; justify-content:space-between; font-size:18px;">
        <strong>Total Paid:</strong>
        <strong class="text-primary-glow">₹${inv.total_price.toFixed(2)}</strong>
      </div>
    </div>
  `;
  openModal('invoiceModal');
}

function renderRecentSalesTable() {
  const container = document.getElementById('recentSalesTable');
  if (!container) return;

  if (appState.sales.length === 0) {
    container.innerHTML = `<p class="text-muted p-4 text-center">No sales completed yet.</p>`;
    return;
  }

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>Invoice #</th>
          <th>Medicine</th>
          <th>Qty</th>
          <th>Total (₹)</th>
          <th>Customer</th>
          <th>Timestamp</th>
        </tr>
      </thead>
      <tbody>
        ${appState.sales.map(s => `
          <tr>
            <td><code>${s.invoice_number || 'INV-' + s.id}</code></td>
            <td><strong>${s.medicine_name}</strong></td>
            <td>${s.quantity}</td>
            <td>₹${s.total_price.toFixed(2)}</td>
            <td>${s.customer_name || 'Walk-in'}</td>
            <td class="text-muted fs-sm">${s.timestamp}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// ==================== INVENTORY VIEW ====================
function renderInventoryView() {
  renderMedicinesTable();
  renderBatchesTable();
}

function renderMedicinesTable() {
  const container = document.getElementById('medicinesTableWrapper');
  if (!container) return;

  if (appState.medicines.length === 0) {
    container.innerHTML = `<p class="text-muted p-4 text-center">No medicines in catalog. Click <strong>"Add New Medicine"</strong> to begin.</p>`;
    return;
  }

  container.innerHTML = `
    <table class="data-table" id="medicinesTable">
      <thead>
        <tr>
          <th>ID</th>
          <th>Medicine Name</th>
          <th>Category</th>
          <th>Selling Price (₹)</th>
          <th>Cost Price (₹)</th>
          <th>Margin</th>
          <th>Store Stock Breakdown</th>
        </tr>
      </thead>
      <tbody>
        ${appState.medicines.map(m => {
          const cost = m.cost_price || 0;
          const margin = m.price > 0 ? (((m.price - cost) / m.price) * 100).toFixed(0) : 0;
          
          const medBatches = appState.batches.filter(b => b.medicine_id === m.id);
          const totalQty = medBatches.reduce((sum, b) => sum + b.quantity, 0);
          
          let breakdownList = '';
          if (appState.outlets.length > 0) {
            breakdownList = appState.outlets.map(o => {
              const oQty = medBatches.filter(b => b.outlet_id === o.id).reduce((sum, b) => sum + b.quantity, 0);
              return `<span style="display:inline-block; margin-right:6px; margin-bottom:4px; font-size:0.75rem;" class="badge ${oQty > 5 ? 'badge-info' : (oQty > 0 ? 'badge-warning' : 'badge-danger')}">${o.name}: ${oQty} units</span>`;
            }).join('');
          } else {
            breakdownList = `<span class="text-muted fs-sm">No outlets</span>`;
          }

          return `
            <tr>
              <td>#${m.id}</td>
              <td><strong>${m.name}</strong><br><span class="text-muted fs-sm">${m.description || ''}</span></td>
              <td><span class="badge badge-primary">${m.category}</span></td>
              <td>₹${m.price.toFixed(2)}</td>
              <td>₹${cost.toFixed(2)}</td>
              <td><span class="badge badge-success">+${margin}%</span></td>
              <td>
                <strong class="text-cyan">${totalQty} units total</strong><br>
                ${breakdownList}
              </td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}

function renderBatchesTable() {
  const container = document.getElementById('batchesTableWrapper');
  if (!container) return;

  if (appState.batches.length === 0) {
    container.innerHTML = `<p class="text-muted p-4 text-center">No stock batches received yet. Click <strong>"Receive Stock Batch"</strong> to add stock.</p>`;
    return;
  }

  container.innerHTML = `
    <table class="data-table" id="batchesTable">
      <thead>
        <tr>
          <th>Batch #</th>
          <th>Medicine Name</th>
          <th>Quantity</th>
          <th>Expiry Date</th>
          <th>Outlet</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        ${appState.batches.map(b => {
          const isExpiring = new Date(b.expiry_date) < new Date(Date.now() + 30*24*60*60*1000);
          return `
            <tr>
              <td><code>${b.batch_number}</code></td>
              <td><strong>${b.medicine_name}</strong></td>
              <td>${b.quantity} units</td>
              <td>${b.expiry_date}</td>
              <td>${b.outlet_name || 'Outlet'}</td>
              <td>
                ${isExpiring 
                  ? '<span class="badge badge-danger">Expiring Soon</span>' 
                  : '<span class="badge badge-success">Good Stock</span>'}
              </td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}

function filterMedicinesTable() {
  const q = document.getElementById('medicineSearchInput').value.toLowerCase();
  const rows = document.querySelectorAll('#medicinesTable tbody tr');
  rows.forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

function filterBatchesTable() {
  const q = document.getElementById('batchSearchInput').value.toLowerCase();
  const rows = document.querySelectorAll('#batchesTable tbody tr');
  rows.forEach(row => {
    const text = row.innerText.toLowerCase();
    row.style.display = text.includes(q) ? '' : 'none';
  });
}

async function handleAddMedicineSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('medName').value.trim();
  const description = document.getElementById('medDescription').value.trim();
  const price = parseFloat(document.getElementById('medPrice').value);
  const cost_price = parseFloat(document.getElementById('medCostPrice').value);
  const category = document.getElementById('medCategory').value;

  const res = await apiCall('/medicine/add', 'POST', { name, description, price, cost_price, category });
  if (res.success) {
    showToast('Medicine added to catalog!', 'success');
    closeModal('addMedicineModal');
    await refreshAllData();
  } else {
    showToast(res.error || 'Failed to add medicine', 'error');
  }
}

async function handleAddBatchSubmit(event) {
  event.preventDefault();
  const medicine_id = parseInt(document.getElementById('batchMedicine').value);
  const batch_number = document.getElementById('batchNumber').value.trim();
  const expiry_date = document.getElementById('batchExpiry').value;
  const quantity = parseInt(document.getElementById('batchQuantity').value);
  const outlet_id = parseInt(document.getElementById('batchOutlet').value);

  if (!medicine_id || !outlet_id) {
    showToast('Please create medicine and outlet first', 'error');
    return;
  }

  const res = await apiCall('/batch/add', 'POST', { medicine_id, batch_number, expiry_date, quantity, outlet_id });
  if (res.success) {
    showToast('Stock batch received successfully!', 'success');
    closeModal('addBatchModal');
    await refreshAllData();
  } else {
    showToast(res.error || 'Failed to add batch', 'error');
  }
}

// ==================== OUTLETS & CUSTOMERS VIEW ====================
function renderOutletsView() {
  renderOutletsList();
  renderCustomersTable();
}

function renderOutletsList() {
  const container = document.getElementById('outletsList');
  if (!container) return;

  if (appState.outlets.length === 0) {
    container.innerHTML = `<p class="text-muted p-3">No outlets created yet. Click <strong>"Add New Outlet"</strong> to create one.</p>`;
    return;
  }

  container.innerHTML = appState.outlets.map(o => `
    <div class="glass-card p-3 mb-3 border-cyan" style="background:rgba(255,255,255,0.03); border-radius:12px; padding:16px;">
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <h4>🏪 ${o.name}</h4>
        <span class="badge badge-primary">${o.type}</span>
      </div>
      <p class="text-muted fs-sm mt-1">📍 Location: ${o.location}</p>
    </div>
  `).join('');
}

function renderCustomersTable() {
  const container = document.getElementById('customersTableWrapper');
  if (!container) return;

  if (appState.customers.length === 0) {
    container.innerHTML = `<p class="text-muted p-4 text-center">No customers registered yet.</p>`;
    return;
  }

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Customer Name</th>
          <th>Type</th>
          <th>Contact</th>
        </tr>
      </thead>
      <tbody>
        ${appState.customers.map(c => `
          <tr>
            <td>#${c.id}</td>
            <td><strong>${c.name}</strong></td>
            <td><span class="badge badge-info">${c.type}</span></td>
            <td>${c.contact || 'N/A'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

async function handleAddOutletSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('outletName').value.trim();
  const location = document.getElementById('outletLocation').value.trim();
  const type = document.getElementById('outletType').value;

  const res = await apiCall('/outlet/add', 'POST', { name, location, type });
  if (res.success) {
    showToast('Outlet created!', 'success');
    closeModal('addOutletModal');
    await refreshAllData();
  } else {
    showToast(res.error || 'Failed to create outlet', 'error');
  }
}

async function handleAddCustomerSubmit(event) {
  event.preventDefault();
  const name = document.getElementById('custName').value.trim();
  const type = document.getElementById('custType').value;
  const contact = document.getElementById('custContact').value.trim();

  const res = await apiCall('/customer/add', 'POST', { name, type, contact });
  if (res.success) {
    showToast('Customer recorded!', 'success');
    closeModal('addCustomerModal');
    await refreshAllData();
  } else {
    showToast(res.error || 'Failed to add customer', 'error');
  }
}

// ==================== REPORTS VIEW ====================
async function renderReportsView() {
  if (!authToken) return;
  const param = getActiveOutletParam();

  const perfRes = await apiCall(`/report/outlet-performance${param}`);
  let perfData = (perfRes.success && Array.isArray(perfRes.data)) ? perfRes.data : [];

  const topRes = await apiCall(`/report/top-medicines${param}`);
  let topData = (topRes.success && Array.isArray(topRes.data)) ? topRes.data : [];

  // Render Outlet Chart
  const ctxOutlet = document.getElementById('outletPerformanceChart');
  if (ctxOutlet) {
    if (appState.outletChart) appState.outletChart.destroy();
    appState.outletChart = new Chart(ctxOutlet, {
      type: 'bar',
      data: {
        labels: perfData.length > 0 ? perfData.map(p => p.outlet_name) : ['No Outlets'],
        datasets: [{
          label: 'Revenue (₹)',
          data: perfData.length > 0 ? perfData.map(p => p.total_revenue) : [0],
          backgroundColor: '#06b6d4'
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  // Render Top Meds Chart
  const ctxTop = document.getElementById('topMedicinesChart');
  if (ctxTop) {
    if (appState.topMedsChart) appState.topMedsChart.destroy();
    appState.topMedsChart = new Chart(ctxTop, {
      type: 'doughnut',
      data: {
        labels: topData.length > 0 ? topData.map(t => t.medicine_name) : ['No Sales'],
        datasets: [{
          data: topData.length > 0 ? topData.map(t => t.quantity_sold || t.total_sold) : [1],
          backgroundColor: ['#06b6d4', '#10b981', '#6366f1', '#f59e0b', '#ef4444']
        }]
      },
      options: { responsive: true, maintainAspectRatio: false }
    });
  }

  // Render Store P&L Table
  const pnlContainer = document.getElementById('storePnLTableWrapper');
  if (pnlContainer) {
    if (perfData.length === 0) {
      pnlContainer.innerHTML = `<p class="text-muted p-4 text-center">No store sales data available yet.</p>`;
    } else {
      pnlContainer.innerHTML = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Store Name</th>
              <th>Location</th>
              <th>Total Revenue (Income)</th>
              <th>Cost of Goods (COGS)</th>
              <th>Net Profit / Loss</th>
              <th>Profit Margin</th>
              <th>Total Sales</th>
              <th>Top Selling Medicine</th>
              <th>Performance Status</th>
            </tr>
          </thead>
          <tbody>
            ${perfData.map((p, idx) => {
              const isTop = idx === 0 && p.total_revenue > 0;
              const isProfit = p.total_profit >= 0;
              return `
                <tr ${isTop ? 'style="background: rgba(6, 182, 212, 0.08);"' : ''}>
                  <td>
                    <strong>${p.outlet_name}</strong>
                    ${isTop ? ' <span class="badge badge-success">🔥 Fastest Selling Store</span>' : ''}
                  </td>
                  <td>📍 ${p.location || 'Main'}</td>
                  <td>₹${(p.total_revenue || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td>₹${(p.total_cost || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                  <td class="${isProfit ? 'text-success' : 'text-danger'}" style="font-weight:600;">
                    ${isProfit ? '+' : ''}₹${(p.total_profit || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td><span class="badge ${isProfit ? 'badge-success' : 'badge-danger'}">${p.profit_margin || 0}%</span></td>
                  <td>${p.total_sales || 0} orders</td>
                  <td><strong>${p.top_medicine || 'N/A'}</strong> ${p.top_medicine_qty ? `(${p.top_medicine_qty} sold)` : ''}</td>
                  <td>
                    ${isTop 
                      ? '<span class="badge badge-cyan">Top Performer</span>' 
                      : (isProfit ? '<span class="badge badge-success">Profitable</span>' : '<span class="badge badge-warning">Low Margin</span>')}
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      `;
    }
  }
}

// ==================== MEDS AI HUB ====================
function renderAIHubView() {
  loadAIReplenishment();
}

async function handleAIChatSubmit(event) {
  event.preventDefault();
  const input = document.getElementById('aiQueryInput');
  const query = input.value.trim();
  if (!query) return;

  appendChatMessage(query, 'user');
  input.value = '';

  const res = await apiCall('/ai/chat', 'POST', { query });
  if (res.success && res.data.response) {
    appendChatMessage(res.data.response, 'bot');
  } else {
    appendChatMessage("I am connected to your Meds live database. Ask me about your revenue, sales count, top medicines, stock levels, or expiring batches!", 'bot');
  }
}

function appendChatMessage(text, sender) {
  const container = document.getElementById('chatMessages');
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;
  bubble.innerText = text;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

async function runAIDemandPrediction() {
  const medId = document.getElementById('aiPredictMedSelect').value;
  const resultBox = document.getElementById('aiPredictionResult');
  if (!medId) {
    resultBox.innerHTML = `⚠️ Please add a medicine first.`;
    return;
  }
  resultBox.innerText = 'Calculating linear regression prediction...';

  const res = await apiCall(`/ai/predict/${medId}`);
  if (res.success && res.data.predicted_demand !== undefined) {
    resultBox.innerHTML = `🔮 <strong>Predicted Demand:</strong> <span class="badge badge-success">${res.data.predicted_demand} units</span> for next period.`;
  } else {
    resultBox.innerHTML = `🔮 <strong>Predicted Demand:</strong> ${res.data.message || 'No sales data yet.'}`;
  }
}

async function runAIAnomalyDetection() {
  const resultBox = document.getElementById('aiAnomalyResult');
  resultBox.innerText = 'Scanning transaction log with Isolation Forest...';

  const res = await apiCall('/ai/anomalies');
  if (res.success && res.data.anomalies_found !== undefined) {
    resultBox.innerHTML = `🚨 <strong>Scan Complete:</strong> Found <span class="badge badge-warning">${res.data.anomalies_found} anomalies</span> out of ${res.data.total_records} transactions.`;
  } else {
    resultBox.innerHTML = `🚨 <strong>Scan Complete:</strong> ${res.data.message || '0 transaction anomalies detected.'}`;
  }
}

async function loadAIReplenishment() {
  const container = document.getElementById('aiReplenishmentTable');
  if (!container) return;

  const res = await apiCall('/ai/replenishment');
  let suggestions = [];
  if (res.success && Array.isArray(res.data)) {
    suggestions = res.data;
  }

  if (suggestions.length === 0) {
    container.innerHTML = `<p class="text-success p-4 text-center">✅ All medicine stock levels across stores are clear!</p>`;
    return;
  }

  container.innerHTML = `
    <table class="data-table">
      <thead>
        <tr>
          <th>AI Admin Suggestion Alert</th>
          <th>Store & Location</th>
          <th>Medicine</th>
          <th>Current Stock</th>
          <th>Suggested Reorder</th>
        </tr>
      </thead>
      <tbody>
        ${suggestions.map(s => `
          <tr>
            <td><strong class="text-amber" style="font-size:0.85rem;">⚠️ "${s.message || `hi. admin the store ${s.outlet_name || 'Store'} in ${s.outlet_location || 'Main'} has low stock in ${s.medicine} ${s.current_stock} quantity left`}"</strong></td>
            <td><strong>${s.outlet_name || 'Store'}</strong><br><span class="text-muted fs-sm">📍 ${s.outlet_location || 'Main'}</span></td>
            <td><strong>${s.medicine}</strong></td>
            <td><span class="badge badge-danger">${s.current_stock} units left</span></td>
            <td><span class="badge badge-success">+${s.suggested_reorder} units</span></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

// ==================== MODAL UTILITIES ====================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('active');
}

// Global Window Mappings
window.toggleAuthMode = toggleAuthMode;
window.handleAuthSubmit = handleAuthSubmit;
window.logoutUser = logoutUser;
window.switchTab = switchTab;
window.showSubTab = showSubTab;
window.openModal = openModal;
window.closeModal = closeModal;
window.handleAddMedicineSubmit = handleAddMedicineSubmit;
window.handleAddBatchSubmit = handleAddBatchSubmit;
window.handleAddOutletSubmit = handleAddOutletSubmit;
window.handleAddCustomerSubmit = handleAddCustomerSubmit;
window.handlePOSSubmit = handlePOSSubmit;
window.handleAIChatSubmit = handleAIChatSubmit;
window.runAIDemandPrediction = runAIDemandPrediction;
window.runAIAnomalyDetection = runAIAnomalyDetection;
window.loadAIReplenishment = loadAIReplenishment;
window.filterMedicinesTable = filterMedicinesTable;
window.filterBatchesTable = filterBatchesTable;
window.updatePOSPriceInfo = updatePOSPriceInfo;
window.updatePOSTotal = updatePOSTotal;
window.refreshAllData = refreshAllData;

