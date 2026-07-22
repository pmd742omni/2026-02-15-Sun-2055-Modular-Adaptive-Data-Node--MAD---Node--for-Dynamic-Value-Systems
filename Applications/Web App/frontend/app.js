/**
 * MADN Web Application - Core SPA Logic
 * Coordinates state, UI events, and local data persistence.
 */

// --- STATE MANAGEMENT ---
const state = {
  activeView: 'dashboard',
  nodes: {
    node1: { online: false, rssi: -75, alarm: false },
    node2: { online: false, rssi: -80, alarm: false }
  },
  pos: {
    rateZar: 18.00,
    rateZwg: 25.00,
    cartTotalUsd: 10.00,
    tenderedUsd: 10.00,
    tenderedZar: 0.00,
    tenderedZwg: 0.00,
    transactions: []
  }
};

// --- DATA: Bulawayo Historical Monthly Climate Profiles ---
const climateData = [
  { month: "January", rainfall: 95, temp: 21.8, rainyDays: 10 },
  { month: "February", rainfall: 80, temp: 21.2, rainyDays: 8 },
  { month: "March", rainfall: 55, temp: 20.6, rainyDays: 6 },
  { month: "April", rainfall: 25, temp: 19.1, rainyDays: 3 },
  { month: "May", rainfall: 5, temp: 16.3, rainyDays: 1 },
  { month: "June", rainfall: 1, temp: 13.7, rainyDays: 0 },
  { month: "July", rainfall: 0, temp: 13.8, rainyDays: 0 },
  { month: "August", rainfall: 1, temp: 16.1, rainyDays: 0 },
  { month: "September", rainfall: 5, temp: 19.9, rainyDays: 1 },
  { month: "October", rainfall: 25, temp: 21.9, rainyDays: 3 },
  { month: "November", rainfall: 60, temp: 22.0, rainyDays: 7 },
  { month: "December", rainfall: 90, temp: 22.1, rainyDays: 10 }
];

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
  initAuthSystem();
  initNavigation();
  initTime();
  initAgriModule();
  initSecurityModule();
  initPOSModule();
  initAgriDiagnosticTree();
  initSecurityQRScanner();
  initPOSSalesAnalytics();
  
  // Dashboard mock controls
  const btnMock = document.getElementById('btn-mock-telemetry');
  if (btnMock) btnMock.addEventListener('click', runMockNodeActivity);
  
  const btnClear = document.getElementById('btn-clear-db');
  if (btnClear) btnClear.addEventListener('click', resetLocalCache);
  
  // Update summaries
  updateSummaries();
});

// --- NAVIGATION ---
function switchView(target) {
  state.activeView = target;

  // 1. Sidebar items
  document.querySelectorAll('.nav-item-btn').forEach(btn => {
    if (btn.dataset.target === target) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // 2. Horizontal pill tabs
  document.querySelectorAll('.tab-pill-btn').forEach(tab => {
    if (tab.dataset.view === target) {
      tab.classList.add('active');
    } else {
      tab.classList.remove('active');
    }
  });

  // 3. Mobile bottom items
  document.querySelectorAll('.mobile-nav-item').forEach(item => {
    if (item.dataset.target === target) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // 4. Update section visibility explicitly
  document.querySelectorAll('.view-section').forEach(sec => {
    if (sec.id === `view-${target}`) {
      sec.classList.add('active');
      sec.style.display = 'block';
    } else {
      sec.classList.remove('active');
      sec.style.display = 'none';
    }
  });

  // 5. Update sub-navigation pills
  if (typeof updateSubNav === 'function') {
    updateSubNav(target);
  }

  if (target === 'admin') {
    loadAdminPanel();
  }
}

// Expose globally for inline onclick handlers
window.switchView = switchView;
window.switchViewInternal = switchView;

function initNavigation() {
  const sidebarButtons = document.querySelectorAll('.nav-item-btn');
  const horizontalTabs = document.querySelectorAll('.tab-pill-btn');
  const mobileNavItems = document.querySelectorAll('.mobile-nav-item');

  // Attach click listeners to all tab types
  sidebarButtons.forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.target));
  });

  horizontalTabs.forEach(tab => {
    tab.addEventListener('click', () => switchView(tab.dataset.view));
  });

  mobileNavItems.forEach(item => {
    item.addEventListener('click', () => switchView(item.dataset.target));
  });

  mobileNavItems.forEach(item => {
    item.addEventListener('click', () => switchView(item.dataset.target));
  });

  // Collapsible bottom widget triggers
  const posWidget = document.getElementById('widget-toggle-pos');
  if (posWidget) {
    posWidget.addEventListener('click', () => switchView('vpa3'));
  }

  const secWidget = document.getElementById('widget-toggle-security');
  if (secWidget) {
    secWidget.addEventListener('click', () => switchView('vpa2'));
  }

  // Global Search Capsule Input Filtering
  const searchInput = document.getElementById('global-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll('.visitor-table tbody tr, .widget-item-row');
      rows.forEach(r => {
        const txt = r.textContent.toLowerCase();
        if (!q || txt.includes(q)) {
          r.style.display = '';
        } else {
          r.style.display = 'none';
        }
      });
    });
  }
}

// Live Time display
function initTime() {
  const timeVal = document.getElementById('live-time');
  const updateClock = () => {
    const now = new Date();
    timeVal.textContent = now.toTimeString().split(' ')[0].substring(0, 5);
  };
  updateClock();
  setInterval(updateClock, 30000);
}

// --- VPA 1.1: AGRICULTURAL AID SCHEDULER ---
function initAgriModule() {
  const btnCalculate = document.getElementById('btn-calculate-planting');
  
  btnCalculate.addEventListener('click', () => {
    const crop = document.getElementById('crop-select').value;
    const monthIndex = parseInt(document.getElementById('month-select').value);
    const climate = climateData[monthIndex];
    
    // Set climate stats display
    document.getElementById('climate-rain').textContent = `${climate.rainfall} mm`;
    document.getElementById('climate-temp').textContent = `${climate.temp} °C`;
    document.getElementById('climate-days').textContent = `${climate.rainyDays} days`;
    
    const recBox = document.getElementById('planting-recommendation');
    let title = '';
    let description = '';
    let statusClass = 'success'; // success, warning, danger
    
    // Evaluation Logic
    if (crop === 'maize') {
      if (monthIndex === 10 || monthIndex === 11) { // Nov, Dec
        title = 'Optimal Planting Window (Kunisela - Ideal)';
        description = `Maize thrives best in ${climate.month} due to natural seasonal rainfall (${climate.rainfall} mm). Soil humidity will support early growth stage. No additional manual watering is required.`;
        statusClass = 'success';
      } else if (monthIndex === 0 || monthIndex === 1 || monthIndex === 9) { // Jan, Feb, Oct
        title = 'Moderate Risk Window (Watering Required)';
        description = `${climate.month} has moderate rainfall (${climate.rainfall} mm). Supplemental watering is highly recommended during dry spells to maintain soil moisture profiles.`;
        statusClass = 'warning';
      } else { // Winter dry season
        title = 'Critical Irrigation Alert (High Risk)';
        description = `Planting Maize in ${climate.month} is not advised due to low temperatures (${climate.temp}°C) and zero natural rainfall. It requires high daily drip irrigation.`;
        statusClass = 'danger';
      }
    } else if (crop === 'sorghum') {
      if (monthIndex === 9 || monthIndex === 10 || monthIndex === 11 || monthIndex === 0) { // Oct, Nov, Dec, Jan
        title = 'Optimal Crop Selection (Drought Resistant)';
        description = `Sorghum is highly optimized for dry dry-spell soils. Planting in ${climate.month} utilizes ambient heat (${climate.temp}°C) for germination. Highly suitable for Bulawayo microclimate.`;
        statusClass = 'success';
      } else if (monthIndex >= 4 && monthIndex <= 7) { // May - Aug (Dry/Cold)
        title = 'Cold Season Retardation Warn';
        description = `Sorghum is drought resistant but highly vulnerable to winter cold. The average temperature of ${climate.temp}°C in ${climate.month} will stunt growth rates.`;
        statusClass = 'danger';
      } else {
        title = 'Secondary Planting Window';
        description = `Planting in ${climate.month} is viable. Ensure initial seedbeds are watered manually twice a week.`;
        statusClass = 'warning';
      }
    } else if (crop === 'beans') {
      if (monthIndex === 1 || monthIndex === 2 || monthIndex === 8 || monthIndex === 9) { // Feb, Mar, Sep, Oct
        title = 'Ideal Beans Climate Fit';
        description = `Sugar beans require moderate moisture without waterlogging. Planting in ${climate.month} avoids the peak rains of Dec-Jan (preventing pod mold) and winter frost.`;
        statusClass = 'success';
      } else if (monthIndex === 11 || monthIndex === 0) { // Dec, Jan
        title = 'Waterlog & Rot Risk warning';
        description = `High seasonal rainfall in ${climate.month} (${climate.rainfall} mm) raises soil waterlogging risk, which easily rots bean root zones. Ensure proper raised beds.`;
        statusClass = 'warning';
      } else {
        title = 'Dry Cultivation Required';
        description = `Winter bean cultivation requires controlled, shallow watering. Keep soil moist but never soaked.`;
        statusClass = 'warning';
      }
    } else if (crop === 'cabbage') {
      if (monthIndex >= 2 && monthIndex <= 5) { // Mar - Jun
        title = 'Prime Cool Season Vegetable Window';
        description = `Cabbages grow exceptionally well in the cooler winter months (${climate.temp}°C). Drip irrigate consistently to maintain solid head formation.`;
        statusClass = 'success';
      } else if (monthIndex === 11 || monthIndex === 0) {
        title = 'Heat & Pest Infestation Danger';
        description = `High summer heat in ${climate.month} increases vector populations (e.g., diamondback moths). Monitor leaf structures frequently.`;
        statusClass = 'danger';
      } else {
        title = 'Moderate Planting Window';
        description = `Requires consistent irrigation shield. Mulching is highly recommended to preserve soil hydration.`;
        statusClass = 'warning';
      }
    }
    
    recBox.innerHTML = `
      <div class="recommendation-content">
        <h5 class="color-${statusClass}">${title}</h5>
        <p>${description}</p>
      </div>
    `;
    
    // Style update
    recBox.className = `recommendation-box ${statusClass}`;
  });
}

// --- VPA 2.1: PERIMETER SECURITY GATEWAY ---
function initSecurityModule() {
  const btnNode1 = document.getElementById('btn-toggle-node1');
  const btnNode2 = document.getElementById('btn-toggle-node2');
  const btnAlarm1 = document.getElementById('btn-trigger-alarm1');
  const btnAlarm2 = document.getElementById('btn-trigger-alarm2');
  const slider1 = document.getElementById('node1-rssi');
  const slider2 = document.getElementById('node2-rssi');
  
  // Toggle Node 1
  btnNode1.addEventListener('click', () => {
    state.nodes.node1.online = !state.nodes.node1.online;
    if (!state.nodes.node1.online) {
      state.nodes.node1.alarm = false;
    }
    updateNodeUI('node1');
  });

  // Toggle Node 2
  btnNode2.addEventListener('click', () => {
    state.nodes.node2.online = !state.nodes.node2.online;
    if (!state.nodes.node2.online) {
      state.nodes.node2.alarm = false;
    }
    updateNodeUI('node2');
  });

  // Slider controls
  slider1.addEventListener('input', (e) => {
    state.nodes.node1.rssi = parseInt(e.target.value);
    document.getElementById('node1-rssi-val').textContent = `${state.nodes.node1.rssi} dBm`;
    updateNodeUI('node1');
  });

  slider2.addEventListener('input', (e) => {
    state.nodes.node2.rssi = parseInt(e.target.value);
    document.getElementById('node2-rssi-val').textContent = `${state.nodes.node2.rssi} dBm`;
    updateNodeUI('node2');
  });

  // Alarm triggers
  btnAlarm1.addEventListener('click', () => {
    if (state.nodes.node1.online) {
      state.nodes.node1.alarm = !state.nodes.node1.alarm;
      updateNodeUI('node1');
    }
  });

  btnAlarm2.addEventListener('click', () => {
    if (state.nodes.node2.online) {
      state.nodes.node2.alarm = !state.nodes.node2.alarm;
      updateNodeUI('node2');
    }
  });
}

function updateNodeUI(nodeId) {
  const node = state.nodes[nodeId];
  
  // Header Indicator Elements
  const headerInd = document.getElementById(`${nodeId}-indicator`);
  const headerVal = document.getElementById(`${nodeId}-val`);
  
  // Map SVG elements
  const mapDot = document.getElementById(`map-${nodeId}-dot`);
  const mapLink = document.getElementById(`link-${nodeId}`);
  
  // Controls
  const toggleBtn = document.getElementById(`btn-toggle-${nodeId}`);
  const alarmBtn = document.getElementById(`btn-trigger-alarm${nodeId === 'node1' ? '1' : '2'}`);
  const slider = document.getElementById(`${nodeId}-rssi`);
  
  if (node.online) {
    // Enable controls
    slider.disabled = false;
    toggleBtn.textContent = `Disconnect ${nodeId === 'node1' ? 'Node 1' : 'Node 2'}`;
    toggleBtn.classList.add('active');
    alarmBtn.classList.remove('hidden');
    alarmBtn.textContent = node.alarm ? "Acknowledge Trigger" : "Simulate Motion";
    
    // Evaluate signal strength
    let signalLabel = 'Excellent';
    let signalClass = 'online';
    
    if (node.rssi < -85) {
      signalLabel = 'Weak Signal';
      signalClass = 'offline'; // maps to orange warning
      mapLink.className.baseVal = 'map-link offline'; // dotted orange
    } else {
      signalClass = 'online';
      mapLink.className.baseVal = 'map-link online'; // solid green
    }

    if (node.alarm) {
      headerInd.className = 'node-indicator danger';
      headerVal.textContent = 'INTRUSION ALERT!';
      headerVal.className = 'status-value color-danger';
      
      mapDot.className.baseVal = 'node-center danger';
      mapLink.className.baseVal = 'map-link danger';
    } else {
      headerInd.className = `node-indicator ${signalClass === 'online' ? 'online' : 'offline'}`;
      headerVal.textContent = `${signalLabel} (${node.rssi} dBm)`;
      headerVal.className = 'status-value';
      
      mapDot.className.baseVal = 'node-center online';
    }
  } else {
    // Offline State
    slider.disabled = true;
    toggleBtn.textContent = `Connect ${nodeId === 'node1' ? 'Node 1' : 'Node 2'}`;
    toggleBtn.classList.remove('active');
    alarmBtn.classList.add('hidden');
    
    headerInd.className = 'node-indicator offline';
    headerVal.textContent = 'Offline';
    headerVal.className = 'status-value';
    
    mapDot.className.baseVal = 'node-center offline';
    mapLink.className.baseVal = 'map-link offline';
  }

  // Update active counter
  const activeCount = (state.nodes.node1.online ? 1 : 0) + (state.nodes.node2.online ? 1 : 0);
  document.getElementById('security-active-pill').textContent = `${activeCount} Node${activeCount !== 1 ? 's' : ''} Active`;
  updateSummaries();
}

// --- VPA 3.1 & 3.3: POINT OF SALE TERMINAL & INVENTORY ---
let posCart = [];
let posInventory = [];

function initPOSModule() {
  const inputDueUsd = document.getElementById('cart-amount-usd');
  const inputZar = document.getElementById('rate-zar');
  const inputZwg = document.getElementById('rate-zwg');
  const inputTenderUsd = document.getElementById('tender-usd');
  const inputTenderZar = document.getElementById('tender-zar');
  const inputTenderZwg = document.getElementById('tender-zwg');
  const btnProcess = document.getElementById('btn-process-sale');
  
  // Load products list and inventory lists
  loadInventory();
  
  // Cart Add Button Hook
  const btnAdd = document.getElementById('btn-pos-add-item');
  if (btnAdd) {
    btnAdd.addEventListener('click', () => {
      const select = document.getElementById('pos-product-select');
      const qtyInput = document.getElementById('pos-product-qty');
      const itemId = select.value;
      const qty = parseFloat(qtyInput.value) || 0;
      
      if (!itemId || qty <= 0) {
        alert("Please select a valid product and specify a quantity.");
        return;
      }
      
      addCartItem(itemId, qty);
      qtyInput.value = 1;
    });
  }
  
  // Real-time calculations on input focus change
  const triggerRec = () => {
    recalculateTender(
      parseFloat(inputDueUsd.value) || 0,
      parseFloat(inputZar.value) || 18,
      parseFloat(inputZwg.value) || 25,
      parseFloat(inputTenderUsd.value) || 0,
      parseFloat(inputTenderZar.value) || 0,
      parseFloat(inputTenderZwg.value) || 0
    );
  };
  
  [inputDueUsd, inputZar, inputZwg, inputTenderUsd, inputTenderZar, inputTenderZwg].forEach(el => {
    el.addEventListener('input', triggerRec);
  });
  
  // Check for auto-recovery of cart on startup
  setTimeout(loadPOSCartFromCache, 500);
  
  btnProcess.addEventListener('click', async () => {
    const dueUsd = parseFloat(inputDueUsd.value) || 0;
    const rateZar = parseFloat(inputZar.value) || 18;
    const rateZwg = parseFloat(inputZwg.value) || 25;
    const tenderUsd = parseFloat(inputTenderUsd.value) || 0;
    const tenderZar = parseFloat(inputTenderZar.value) || 0;
    const tenderZwg = parseFloat(inputTenderZwg.value) || 0;
    
    if (posCart.length === 0) {
      alert("Cart is empty! Add products to the cart first.");
      return;
    }
    
    const outcome = recalculateTender(dueUsd, rateZar, rateZwg, tenderUsd, tenderZar, tenderZwg);
    
    if (!outcome.paid) {
      alert("Deficit in payment splits. Please tender enough cash options.");
      return;
    }
    
    // Prepare API checkout models
    const clientReqId = 'tx_' + generateUUIDv4(); // Unique transaction idempotency key
    
    const tendersList = [];
    if (tenderUsd > 0) tendersList.push({ currency: "USD", amount_tendered: tenderUsd, exchange_rate: 1.0, amount_usd_equiv: tenderUsd });
    if (tenderZar > 0) tendersList.push({ currency: "ZAR", amount_tendered: tenderZar, exchange_rate: rateZar, amount_usd_equiv: tenderZar / rateZar });
    if (tenderZwg > 0) tendersList.push({ currency: "ZWG", amount_tendered: tenderZwg, exchange_rate: rateZwg, amount_usd_equiv: tenderZwg / rateZwg });
    
    const itemsList = posCart.map(c => ({
      inventory_id: c.id,
      quantity: c.quantity,
      price_usd_at_sale: c.price_usd
    }));
    
    try {
      btnProcess.disabled = true;
      btnProcess.textContent = "Processing Checkout...";
      
      const res = await secureFetch("/api/pos/checkout", {
        method: "POST",
        headers: {
          "X-Client-Request-Id": clientReqId
        },
        body: JSON.stringify({
          total_due_usd: dueUsd,
          tenders: tendersList,
          items: itemsList
        })
      });
      
      const data = await res.json();
      if (!res.ok) {
        alert(`Checkout Transaction failed: ${data.detail}`);
        btnProcess.disabled = false;
        btnProcess.textContent = "Commit Sale & Calculate Change";
        return;
      }
      
      // Success: Log transaction locally
      const newTx = {
        id: data.transaction_id,
        time: new Date().toLocaleTimeString(),
        dueUsd: dueUsd,
        tenderedUsdEquiv: outcome.tenderedUsd,
        changeUsd: outcome.changeUsd,
        paidUsd: tenderUsd,
        paidZar: tenderZar,
        paidZwg: tenderZwg
      };
      
      state.pos.transactions.unshift(newTx);
      localStorage.setItem('madn_transactions', JSON.stringify(state.pos.transactions));
      
      // Clear cart
      clearCart();
      
      // Reload inventory counts
      await loadInventory();
      
      // Reset input fields
      inputTenderUsd.value = 0;
      inputTenderZar.value = 0;
      inputTenderZwg.value = 0;
      triggerRec();
      
      renderTransactionHistory();
      
      btnProcess.disabled = false;
      btnProcess.textContent = "Transaction Logged! ✓";
      btnProcess.classList.add('active');
      setTimeout(() => {
        btnProcess.textContent = "Commit Sale & Calculate Change";
        btnProcess.classList.remove('active');
      }, 2000);
      
    } catch (err) {
      alert(`Checkout failed: ${err.message}`);
      btnProcess.disabled = false;
      btnProcess.textContent = "Commit Sale & Calculate Change";
    }
  });

  // Load from local storage history
  const cachedTx = localStorage.getItem('madn_transactions');
  if (cachedTx) {
    state.pos.transactions = JSON.parse(cachedTx);
    renderTransactionHistory();
  }
}

function recalculateTender(dueUsd, rateZar, rateZwg, tenderUsd, tenderZar, tenderZwg) {
  // Convert due value to multiple currencies
  document.getElementById('rec-due-usd').textContent = `$${dueUsd.toFixed(2)}`;
  document.getElementById('rec-due-zar').textContent = `R${(dueUsd * rateZar).toFixed(2)}`;
  document.getElementById('rec-due-zwg').textContent = `${(dueUsd * rateZwg).toFixed(2)} ZWG`;
  
  // Calculate total tendered value in USD equivalents
  const zarTenderedInUsd = tenderZar / rateZar;
  const zwgTenderedInUsd = tenderZwg / rateZwg;
  const totalTenderedUsd = tenderUsd + zarTenderedInUsd + zwgTenderedInUsd;
  
  document.getElementById('rec-tendered-usd').textContent = `$${totalTenderedUsd.toFixed(2)}`;
  
  const changeBox = document.getElementById('rec-change-box');
  const changeTitle = document.getElementById('change-title');
  const changeDesc = document.getElementById('change-desc');
  const changeSplits = document.getElementById('change-currency-split');
  
  let changeUsd = totalTenderedUsd - dueUsd;
  
  let outcome = {
    paid: false,
    tenderedUsd: totalTenderedUsd,
    changeUsd: 0
  };

  if (totalTenderedUsd >= dueUsd) {
    outcome.paid = true;
    outcome.changeUsd = changeUsd;
    
    changeBox.className = 'change-status-box success';
    
    if (changeUsd > 0.009) {
      changeTitle.textContent = 'Change Due';
      changeDesc.textContent = `Customer overpaid by $${changeUsd.toFixed(2)} USD (equivalent).`;
      changeSplits.classList.remove('hidden');
      
      // Calculate split options
      document.getElementById('change-opt-usd').textContent = `$${changeUsd.toFixed(2)}`;
      document.getElementById('change-opt-zar').textContent = `R${(changeUsd * rateZar).toFixed(2)}`;
      document.getElementById('change-opt-zwg').textContent = `${(changeUsd * rateZwg).toFixed(2)} ZWG`;
    } else {
      changeTitle.textContent = 'Paid in Full';
      changeDesc.textContent = 'Exact amount paid. No change required.';
      changeSplits.classList.add('hidden');
    }
  } else {
    // Underpaid
    const deficitUsd = dueUsd - totalTenderedUsd;
    changeBox.className = 'change-status-box danger';
    changeTitle.textContent = 'Payment Incomplete';
    changeDesc.textContent = `Underpaid by $${deficitUsd.toFixed(2)} USD (Needs R${(deficitUsd * rateZar).toFixed(2)} or ${(deficitUsd * rateZwg).toFixed(2)} ZWG).`;
    changeSplits.classList.add('hidden');
  }

  updateSummaries();
  return outcome;
}

function renderTransactionHistory() {
  const container = document.getElementById('pos-recent-entries');
  if (state.pos.transactions.length === 0) {
    container.innerHTML = `<p class="neutral-message">No transactions recorded in this session.</p>`;
    return;
  }
  
  container.innerHTML = state.pos.transactions.map(tx => `
    <div class="log-entry">
      <div class="log-entry-info">
        <span class="log-entry-time">${tx.time}</span>
        <span class="log-entry-lbl">Sale Checkout</span>
      </div>
      <span class="log-entry-total">$${tx.dueUsd.toFixed(2)}</span>
    </div>
  `).join('');
}

// --- UTILITIES / OVERLAYS ---
function runMockNodeActivity() {
  // Turn on node1 and node2 with random signals and alarm toggle
  state.nodes.node1.online = true;
  state.nodes.node1.rssi = Math.floor(Math.random() * ( -30 - -95 ) + -95);
  state.nodes.node1.alarm = Math.random() > 0.7; // 30% alert chance
  
  state.nodes.node2.online = true;
  state.nodes.node2.rssi = Math.floor(Math.random() * ( -30 - -95 ) + -95);
  state.nodes.node2.alarm = Math.random() > 0.8;
  
  document.getElementById('node1-rssi').value = state.nodes.node1.rssi;
  document.getElementById('node1-rssi-val').textContent = `${state.nodes.node1.rssi} dBm`;
  
  document.getElementById('node2-rssi').value = state.nodes.node2.rssi;
  document.getElementById('node2-rssi-val').textContent = `${state.nodes.node2.rssi} dBm`;

  updateNodeUI('node1');
  updateNodeUI('node2');
}

function resetLocalCache() {
  if (confirm("This will clear all transactions in your local browser storage. Are you sure?")) {
    localStorage.removeItem('madn_transactions');
    state.pos.transactions = [];
    renderTransactionHistory();
    updateSummaries();
  }
}

function updateSummaries() {
  // Update dashboard overview stats
  const activeCount = (state.nodes.node1.online ? 1 : 0) + (state.nodes.node2.online ? 1 : 0);
  document.getElementById('security-summary').textContent = `${activeCount} nodes active on map`;
  
  const txCount = state.pos.transactions.length;
  document.getElementById('pos-summary').textContent = `${txCount} local sales registered`;
  
  // Trigger update of POS analytics charts and KPIs
  if (typeof updatePOSAnalytics === 'function') {
    updatePOSAnalytics();
  }
}

// --- VPA 1.2: INTERACTIVE SYMPTOM DIAGNOSTIC TREE ---
const diagnosticTree = {
  root: {
    question: "Select the agricultural asset type you are troubleshooting:",
    options: [
      { text: "Crop Issues (Yellowing, Wilting)", next: "crop_symptoms" },
      { text: "Livestock Issues (Lethargy, Coughing)", next: "livestock_symptoms" }
    ]
  },
  crop_symptoms: {
    question: "What primary visual symptom do you observe on the crop?",
    options: [
      { text: "Yellowing or spots on leaves", next: "crop_yellowing" },
      { text: "Wilting stems or general collapse", next: "crop_wilting" }
    ]
  },
  crop_yellowing: {
    question: "Are the crops also showing severely stunted growth?",
    options: [
      { text: "Yes, stunted and pale green leaves", diagnosis: "Nitrogen Deficiency", remedy: "Apply organic manure, nitrogen-rich compost, or nitrogenous fertilizer to restore soil nitrogen levels.", statusClass: "warning" },
      { text: "No, mostly leaf-spots with concentric rings", diagnosis: "Leaf Spot Fungus (Early Blight)", remedy: "Prune infected lower foliage, avoid overhead watering to keep leaves dry, and apply a local copper-based organic fungicide.", statusClass: "danger" }
    ]
  },
  crop_wilting: {
    question: "Do you see root mold, grey dust, or decay at the base?",
    options: [
      { text: "Yes, base stem looks soft and decayed", diagnosis: "Root / Stem Rot (Waterlogging)", remedy: "Improve plot drainage immediately. Reduce watering frequency, remove severely decayed stalks, and let the soil dry out.", statusClass: "danger" },
      { text: "No, soil is dry and dusty", diagnosis: "Underwatering / Dehydration", remedy: "Establish consistent irrigation cycles using the Ukunisela parameters. Apply mulch around crop bases to retain soil moisture.", statusClass: "warning" }
    ]
  },
  livestock_symptoms: {
    question: "What primary symptom do you observe in the animal?",
    options: [
      { text: "Lethargy, weakness, or pale gums", next: "livestock_lethargy" },
      { text: "Coughing, nasal discharge, or fast breathing", next: "livestock_coughing" }
    ]
  },
  livestock_lethargy: {
    question: "Are the animal's gums and eye membranes unusually pale?",
    options: [
      { text: "Yes, very pale (anemia signature)", diagnosis: "Wireworm Parasite (Haemonchus)", remedy: "Isolate the animal. Administer target broad-spectrum dewormer (anthelmintic) immediately and check pasture rotation schedule.", statusClass: "danger" },
      { text: "No, but body temperature is high", diagnosis: "Tick-Borne Fever / Infection", remedy: "Check coat for active ticks. Treat with a local tick dip/pour-on solution. Consult local veterinary brief for oxytetracycline administration.", statusClass: "warning" }
    ]
  },
  livestock_coughing: {
    question: "Does the animal have a high fever or shallow, rapid breathing?",
    options: [
      { text: "Yes, rapid chest movement and high fever", diagnosis: "Bovine Pneumonia / BRD", remedy: "Move animal to a dry, draught-free quarantine shelter. Provide warm water and dry feed. Consult vet immediately for antibiotic treatment.", statusClass: "danger" },
      { text: "No, breathing is normal but sneezing", diagnosis: "Dust / Environmental Irritation", remedy: "Clean feed troughs of dust. Dampen dry hay feed slightly, and ensure the paddock has adequate cross-ventilation.", statusClass: "success" }
    ]
  }
};

let currentDiagNode = 'root';
let diagHistory = [];

function initAgriDiagnosticTree() {
  renderDiagnosticStep();
  
  document.getElementById('btn-diag-back').addEventListener('click', () => {
    if (diagHistory.length > 0) {
      currentDiagNode = diagHistory.pop();
      renderDiagnosticStep();
    }
  });
  
  document.getElementById('btn-diag-reset').addEventListener('click', () => {
    currentDiagNode = 'root';
    diagHistory = [];
    renderDiagnosticStep();
    
    // Reset outcome box
    const outcomeBox = document.getElementById('diag-outcome-box');
    outcomeBox.className = 'recommendation-box';
    outcomeBox.innerHTML = `<p class="neutral-message">Complete the diagnostic questionnaire steps in the interaction zone to view the generated plant/animal diagnosis and recommended treatment procedures.</p>`;
  });
}

function renderDiagnosticStep() {
  const stepTitle = document.getElementById('diag-step-title');
  const stepBody = document.getElementById('diag-wizard-body');
  const navFooter = document.getElementById('diag-nav-footer');
  
  // Show / hide back/reset footer based on depth
  if (diagHistory.length > 0) {
    navFooter.classList.remove('hidden');
  } else {
    navFooter.classList.add('hidden');
  }
  
  const node = diagnosticTree[currentDiagNode];
  stepTitle.textContent = currentDiagNode === 'root' ? "Select Diagnostics Category" : "Diagnostic Question";
  
  let html = `
    <p class="wizard-help-text" style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 20px;">${node.question}</p>
    <div class="option-buttons-grid" style="display: flex; flex-direction: column; gap: 12px;">
  `;
  
  node.options.forEach((opt, idx) => {
    html += `
      <button class="action-btn text-left diag-opt-btn" data-index="${idx}" style="text-align: left;">
        ${opt.text}
      </button>
    `;
  });
  
  html += `</div>`;
  stepBody.innerHTML = html;
  
  // Add click listeners to buttons
  const buttons = stepBody.querySelectorAll('.diag-opt-btn');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.index);
      const chosenOpt = node.options[idx];
      
      if (chosenOpt.next) {
        diagHistory.push(currentDiagNode);
        currentDiagNode = chosenOpt.next;
        renderDiagnosticStep();
      } else {
        // We reached a leaf node (diagnosis outcome)
        displayDiagnosisOutcome(chosenOpt);
      }
    });
  });
}

function displayDiagnosisOutcome(outcome) {
  const outcomeBox = document.getElementById('diag-outcome-box');
  outcomeBox.className = `recommendation-box ${outcome.statusClass}`;
  
  outcomeBox.innerHTML = `
    <div class="recommendation-content" style="width: 100%;">
      <h5 class="color-${outcome.statusClass}" style="font-weight: 700; margin-bottom: 8px;">Diagnosis: ${outcome.diagnosis}</h5>
      <p style="margin-bottom: 12px;">${outcome.remedy}</p>
      <div style="font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid var(--border-light); padding-top: 8px; margin-top: 8px;">
        Severity rating: <span class="color-${outcome.statusClass}" style="font-weight: 600; text-transform: uppercase;">${outcome.statusClass}</span>
      </div>
    </div>
  `;
  
  // Disable options or show success message in wizard body
  const stepBody = document.getElementById('diag-wizard-body');
  stepBody.innerHTML = `
    <div style="text-align: center; padding: 20px 0;">
      <span style="font-size: 3rem; display: block; margin-bottom: 12px;">✓</span>
      <h5 class="color-success" style="margin-bottom: 6px;">Diagnosis Complete</h5>
      <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 280px; margin: 0 auto 16px;">The diagnostic tree has successfully evaluated your inputs. See details in the viewing zone.</p>
    </div>
  `;
  document.getElementById('diag-step-title').textContent = "Troubleshooting Finished";
}

// --- VPA 2.2: LOCAL QR CODE BADGE GENERATOR & SCANNER ---
let lastGeneratedQRToken = '';
let scannedVisitorCount = 0;
let scannedVisitorsArray = [];

function initSecurityQRScanner() {
  const btnGenerate = document.getElementById('btn-generate-badge');
  const btnScanSim = document.getElementById('btn-scan-sim');
  
  btnGenerate.addEventListener('click', () => {
    const name = document.getElementById('visitor-name').value.trim();
    const id = document.getElementById('visitor-id').value.trim();
    const hours = parseInt(document.getElementById('visitor-hours').value) || 4;
    
    if (!name || !id) {
      alert("Please enter both the Guest Name and National ID Number to issue a badge.");
      return;
    }
    
    // Construct payload
    const payload = {
      name: name,
      id: id,
      duration: hours,
      issued: Date.now()
    };
    
    // Encode as Base64 to simulate encrypted offline token
    const token = btoa(JSON.stringify(payload));
    lastGeneratedQRToken = token;
    
    // Renders custom QR code representation on Canvas
    drawQRBadgeCanvas(token);
    
    // Update display box
    document.getElementById('qr-payload-val').textContent = token.substring(0, 48) + "...";
    document.getElementById('qr-result-box').classList.remove('hidden');
    
    // Small success effect
    btnGenerate.textContent = "Credential Issued! ✓";
    btnGenerate.classList.add('active');
    setTimeout(() => {
      btnGenerate.textContent = "Generate Digital QR Badge";
      btnGenerate.classList.remove('active');
    }, 1500);
  });
  
  btnScanSim.addEventListener('click', () => {
    if (!lastGeneratedQRToken) {
      alert("No digital QR badge has been generated yet. Please pre-register a guest first on the left.");
      return;
    }
    
    // Simulates decoding of QR code payload
    try {
      const decodedString = atob(lastGeneratedQRToken);
      const visitorObj = JSON.parse(decodedString);
      
      // Validate expiry
      const checkInTime = Date.now();
      const allocatedDurationMs = visitorObj.duration * 60 * 60 * 1000;
      const expired = (checkInTime - visitorObj.issued) > allocatedDurationMs;
      
      const newScan = {
        name: visitorObj.name,
        id: visitorObj.id,
        checkInStr: new Date(checkInTime).toLocaleTimeString(),
        duration: `${visitorObj.duration} hrs`,
        status: expired ? "Expired" : "Authorized",
        statusClass: expired ? "danger" : "success"
      };
      
      // Save scan to list
      scannedVisitorsArray.unshift(newScan);
      scannedVisitorCount = scannedVisitorsArray.length;
      document.getElementById('visitor-count-badge').textContent = `${scannedVisitorCount} Guest${scannedVisitorCount !== 1 ? 's' : ''} Scanned`;
      
      // Redraw table
      renderVisitorLedger();
      
      // Highlight viewpoint success flash
      const viewfinder = document.querySelector('.scanner-viewfinder');
      viewfinder.style.borderColor = expired ? 'var(--danger)' : 'var(--success)';
      viewfinder.style.backgroundColor = expired ? 'var(--danger-glow)' : 'var(--success-glow)';
      
      setTimeout(() => {
        viewfinder.style.borderColor = 'var(--accent)';
        viewfinder.style.backgroundColor = 'var(--surface-card)';
      }, 1000);
      
    } catch (err) {
      alert("Error scanning/decoding credential token: Invalid Payload.");
    }
  });
}

function drawQRBadgeCanvas(tokenText) {
  const canvas = document.getElementById('qr-code-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  
  // Clear canvas to white
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, width, height);
  
  // Draw finder patterns (corners)
  drawQRCornerPattern(ctx, 10, 10, 32); // Top Left
  drawQRCornerPattern(ctx, width - 42, 10, 32); // Top Right
  drawQRCornerPattern(ctx, 10, height - 42, 32); // Bottom Left
  
  // Generate pseudo-random matrix blocks using hash of token text
  let hashVal = 0;
  for (let i = 0; i < tokenText.length; i++) {
    hashVal = (hashVal << 5) - hashVal + tokenText.charCodeAt(i);
    hashVal = hashVal & hashVal; // Convert to 32bit integer
  }
  
  // Grid size
  const gridSize = 16;
  const cellWidth = (width - 20) / gridSize;
  const cellHeight = (height - 20) / gridSize;
  
  ctx.fillStyle = "#000000";
  for (let row = 0; row < gridSize; row++) {
    for (let col = 0; col < gridSize; col++) {
      // Exclude corner finder zones (first 5 and last 5 columns/rows in corners)
      const isTopLeft = row < 5 && col < 5;
      const isTopRight = row < 5 && col >= gridSize - 5;
      const isBottomLeft = row >= gridSize - 5 && col < 5;
      
      if (!isTopLeft && !isTopRight && !isBottomLeft) {
        // Deterministic PRNG check
        const bitVal = Math.sin(hashVal + (row * 13) + (col * 37)) > 0;
        if (bitVal) {
          ctx.fillRect(10 + col * cellWidth, 10 + row * cellHeight, cellWidth - 0.5, cellHeight - 0.5);
        }
      }
    }
  }
}

function drawQRCornerPattern(ctx, x, y, size) {
  ctx.fillStyle = "#000000";
  ctx.fillRect(x, y, size, size); // Outer black square
  
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(x + size/6, y + size/6, size * 2/3, size * 2/3); // Inner white square
  
  ctx.fillStyle = "#000000";
  ctx.fillRect(x + size/3, y + size/3, size/3, size/3); // Center black square
}

function renderVisitorLedger() {
  const tbody = document.getElementById('visitor-ledger-body');
  if (scannedVisitorsArray.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" style="padding: 15px; text-align: center; color: var(--text-muted); font-style: italic;">No visitors checked in today.</td>
      </tr>
    `;
    return;
  }
  
  tbody.innerHTML = scannedVisitorsArray.map(vis => `
    <tr style="border-bottom: 1px solid var(--border-light);">
      <td style="padding: 10px; font-weight: 500; color: var(--text-main);">${vis.name}</td>
      <td style="padding: 10px; color: var(--text-main);">${vis.checkInStr}</td>
      <td style="padding: 10px; color: var(--text-main);">${vis.duration}</td>
      <td style="padding: 10px;">
        <span class="pill-badge ${vis.statusClass}" style="font-size: 0.7rem; padding: 2px 8px;">${vis.status}</span>
      </td>
    </tr>
  `).join('');
}

// --- VPA 3.2: INTERACTIVE SALES ANALYTICS & VISUALIZER ---
function initPOSSalesAnalytics() {
  // Draw initial charts
  updatePOSAnalytics();
}

function updatePOSAnalytics() {
  const txHistory = state.pos.transactions;
  const countSpan = document.getElementById('pos-analytics-badge');
  const revenueSpan = document.getElementById('kpi-total-revenue');
  const salesSpan = document.getElementById('kpi-total-sales');
  
  const distUsdSpan = document.getElementById('dist-usd-val');
  const distZarSpan = document.getElementById('dist-zar-val');
  const distZwgSpan = document.getElementById('dist-zwg-val');
  
  if (!countSpan || !revenueSpan || !salesSpan) return;
  
  // Calculate total counts
  const totalCount = txHistory.length;
  countSpan.textContent = `${totalCount} sale${totalCount !== 1 ? 's' : ''} logged`;
  salesSpan.textContent = totalCount;
  
  // Calculate total revenue & reserves splits
  let totalRevenueUsd = 0;
  let cashUsd = 0;
  let cashZar = 0;
  let cashZwg = 0;
  
  txHistory.forEach(tx => {
    totalRevenueUsd += tx.dueUsd;
    // Accumulate cash tender splits (default to 0 if undefined for old session cache)
    cashUsd += (tx.paidUsd || 0);
    cashZar += (tx.paidZar || 0);
    cashZwg += (tx.paidZwg || 0);
  });
  
  revenueSpan.textContent = `$${totalRevenueUsd.toFixed(2)}`;
  distUsdSpan.textContent = `$${cashUsd.toFixed(2)}`;
  distZarSpan.textContent = `R${cashZar.toFixed(2)}`;
  distZwgSpan.textContent = `${cashZwg.toFixed(2)} ZWG`;
  
  // Render sales graph canvas
  drawSalesChartCanvas(txHistory);
}

function drawSalesChartCanvas(txs) {
  const canvas = document.getElementById('sales-chart-canvas');
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  
  // Clear canvas
  ctx.clearRect(0, 0, w, h);
  
  // Create beautiful background dark glow
  ctx.fillStyle = "#161b22"; // matches var(--surface-card)
  ctx.fillRect(0, 0, w, h);
  
  // Setup padding
  const paddingLeft = 50;
  const paddingRight = 30;
  const paddingTop = 30;
  const paddingBottom = 40;
  
  const graphWidth = w - paddingLeft - paddingRight;
  const graphHeight = h - paddingTop - paddingBottom;
  
  // Draw Axes
  ctx.strokeStyle = "rgba(255, 255, 255, 0.1)"; // grid color
  ctx.lineWidth = 1;
  
  ctx.beginPath();
  // X axis
  ctx.moveTo(paddingLeft, h - paddingBottom);
  ctx.lineTo(w - paddingRight, h - paddingBottom);
  // Y axis
  ctx.moveTo(paddingLeft, paddingTop);
  ctx.lineTo(paddingLeft, h - paddingBottom);
  ctx.stroke();
  
  // Get data points (either real transactions sorted chronologically, or mock fallback points if empty)
  let dataPoints = [];
  
  if (txs.length > 0) {
    // Reverse to chronological order, slice last 6 transactions
    const chronological = [...txs].reverse().slice(-6);
    dataPoints = chronological.map(tx => ({
      label: tx.time.substring(0, 5), // HH:MM
      value: tx.dueUsd
    }));
  } else {
    // Empty cache fallback: draw mock historical slots showing zero line
    dataPoints = [
      { label: "08:00", value: 0 },
      { label: "10:00", value: 0 },
      { label: "12:00", value: 0 },
      { label: "14:00", value: 0 },
      { label: "16:00", value: 0 }
    ];
  }
  
  // Draw Grid Lines (Y axis splits)
  const ySplits = 4;
  let maxVal = Math.max(...dataPoints.map(d => d.value), 10); // scale upper boundary to max or min 10
  maxVal = Math.ceil(maxVal / 10) * 10; // round up to multiple of 10
  
  ctx.textAlign = "right";
  ctx.textBaseline = "middle";
  ctx.fillStyle = "rgba(255, 255, 255, 0.5)"; // text secondary
  ctx.font = "0.75rem sans-serif";
  
  for (let i = 0; i <= ySplits; i++) {
    const val = (maxVal / ySplits) * i;
    const y = h - paddingBottom - (val / maxVal) * graphHeight;
    
    // Draw grid horizontal line
    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(w - paddingRight, y);
    ctx.stroke();
    
    // Draw Y labels
    ctx.fillText(`$${val.toFixed(0)}`, paddingLeft - 8, y);
  }
  
  // Plot coordinates
  const pointsCount = dataPoints.length;
  const xSplit = graphWidth / (pointsCount - 1 || 1);
  
  let coords = [];
  dataPoints.forEach((pt, idx) => {
    const x = paddingLeft + idx * xSplit;
    const y = h - paddingBottom - (pt.value / maxVal) * graphHeight;
    coords.push({ x: x, y: y, label: pt.label, value: pt.value });
  });
  
  // Draw Fill Area (Gradient)
  if (coords.length > 1) {
    const areaGlow = ctx.createLinearGradient(0, paddingTop, 0, h - paddingBottom);
    areaGlow.addColorStop(0, "rgba(0, 240, 255, 0.15)"); // matches cyan accent glow
    areaGlow.addColorStop(1, "rgba(0, 240, 255, 0.0)");
    
    ctx.fillStyle = areaGlow;
    ctx.beginPath();
    ctx.moveTo(coords[0].x, h - paddingBottom);
    coords.forEach(c => {
      ctx.lineTo(c.x, c.y);
    });
    ctx.lineTo(coords[coords.length - 1].x, h - paddingBottom);
    ctx.closePath();
    ctx.fill();
  }
  
  // Draw Graph Lines
  ctx.strokeStyle = "#00f0ff"; // Accent Cyan
  ctx.lineWidth = 3;
  ctx.shadowColor = "rgba(0, 240, 255, 0.4)";
  ctx.shadowBlur = 8;
  
  ctx.beginPath();
  coords.forEach((c, idx) => {
    if (idx === 0) {
      ctx.moveTo(c.x, c.y);
    } else {
      ctx.lineTo(c.x, c.y);
    }
  });
  ctx.stroke();
  
  // Reset shadow effects for labels and markers
  ctx.shadowBlur = 0;
  
  // Draw coordinate points (dots) and X labels
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  
  coords.forEach(c => {
    // White outer, Cyan inner marker
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(c.x, c.y, 5, 0, Math.PI * 2);
    ctx.fill();
    
    ctx.fillStyle = "#00f0ff";
    ctx.beginPath();
    ctx.arc(c.x, c.y, 3, 0, Math.PI * 2);
    ctx.fill();
    
    // Draw X axis label
    ctx.fillStyle = "rgba(255, 255, 255, 0.5)";
    ctx.fillText(c.label, c.x, h - paddingBottom + 10);
    
    // Draw value text above dots if > 0
    if (c.value > 0) {
      ctx.fillStyle = "#ffffff";
      ctx.textBaseline = "bottom";
      ctx.fillText(`$${c.value.toFixed(2)}`, c.x, c.y - 8);
    }
  });
}

// --- CORE COOKIES & SECURE FETCH HELPERS ---
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

let pendingStepUpResolve = null;
let pendingStepUpReject = null;

async function secureFetch(url, options = {}) {
  // Read CSRF token from cookie
  const csrfToken = getCookie("csrf_token");
  if (csrfToken) {
    if (!options.headers) options.headers = {};
    options.headers["X-CSRF-Token"] = csrfToken;
    options.headers["Content-Type"] = "application/json";
  }
  
  try {
    const response = await fetch(url, options);
    if (response.status === 401) {
      showLoginOverlay();
      throw new Error("Unauthorized");
    }
    if (response.status === 403) {
      const errData = await response.json();
      const detail = errData.detail || "";
      if (detail.includes("step-up") || detail.includes("elevate")) {
        // Trigger Step-up modal and delay execution
        return new Promise((resolve, reject) => {
          pendingStepUpResolve = () => resolve(secureFetch(url, options));
          pendingStepUpReject = () => reject(new Error("Step-up cancelled"));
          showStepUpModal();
        });
      }
      throw new Error(detail);
    }
    return response;
  } catch (err) {
    throw err;
  }
}

// --- AUTHENTICATION STATE ACTIONS ---

function showLoginOverlay() {
  document.getElementById('auth-overlay').style.display = 'flex';
  document.getElementById('card-login').style.display = 'block';
  document.getElementById('card-register').style.display = 'none';
  document.getElementById('user-profile-drawer').style.display = 'none';
  document.getElementById('nav-admin').style.display = 'none';
  setTimeout(() => document.getElementById('login-username').focus(), 50);
}

function hideLoginOverlay() {
  document.getElementById('auth-overlay').style.display = 'none';
  document.getElementById('user-profile-drawer').style.display = 'flex';
}

function showStepUpModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-step-up').style.display = 'block';
  document.getElementById('modal-change-password').style.display = 'none';
  document.getElementById('modal-mfa-setup').style.display = 'none';
  document.getElementById('step-up-password').value = '';
  document.getElementById('step-up-error').style.display = 'none';
  setTimeout(() => document.getElementById('step-up-password').focus(), 50);
}

function hideModals() {
  document.getElementById('modal-overlay').style.display = 'none';
  document.getElementById('modal-step-up').style.display = 'none';
  document.getElementById('modal-change-password').style.display = 'none';
  document.getElementById('modal-mfa-setup').style.display = 'none';
  
  if (pendingStepUpReject) {
    pendingStepUpReject();
    pendingStepUpResolve = null;
    pendingStepUpReject = null;
  }
}

async function checkActiveSession() {
  try {
    const res = await secureFetch("/api/auth/session");
    if (res.ok) {
      const user = await res.json();
      state.user = user;
      
      // Update UI displays
      document.getElementById('profile-username').textContent = user.username;
      document.getElementById('profile-role').textContent = user.role.toUpperCase();
      document.getElementById('user-avatar-pic').textContent = user.username[0].toUpperCase();
      
      hideLoginOverlay();
      
      // Show admin controls conditionally for administrator role
      const navAdmin = document.getElementById('nav-admin');
      const tabAdmin = document.getElementById('tab-admin');
      if (user.role === 'admin') {
        if (navAdmin) navAdmin.style.display = 'flex';
        if (tabAdmin) tabAdmin.style.display = 'inline-block';
      } else {
        if (navAdmin) navAdmin.style.display = 'none';
        if (tabAdmin) tabAdmin.style.display = 'none';
      }
      
      // Force change password overlay if must_change_password flag is set
      if (user.must_change_password) {
        document.getElementById('modal-overlay').style.display = 'flex';
        document.getElementById('modal-change-password').style.display = 'block';
        document.getElementById('btn-change-pw-cancel').style.display = 'none'; // hide cancel
        document.getElementById('change-pw-subtitle').textContent = "CRITICAL: You are using bootstrap credentials. You must update your password before accessing other features.";
        document.getElementById('change-pw-subtitle').style.color = 'var(--danger)';
        setTimeout(() => document.getElementById('change-pw-current').focus(), 50);
      } else {
        document.getElementById('btn-change-pw-cancel').style.display = 'inline-block';
        document.getElementById('change-pw-subtitle').style.color = 'var(--text-muted)';
      }
    }
  } catch (err) {
    showLoginOverlay();
  }
}

function initAuthSystem() {
  const linkRegister = document.getElementById('link-goto-register');
  const linkLogin = document.getElementById('link-goto-login');
  
  const btnLogin = document.getElementById('btn-login-submit');
  const btnRegister = document.getElementById('btn-register-submit');
  const btnLogout = document.getElementById('btn-logout');
  
  const btnOpenMFA = document.getElementById('btn-open-mfa');
  const btnOpenChangePw = document.getElementById('btn-open-change-pw');
  
  const btnChangePwSubmit = document.getElementById('btn-change-pw-submit');
  const btnChangePwCancel = document.getElementById('btn-change-pw-cancel');
  
  const btnStepUpSubmit = document.getElementById('btn-step-up-submit');
  const btnStepUpCancel = document.getElementById('btn-step-up-cancel');
  
  const btnMFASubmit = document.getElementById('btn-mfa-submit');
  const btnMFACancel = document.getElementById('btn-mfa-cancel');

  // Toggle views
  linkRegister.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('card-login').style.display = 'none';
    document.getElementById('card-register').style.display = 'block';
    document.getElementById('register-error').style.display = 'none';
    document.getElementById('register-success').style.display = 'none';
  });

  linkLogin.addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('card-login').style.display = 'block';
    document.getElementById('card-register').style.display = 'none';
    document.getElementById('login-error').style.display = 'none';
  });

  // Login handler
  btnLogin.addEventListener('click', async () => {
    const u = document.getElementById('login-username').value;
    const p = document.getElementById('login-password').value;
    const t = document.getElementById('login-mfa-token').value;
    const errBox = document.getElementById('login-error');
    
    errBox.style.display = 'none';
    
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: u, password: p, mfa_token: t })
      });
      
      const data = await res.json();
      if (!res.ok) {
        errBox.textContent = data.detail || "Authentication failed.";
        errBox.style.display = 'block';
        return;
      }
      
      if (data.mfa_required) {
        document.getElementById('login-mfa-group').style.display = 'block';
        errBox.textContent = "Please input the 6-digit Authenticator Code to complete login.";
        errBox.style.display = 'block';
        errBox.style.backgroundColor = 'var(--success-glow)';
        errBox.style.color = 'var(--success)';
        errBox.style.borderColor = 'var(--success)';
        return;
      }
      
      // Reset MFA input states
      document.getElementById('login-mfa-group').style.display = 'none';
      document.getElementById('login-mfa-token').value = '';
      
      // Validate session setup
      checkActiveSession();
    } catch (err) {
      errBox.textContent = "Server connection lost.";
      errBox.style.display = 'block';
    }
  });

  // Registration handler
  btnRegister.addEventListener('click', async () => {
    const u = document.getElementById('register-username').value;
    const p = document.getElementById('register-password').value;
    const c = document.getElementById('register-confirm').value;
    const errBox = document.getElementById('register-error');
    const succBox = document.getElementById('register-success');
    
    errBox.style.display = 'none';
    succBox.style.display = 'none';
    
    if (p !== c) {
      errBox.textContent = "Passwords do not match.";
      errBox.style.display = 'block';
      return;
    }
    
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: u, password: p })
      });
      
      const data = await res.json();
      if (!res.ok) {
        errBox.textContent = data.detail || "Registration request failed.";
        errBox.style.display = 'block';
        return;
      }
      
      succBox.textContent = data.message;
      succBox.style.display = 'block';
      
      // Clear inputs
      document.getElementById('register-username').value = '';
      document.getElementById('register-password').value = '';
      document.getElementById('register-confirm').value = '';
    } catch (err) {
      errBox.textContent = "Server connection lost.";
      errBox.style.display = 'block';
    }
  });

  // Logout handler
  btnLogout.addEventListener('click', async () => {
    try {
      await secureFetch("/api/auth/logout", { method: "POST" });
    } catch (err) {}
    state.user = null;
    showLoginOverlay();
  });

  // Open modals
  btnOpenChangePw.addEventListener('click', () => {
    document.getElementById('modal-overlay').style.display = 'flex';
    document.getElementById('modal-change-password').style.display = 'block';
    document.getElementById('modal-step-up').style.display = 'none';
    document.getElementById('modal-mfa-setup').style.display = 'none';
    document.getElementById('change-pw-error').style.display = 'none';
    document.getElementById('change-pw-current').value = '';
    document.getElementById('change-pw-new').value = '';
    document.getElementById('change-pw-confirm').value = '';
    setTimeout(() => document.getElementById('change-pw-current').focus(), 50);
  });

  btnOpenMFA.addEventListener('click', async () => {
    const errBox = document.getElementById('mfa-setup-error');
    errBox.style.display = 'none';
    
    // Call enroll endpoint. If 403 requires step-up, secureFetch will handle the modal intercept!
    try {
      const res = await secureFetch("/api/auth/mfa/enroll", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        
        document.getElementById('modal-overlay').style.display = 'flex';
        document.getElementById('modal-mfa-setup').style.display = 'block';
        document.getElementById('modal-change-password').style.display = 'none';
        document.getElementById('modal-step-up').style.display = 'none';
        
        // Print key
        document.getElementById('mfa-secret-val').textContent = data.secret;
        
        // Draw verification QR on canvas
        drawMFAQr(data.secret);
      }
    } catch (err) {
      // Step-up verification takes priority, errors are handled locally or skipped
    }
  });

  // Change Password Submit
  btnChangePwSubmit.addEventListener('click', async () => {
    const cur = document.getElementById('change-pw-current').value;
    const n = document.getElementById('change-pw-new').value;
    const c = document.getElementById('change-pw-confirm').value;
    const errBox = document.getElementById('change-pw-error');
    
    errBox.style.display = 'none';
    if (n !== c) {
      errBox.textContent = "New passwords do not match.";
      errBox.style.display = 'block';
      return;
    }
    
    try {
      const res = await secureFetch("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: cur, new_password: n })
      });
      
      const data = await res.json();
      if (!res.ok) {
        errBox.textContent = data.detail || "Failed to update password.";
        errBox.style.display = 'block';
        return;
      }
      
      alert("Password changed successfully.");
      hideModals();
      checkActiveSession();
    } catch (err) {
      errBox.textContent = err.message || "Failed to submit.";
      errBox.style.display = 'block';
    }
  });

  // Step-Up Submit (Elevation Validation)
  btnStepUpSubmit.addEventListener('click', async () => {
    const p = document.getElementById('step-up-password').value;
    const t = document.getElementById('step-up-mfa-token').value;
    const errBox = document.getElementById('step-up-error');
    
    errBox.style.display = 'none';
    
    try {
      const res = await fetch("/api/auth/step-up", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "X-CSRF-Token": getCookie("csrf_token") || ""
        },
        body: JSON.stringify({ password: p, mfa_token: t })
      });
      
      const data = await res.json();
      if (!res.ok) {
        errBox.textContent = data.detail || "Step-up authorization failed.";
        errBox.style.display = 'block';
        return;
      }
      
      // Step-up succeeded: close modal and trigger original callback retries
      document.getElementById('modal-overlay').style.display = 'none';
      document.getElementById('modal-step-up').style.display = 'none';
      
      if (pendingStepUpResolve) {
        pendingStepUpResolve();
        pendingStepUpResolve = null;
        pendingStepUpReject = null;
      }
    } catch (err) {
      errBox.textContent = "Connection lost.";
      errBox.style.display = 'block';
    }
  });

  // MFA Enrollment Complete Verify
  btnMFASubmit.addEventListener('click', async () => {
    const secret = document.getElementById('mfa-secret-val').textContent;
    const code = document.getElementById('mfa-verify-code').value;
    const errBox = document.getElementById('mfa-setup-error');
    
    errBox.style.display = 'none';
    
    try {
      const res = await secureFetch("/api/auth/mfa/verify-enroll", {
        method: "POST",
        body: JSON.stringify({ secret: secret, code: code })
      });
      
      const data = await res.json();
      if (!res.ok) {
        errBox.textContent = data.detail || "Invalid code. MFA setup failed.";
        errBox.style.display = 'block';
        return;
      }
      
      alert("MFA successfully configured!");
      hideModals();
    } catch (err) {
      errBox.textContent = err.message || "Failed verification.";
      errBox.style.display = 'block';
    }
  });

  // Cancel modals
  btnChangePwCancel.addEventListener('click', hideModals);
  btnStepUpCancel.addEventListener('click', hideModals);
  btnMFACancel.addEventListener('click', hideModals);
  
  // Close modals on overlay outer click
  document.getElementById('modal-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'modal-overlay') {
      hideModals();
    }
  });

  // Check active session on startup
  checkActiveSession();
}

// --- ADMIN PANEL FUNCTIONS ---

async function loadAdminPanel() {
  const usersBody = document.getElementById('admin-users-table-body');
  const auditBody = document.getElementById('admin-audit-table-body');
  
  usersBody.innerHTML = `<tr><td colspan="4" style="text-align:center; padding:20px;">Fetching directories...</td></tr>`;
  auditBody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px;">Loading audit trail...</td></tr>`;
  
  try {
    // 1. Fetch Users
    const usersRes = await secureFetch("/api/admin/users");
    if (usersRes.ok) {
      const users = await usersRes.json();
      document.getElementById('active-user-kpi').textContent = `${users.length} User${users.length !== 1 ? 's' : ''}`;
      
      if (users.length === 0) {
        usersBody.innerHTML = `<tr><td colspan="4" style="text-align:center; font-style:italic; padding:20px;">No registered operators.</td></tr>`;
      } else {
        usersBody.innerHTML = users.map(u => {
          const checkStatus = u.status === 'active';
          const isOperator = u.role === 'operator';
          
          return `
            <tr style="border-bottom:1px solid var(--border-light);">
              <td style="padding:10px; font-weight:600; color:var(--text-main);">${u.username}</td>
              <td style="padding:10px;"><span class="pill-badge info">${u.role}</span></td>
              <td style="padding:10px;"><span class="pill-badge ${u.status}">${u.status}</span></td>
              <td style="padding:10px; text-align:center; display:flex; gap:6px; justify-content:center;">
                <button class="action-btn user-act-btn" data-id="${u.id}" data-action="status" style="padding:4px 8px; font-size:0.75rem; min-height:28px; border-radius:6px; width:auto; cursor:pointer;">
                  ${checkStatus ? 'Disable' : 'Activate'}
                </button>
                <button class="action-btn user-act-btn" data-id="${u.id}" data-action="role" style="padding:4px 8px; font-size:0.75rem; min-height:28px; border-radius:6px; width:auto; cursor:pointer;">
                  ${isOperator ? 'Make Admin' : 'Make Operator'}
                </button>
                <button class="action-btn user-act-btn" data-id="${u.id}" data-action="reset" style="padding:4px 8px; font-size:0.75rem; min-height:28px; border-radius:6px; width:auto; cursor:pointer;">
                  Reset PW
                </button>
                <button class="action-btn user-act-btn secondary" data-id="${u.id}" data-action="delete" style="padding:4px 8px; font-size:0.75rem; min-height:28px; border-radius:6px; width:auto; cursor:pointer; color:var(--danger); border-color:var(--danger-glow);">
                  Delete
                </button>
              </td>
            </tr>
          `;
        }).join('');
        
        // Link User Action listeners
        usersBody.querySelectorAll('.user-act-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const userId = btn.dataset.id;
            const action = btn.dataset.action;
            handleUserManagementAction(userId, action);
          });
        });
      }
    }
    
    // 2. Fetch Audit Logs
    const auditRes = await secureFetch("/api/admin/audit");
    if (auditRes.ok) {
      const logs = await auditRes.json();
      
      if (logs.length === 0) {
        auditBody.innerHTML = `<tr><td colspan="6" style="text-align:center; font-style:italic; padding:20px;">No security records logged.</td></tr>`;
      } else {
        auditBody.innerHTML = logs.map(l => {
          const dateStr = new Date(l.timestamp * 1000).toLocaleTimeString();
          
          return `
            <tr style="border-bottom:1px solid var(--border-light);">
              <td style="padding:8px; color:var(--accent); font-weight:600;">#${l.seq}</td>
              <td style="padding:8px; color:var(--text-muted);">${dateStr}</td>
              <td style="padding:8px; color:var(--text-main); font-weight:500;">${l.actor}</td>
              <td style="padding:8px;"><span class="pill-badge info" style="font-size:0.7rem; padding:1px 6px;">${l.action}</span></td>
              <td style="padding:8px; color:var(--text-main);">${l.details}</td>
              <td style="padding:8px; color:var(--text-muted); font-size:0.75rem;">${l.record_hash.substring(0,16)}...</td>
            </tr>
          `;
        }).join('');
      }
    }

    // 3. Fetch Tracked Devices
    const devicesBody = document.getElementById('admin-devices-table-body');
    if (devicesBody) {
      devicesBody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px;">Loading network devices...</td></tr>`;
      const devicesRes = await secureFetch("/api/admin/devices");
      if (devicesRes.ok) {
        const devices = await devicesRes.json();
        document.getElementById('active-devices-kpi').textContent = `${devices.length} Device${devices.length !== 1 ? 's' : ''} Tracked`;
        
        if (devices.length === 0) {
          devicesBody.innerHTML = `<tr><td colspan="7" style="text-align:center; font-style:italic; padding:20px;">No network devices recorded.</td></tr>`;
        } else {
          devicesBody.innerHTML = devices.map(d => {
            const isBlocked = d.status === 'blocked';
            const icon = d.device_type === 'Mobile' ? '📱' : (d.device_type === 'Tablet' ? '📱' : '💻');
            const lastSeenStr = new Date(d.last_seen * 1000).toLocaleString();
            
            return `
              <tr style="border-bottom:1px solid var(--border-light);">
                <td style="padding:10px; font-weight:600; font-family:monospace; color:var(--accent);">${d.ip_address}</td>
                <td style="padding:10px;">${icon} ${d.device_type}</td>
                <td style="padding:10px; font-size:0.75rem; color:var(--text-muted); max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${d.user_agent}">${d.user_agent}</td>
                <td style="padding:10px; font-weight:500; color:var(--text-main);">${d.last_username}</td>
                <td style="padding:10px; font-size:0.8rem; color:var(--text-muted);">${lastSeenStr}</td>
                <td style="padding:10px;"><span class="pill-badge ${isBlocked ? 'disabled' : 'active'}">${d.status}</span></td>
                <td style="padding:10px; text-align:center;">
                  <button class="action-btn device-block-btn ${isBlocked ? '' : 'secondary'}" data-ip="${d.ip_address}" data-blocked="${isBlocked}" style="padding:4px 10px; font-size:0.75rem; min-height:28px; border-radius:6px; width:auto; cursor:pointer; ${isBlocked ? '' : 'color:var(--danger); border-color:var(--danger-glow);'}">
                    ${isBlocked ? 'Unblock IP' : 'Block Device'}
                  </button>
                </td>
              </tr>
            `;
          }).join('');
          
          devicesBody.querySelectorAll('.device-block-btn').forEach(btn => {
            btn.addEventListener('click', () => {
              const ip = btn.dataset.ip;
              const isBlocked = btn.dataset.blocked === 'true';
              handleDeviceBlockAction(ip, isBlocked);
            });
          });
        }
      }
    }
  } catch (err) {
    console.error("Admin view load failed:", err);
  }
}

async function handleDeviceBlockAction(ipAddress, isCurrentlyBlocked) {
  const action = isCurrentlyBlocked ? 'unblock' : 'block';
  const url = `/api/admin/devices/${action}`;
  
  if (!isCurrentlyBlocked && !confirm(`Are you sure you want to block device IP '${ipAddress}'? All active sessions from this IP will be terminated immediately.`)) {
    return;
  }
  
  try {
    const res = await secureFetch(url, {
      method: "POST",
      body: JSON.stringify({ ip_address: ipAddress, reason: "Blocked via Administrator Control Gateway" })
    });
    
    const data = await res.json();
    if (!res.ok) {
      alert(`Device action failed: ${data.detail}`);
      return;
    }
    
    alert(data.message);
    loadAdminPanel();
  } catch (err) {
    alert("Connection lost while updating device status.");
  }
}


async function handleUserManagementAction(userId, action) {
  try {
    let url = `/api/admin/users/${userId}`;
    let method = "PUT";
    let body = null;
    
    if (action === "status") {
      const statusBtnText = document.querySelector(`.user-act-btn[data-id="${userId}"][data-action="status"]`).textContent.trim();
      const nextStatus = statusBtnText === 'Activate' ? 'active' : 'disabled';
      url += "/status";
      body = JSON.stringify({ status: nextStatus });
    } else if (action === "role") {
      const roleBtnText = document.querySelector(`.user-act-btn[data-id="${userId}"][data-action="role"]`).textContent.trim();
      const nextRole = roleBtnText === 'Make Admin' ? 'admin' : 'operator';
      url += "/role";
      body = JSON.stringify({ role: nextRole });
    } else if (action === "reset") {
      url += "/reset-password";
    } else if (action === "delete") {
      method = "DELETE";
      if (!confirm("Are you sure you want to permanently delete this user account? This cannot be undone.")) {
        return;
      }
    }
    
    const res = await secureFetch(url, {
      method: method,
      body: body
    });
    
    const data = await res.json();
    if (!res.ok) {
      alert(`Action failed: ${data.detail}`);
      return;
    }
    
    if (action === "reset") {
      // Print temporary password to administrator screen
      alert(`Password successfully reset.\nTemporary Password: ${data.temp_password}\n(This will only be displayed ONCE. Force change is set for next login.)`);
    } else {
      alert(data.message || "User action completed successfully.");
    }
    
    // Reload panel
    loadAdminPanel();
    
  } catch (err) {
    if (err.message && err.message.includes("Step-up")) {
      // Step-up is already being handled, skip alert
      return;
    }
    alert(`Error: ${err.message}`);
  }
}

// Hook Create User Form in Admin view
document.addEventListener('DOMContentLoaded', () => {
  const btnCreateSubmit = document.getElementById('btn-create-user-submit');
  if (btnCreateSubmit) {
    btnCreateSubmit.addEventListener('click', async () => {
      const u = document.getElementById('create-username').value.trim();
      const p = document.getElementById('create-password').value;
      const r = document.getElementById('create-role').value;
      
      if (!u || !p) {
        alert("Please specify a username and initial password.");
        return;
      }
      
      try {
        // Step 1: Request Registration
        const res1 = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username: u, password: p })
        });
        
        const data1 = await res1.json();
        if (!res1.ok) {
          alert(`Registration request failed: ${data1.detail}`);
          return;
        }
        
        // Step 2: Auto-Approve user as Active (requires elevated admin step-up if not already elevated!)
        const listUsers = await secureFetch("/api/admin/users");
        if (listUsers.ok) {
          const usersList = await listUsers.json();
          const targetUser = usersList.find(usr => usr.username === u);
          
          if (targetUser) {
            // Activate status
            const res2 = await secureFetch(`/api/admin/users/${targetUser.id}/status`, {
              method: "PUT",
              body: JSON.stringify({ status: "active" })
            });
            
            // Adjust role if admin was selected
            if (r === "admin" && res2.ok) {
              await secureFetch(`/api/admin/users/${targetUser.id}/role`, {
                method: "PUT",
                body: JSON.stringify({ role: "admin" })
              });
            }
            
            alert(`User account '${u}' successfully created and activated.`);
            
            // Clear inputs
            document.getElementById('create-username').value = '';
            document.getElementById('create-password').value = '';
            
            loadAdminPanel();
          }
        }
      } catch (err) {
        if (err.message && err.message.includes("Step-up")) return;
        alert(`Error: ${err.message}`);
      }
    });
  }
});

// --- MFA QR CODE DRAWING ENGINE ---
function drawMFAQr(secret) {
  const canvas = document.getElementById('mfa-qr-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;
  
  // Clear to white
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, w, h);
  
  // Draw Corner Patterns
  drawQRCornerPattern(ctx, 5, 5, 26);
  drawQRCornerPattern(ctx, w - 31, 5, 26);
  drawQRCornerPattern(ctx, 5, h - 31, 26);
  
  // Draw deterministic blocks from hash of secret
  let hash = 5381;
  for (let i = 0; i < secret.length; i++) {
    hash = ((hash << 5) + hash) + secret.charCodeAt(i);
  }
  
  const cells = 12;
  const cellW = (w - 10) / cells;
  const cellH = (h - 10) / cells;
  
  ctx.fillStyle = "#000000";
  for (let r = 0; r < cells; r++) {
    for (let c = 0; c < cells; c++) {
      const isCorner = (r < 4 && c < 4) || (r < 4 && c >= cells - 4) || (r >= cells - 4 && c < 4);
      if (!isCorner) {
        const fill = Math.sin(hash + r*17 + c*31) > 0;
        if (fill) {
          ctx.fillRect(5 + c*cellW, 5 + r*cellH, cellW - 0.5, cellH - 0.5);
        }
      }
    }
  }
}

function drawQRCornerPattern(ctx, x, y, size) {
  ctx.fillStyle = "#000000";
  ctx.fillRect(x, y, size, size);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(x + 4, y + 4, size - 8, size - 8);
  ctx.fillStyle = "#000000";
  ctx.fillRect(x + 8, y + 8, size - 16, size - 16);
}

// --- CYCLE 3 HELPER ROUTINES & EVENT HANDLERS ---

function generateUUIDv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function loadInventory() {
  try {
    const res = await secureFetch("/api/inventory");
    if (!res.ok) return;
    
    posInventory = await res.json();
    
    // 1. Populate POS Checkout Product Dropdown
    const posSelect = document.getElementById('pos-product-select');
    if (posSelect) {
      posSelect.innerHTML = '<option value="">-- Select Product --</option>' + 
        posInventory.map(item => {
          const out = item.quantity <= 0;
          return `<option value="${item.id}" ${out ? 'disabled' : ''}>${item.name} ($${item.price_usd.toFixed(2)})${out ? ' - [OUT OF STOCK]' : ''}</option>`;
        }).join('');
    }
    
    // 2. Populate Stock Adjust Product Dropdown
    const saSelect = document.getElementById('sa-item-select');
    if (saSelect) {
      saSelect.innerHTML = posInventory.map(item => 
        `<option value="${item.id}">${item.name} (Current: ${item.quantity} ${item.unit})</option>`
      ).join('');
    }
    
    // 3. Render Stock Roster Table
    const tbody = document.getElementById('inventory-tbody');
    if (tbody) {
      if (posInventory.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="padding:15px; text-align:center;">No stock items registered.</td></tr>`;
      } else {
        tbody.innerHTML = posInventory.map(item => {
          let statusBadge = '';
          if (item.quantity <= 0) {
            statusBadge = `<span class="badge-stock danger">⚠️ OUT</span>`;
          } else if (item.quantity <= item.low_stock_threshold) {
            statusBadge = `<span class="badge-stock warning">⚠️ LOW: ${item.quantity}</span>`;
          } else {
            statusBadge = `<span class="badge-stock safe">SAFE</span>`;
          }
          return `
            <tr style="border-bottom: 1px solid var(--border-light);">
              <td style="padding:10px;">${item.name}</td>
              <td style="padding:10px; font-family:monospace;">${item.sku}</td>
              <td style="padding:10px; text-align:right;">${item.quantity} ${item.unit}</td>
              <td style="padding:10px; text-align:right;">$${item.price_usd.toFixed(2)}</td>
              <td style="padding:10px; text-align:center;">${statusBadge}</td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.error("Error loading inventory:", err);
  }
}

function addCartItem(itemId, qty) {
  const item = posInventory.find(i => i.id === itemId);
  if (!item) return;
  
  const existing = posCart.find(c => c.id === itemId);
  const currentQtyInCart = existing ? existing.quantity : 0;
  const requestedTotalQty = currentQtyInCart + qty;
  
  if (item.quantity < requestedTotalQty) {
    alert(`Insufficient stock for '${item.name}'. Available: ${item.quantity} ${item.unit}, requested total: ${requestedTotalQty}.`);
    return;
  }
  
  if (existing) {
    existing.quantity = requestedTotalQty;
  } else {
    posCart.push({
      id: item.id,
      name: item.name,
      sku: item.sku,
      price_usd: item.price_usd,
      quantity: qty
    });
  }
  
  // Save to localStorage for power-loss recovery
  localStorage.setItem('madn_pos_cart', JSON.stringify(posCart));
  renderCartTable();
}

function removeCartItem(idx) {
  posCart.splice(idx, 1);
  localStorage.setItem('madn_pos_cart', JSON.stringify(posCart));
  renderCartTable();
}

function renderCartTable() {
  const tbody = document.getElementById('pos-cart-tbody');
  const inputDueUsd = document.getElementById('cart-amount-usd');
  
  if (!tbody) return;
  
  if (posCart.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="padding: 10px; text-align: center; color: var(--text-muted); font-style: italic;">Cart is empty.</td></tr>`;
    inputDueUsd.value = "0.00";
    // Trigger recalculation
    const inputZar = document.getElementById('rate-zar');
    const inputZwg = document.getElementById('rate-zwg');
    const inputTenderUsd = document.getElementById('tender-usd');
    const inputTenderZar = document.getElementById('tender-zar');
    const inputTenderZwg = document.getElementById('tender-zwg');
    recalculateTender(0, parseFloat(inputZar.value)||18, parseFloat(inputZwg.value)||25, parseFloat(inputTenderUsd.value)||0, parseFloat(inputTenderZar.value)||0, parseFloat(inputTenderZwg.value)||0);
    return;
  }
  
  let totalUsd = 0;
  tbody.innerHTML = posCart.map((c, idx) => {
    const rowTotal = c.price_usd * c.quantity;
    totalUsd += rowTotal;
    return `
      <tr style="border-bottom: 1px solid var(--border-light); font-size: 0.85rem;">
        <td style="padding:6px; display:flex; justify-content:space-between; align-items:center;">
          <span>${c.name}</span>
          <button onclick="removeCartItem(${idx})" style="background:none; border:none; color:var(--danger); cursor:pointer; font-size:0.75rem;">[Remove]</button>
        </td>
        <td style="padding:6px; text-align:right;">$${c.price_usd.toFixed(2)}</td>
        <td style="padding:6px; text-align:right;">${c.quantity}</td>
        <td style="padding:6px; text-align:right; font-weight:600;">$${rowTotal.toFixed(2)}</td>
      </tr>
    `;
  }).join('');
  
  inputDueUsd.value = totalUsd.toFixed(2);
  
  // Trigger recalculation
  const inputZar = document.getElementById('rate-zar');
  const inputZwg = document.getElementById('rate-zwg');
  const inputTenderUsd = document.getElementById('tender-usd');
  const inputTenderZar = document.getElementById('tender-zar');
  const inputTenderZwg = document.getElementById('tender-zwg');
  recalculateTender(totalUsd, parseFloat(inputZar.value)||18, parseFloat(inputZwg.value)||25, parseFloat(inputTenderUsd.value)||0, parseFloat(inputTenderZar.value)||0, parseFloat(inputTenderZwg.value)||0);
}

function clearCart() {
  posCart = [];
  localStorage.removeItem('madn_pos_cart');
  renderCartTable();
}

function loadPOSCartFromCache() {
  const cached = localStorage.getItem('madn_pos_cart');
  if (cached) {
    try {
      const parsed = JSON.parse(cached);
      if (parsed && parsed.length > 0) {
        if (confirm("You have an active in-progress checkout cart from a previous session. Resume transaction?")) {
          posCart = parsed;
          renderCartTable();
        } else {
          clearCart();
        }
      }
    } catch(e) {
      clearCart();
    }
  }
}

// Adjust inventory stock from stock adjust card
async function handleInventoryAdjustment() {
  const select = document.getElementById('sa-item-select');
  const typeSelect = document.getElementById('sa-type');
  const qtyInput = document.getElementById('sa-qty');
  const reasonSelect = document.getElementById('sa-reason');
  
  const itemId = select.value;
  const adjustType = typeSelect.value;
  const qty = parseFloat(qtyInput.value) || 0;
  const reason = reasonSelect.value;
  
  if (!itemId || qty <= 0) {
    alert("Please select a valid item and positive quantity.");
    return;
  }
  
  try {
    let res;
    if (adjustType === 'wastage') {
      res = await secureFetch(`/api/inventory/${itemId}/wastage`, {
        method: "POST",
        body: JSON.stringify({ quantity: qty, reason: reason })
      });
    } else {
      res = await secureFetch(`/api/inventory/${itemId}/adjust`, {
        method: "PUT",
        body: JSON.stringify({ amount: qty, reason: "replenishment" })
      });
    }
    
    if (res.ok) {
      alert("Inventory adjustment saved successfully.");
      qtyInput.value = 1.0;
      await loadInventory();
    } else {
      const err = await res.json();
      alert(`Adjustment failed: ${err.detail}`);
    }
  } catch (err) {
    alert(`Adjustment error: ${err.message}`);
  }
}

function toggleWastageFields() {
  const saType = document.getElementById('sa-type').value;
  const reasonGroup = document.getElementById('sa-reason-group');
  if (saType === 'wastage') {
    reasonGroup.style.display = 'block';
  } else {
    reasonGroup.style.display = 'none';
  }
}

function updateStockAdjustUI() {
  // Optional secondary fields updates
}

// Low Stock Reorder Manifest Generation
function generateReorderManifest() {
  const lowStockItems = posInventory.filter(item => item.quantity <= item.low_stock_threshold);
  
  if (lowStockItems.length === 0) {
    alert("All inventory items are currently above low-stock safety thresholds. No reorder required!");
    return;
  }
  
  const manifest = {
    title: "MADN LOW-STOCK REORDER MANIFEST",
    timestamp: new Date().toLocaleString(),
    items: lowStockItems.map(i => ({
      name: i.name,
      sku: i.sku,
      current_stock: `${i.quantity} ${i.unit}`,
      threshold: `${i.low_stock_threshold} ${i.unit}`,
      suggested_reorder: `${Math.ceil(i.low_stock_threshold * 3 - i.quantity)} ${i.unit}`
    }))
  };
  
  const printText = JSON.stringify(manifest, null, 2);
  
  // Open in a friendly popup window or download
  const blob = new Blob([printText], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `reorder_manifest_${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  alert("Generated and downloaded low-stock reorder manifest JSON package.");
}

// VPA 1.3: Agricultural Estimator wizard
function toggleEstimatorForm() {
  const type = document.getElementById('estimator-type').value;
  const cropGroup = document.getElementById('est-crop-group');
  const herdGroup = document.getElementById('est-herd-group');
  
  if (type === 'crop_yield') {
    cropGroup.style.display = 'block';
    herdGroup.style.display = 'none';
  } else {
    cropGroup.style.display = 'none';
    herdGroup.style.display = 'block';
  }
}

async function runAgriculturalEstimator() {
  const type = document.getElementById('estimator-type').value;
  let inputs = {};
  
  if (type === 'crop_yield') {
    inputs = {
      plot_square_footage: parseFloat(document.getElementById('est-plot-size').value) || 0,
      soil_class: document.getElementById('est-soil-class').value,
      rainfall_anomaly: parseFloat(document.getElementById('est-rainfall-slider').value) / 100.0
    };
  } else {
    inputs = {
      animal_count: parseInt(document.getElementById('est-animal-count').value) || 0,
      average_weight: parseFloat(document.getElementById('est-avg-weight').value) || 0,
      stage: document.getElementById('est-growth-stage').value
    };
  }
  
  try {
    const res = await secureFetch("/api/agriculture/estimator/calculate", {
      method: "POST",
      body: JSON.stringify({ type: type, inputs: inputs })
    });
    
    const data = await res.json();
    if (!res.ok) {
      alert(`Calculation failed: ${data.detail}`);
      return;
    }
    
    const box = document.getElementById('est-outputs-box');
    if (type === 'crop_yield') {
      const yieldKg = data.outputs.estimated_yield_kg;
      box.className = "recommendation-box success";
      box.innerHTML = `
        <div class="recommendation-content" style="width:100%; text-align:left;">
          <h5 class="color-success">Predicted Yield: ${yieldKg} kg</h5>
          <p>Model outputs estimate dynamic harvest potential adjusted by soil classification factors and the rainfall anomaly coefficients.</p>
        </div>
      `;
    } else {
      const feedKg = data.outputs.daily_feed_kg;
      box.className = "recommendation-box success";
      box.innerHTML = `
        <div class="recommendation-content" style="width:100%; text-align:left;">
          <h5 class="color-success">Daily Feed Intake: ${feedKg} kg</h5>
          <p>Total bulk feed requirements computed locally across herd groups and current production growth parameters.</p>
        </div>
      `;
    }
    
    // Reload history
    await loadEstimatorHistory();
    
  } catch (err) {
    alert(`Calculation error: ${err.message}`);
  }
}

async function loadEstimatorHistory() {
  try {
    const res = await secureFetch("/api/agriculture/estimator/history");
    if (!res.ok) return;
    const history = await res.json();
    
    const tbody = document.getElementById('est-history-tbody');
    if (tbody) {
      if (history.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="padding:10px; text-align:center; color:var(--text-muted); font-style:italic;">No historical calculations.</td></tr>`;
      } else {
        tbody.innerHTML = history.map(run => {
          const dateStr = new Date(run.timestamp * 1000).toLocaleDateString();
          const label = run.type === 'crop_yield' ? 'Crop Yield' : 'Herd Feed';
          
          let inputDesc = '';
          let outputDesc = '';
          if (run.type === 'crop_yield') {
            inputDesc = `${run.inputs.plot_square_footage} sqft, ${run.inputs.soil_class.replace('_', ' ')}`;
            outputDesc = `${run.outputs.estimated_yield_kg} kg`;
          } else {
            inputDesc = `${run.inputs.animal_count} heads, ${run.inputs.average_weight} kg`;
            outputDesc = `${run.outputs.daily_feed_kg} kg/day`;
          }
          
          return `
            <tr style="border-bottom: 1px solid var(--border-light);">
              <td style="padding:8px;">${dateStr}</td>
              <td style="padding:8px; font-weight:600;">${label}</td>
              <td style="padding:8px; font-size:0.75rem; color:var(--text-muted);">${inputDesc}</td>
              <td style="padding:8px; text-align:right; font-weight:700; color:var(--accent);">${outputDesc}</td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.error(err);
  }
}

// VPA 2.3: Security handovers
async function submitGuardHandover() {
  const incoming = document.getElementById('ho-incoming-guard').value.trim();
  const pin = document.getElementById('ho-incoming-pin').value.trim();
  const shiftType = document.getElementById('ho-shift-type').value;
  const severity = document.getElementById('ho-severity').value;
  const summary = document.getElementById('ho-events-summary').value.trim();
  
  const usdCash = parseFloat(document.getElementById('ho-cash-usd').value) || 0;
  const zarCash = parseFloat(document.getElementById('ho-cash-zar').value) || 0;
  const zwgCash = parseFloat(document.getElementById('ho-cash-zwg').value) || 0;
  
  if (!incoming || !pin || !summary) {
    alert("Please specify incoming guard username, verification PIN, and duty log summary.");
    return;
  }
  
  // Calculate expected cash balances based on local transactions reserves
  let expectedUSD = 0;
  let expectedZAR = 0;
  let expectedZWG = 0;
  
  state.pos.transactions.forEach(tx => {
    expectedUSD += tx.paidUsd || 0;
    expectedZAR += tx.paidZar || 0;
    expectedZWG += tx.paidZwg || 0;
  });
  
  try {
    const res = await secureFetch("/api/security/handover", {
      method: "POST",
      body: JSON.stringify({
        incoming_guard: incoming,
        incoming_pin: pin,
        shift_type: shiftType,
        severity: severity,
        events_summary: summary,
        cash_expected: { usd: expectedUSD, zar: expectedZAR, zwg: expectedZWG },
        cash_counted: { usd: usdCash, zar: zarCash, zwg: zwgCash }
      })
    });
    
    const data = await res.json();
    if (!res.ok) {
      alert(`Shift Handover failed: ${data.detail}`);
      return;
    }
    
    alert("Shift handover verification succeeded. Digital logs cryptographically signed and chained.");
    
    // Clear inputs
    document.getElementById('ho-incoming-guard').value = '';
    document.getElementById('ho-incoming-pin').value = '';
    document.getElementById('ho-events-summary').value = '';
    document.getElementById('ho-cash-usd').value = '0.00';
    document.getElementById('ho-cash-zar').value = '0.00';
    document.getElementById('ho-cash-zwg').value = '0.00';
    
    await loadHandoverHistory();
    
  } catch (err) {
    alert(`Handover error: ${err.message}`);
  }
}

async function loadHandoverHistory() {
  try {
    const res = await secureFetch("/api/security/handover/history");
    if (!res.ok) return;
    
    const logs = await res.json();
    const tbody = document.getElementById('ho-logs-tbody');
    if (tbody) {
      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="padding:15px; text-align:center; color:var(--text-muted); font-style:italic;">No shift handovers logged.</td></tr>`;
      } else {
        tbody.innerHTML = logs.map(l => {
          const dateStr = new Date(l.timestamp * 1000).toLocaleTimeString() + " " + new Date(l.timestamp * 1000).toLocaleDateString();
          
          let sevColor = 'green_routine';
          if (l.severity === 'amber_minor') sevColor = 'amber_minor';
          if (l.severity === 'red_critical') sevColor = 'red_critical';
          
          const labelSev = l.severity.replace('_', ' ').toUpperCase();
          
          return `
            <tr style="border-bottom: 1px solid var(--border-light);">
              <td style="padding:10px; font-family:monospace; font-size:0.75rem;">${dateStr}</td>
              <td style="padding:10px; font-weight:600;">${l.outgoing_guard} → ${l.incoming_guard}</td>
              <td style="padding:10px;"><span class="severity-badge ${sevColor}">${labelSev}</span></td>
              <td style="padding:10px; font-size:0.75rem; color:var(--text-muted); max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${l.events_summary}">${l.events_summary}</td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.error(err);
  }
}

// Hook Keyboard hotkeys
document.addEventListener('keydown', (e) => {
  if (state.activeView === 'vpa3') {
    if (e.key === 'F2') {
      e.preventDefault();
      const select = document.getElementById('pos-product-select');
      if (select) select.focus();
    } else if (e.key === 'F8') {
      e.preventDefault();
      if (confirm("Are you sure you want to void/clear the current cart?")) {
        clearCart();
      }
    } else if (e.key === 'F9') {
      e.preventDefault();
      const inputTenderUsd = document.getElementById('tender-usd');
      if (inputTenderUsd) inputTenderUsd.focus();
    }
  }
});

// Register Event listeners for new Cycle 3 features
document.addEventListener('DOMContentLoaded', () => {
  // Agriculture Estimators Type Toggle
  const estSelect = document.getElementById('estimator-type');
  if (estSelect) {
    estSelect.addEventListener('change', toggleEstimatorForm);
  }
  
  // Realtime Rainfall Slider output updates
  const rainSlider = document.getElementById('est-rainfall-slider');
  if (rainSlider) {
    rainSlider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      const percentStr = val >= 0 ? `+${val}% Surplus` : `${val}% Deficit`;
      document.getElementById('est-rainfall-percent').textContent = val === 0 ? "Average (0%)" : percentStr;
    });
  }
  
  // Run Estimator Button Click
  const btnRunEst = document.getElementById('btn-run-estimator');
  if (btnRunEst) {
    btnRunEst.addEventListener('click', runAgriculturalEstimator);
  }
  
  // Shift Handover submit click
  const btnSubmitHo = document.getElementById('btn-submit-handover');
  if (btnSubmitHo) {
    btnSubmitHo.addEventListener('click', submitGuardHandover);
  }
  
  // Adjust stock submit click
  const btnAdjustStk = document.getElementById('btn-adjust-stock');
  if (btnAdjustStk) {
    btnAdjustStk.addEventListener('click', handleInventoryAdjustment);
  }
  
  // Reorder manifest download click
  const btnReorder = document.getElementById('btn-reorder-manifest');
  if (btnReorder) {
    btnReorder.addEventListener('click', generateReorderManifest);
  }
  
  // Adjust stock options details toggle
  const saType = document.getElementById('sa-type');
  if (saType) {
    saType.addEventListener('change', toggleWastageFields);
  }
  
  // --- CYCLE 4 FRONTEND HANDLERS ---

  initPointerDragNodes();
  loadSecurityNodesTelemetry();
  loadAgronomyRulesAndOrders();
  loadPosPromotions();

  // Save Rule click
  const btnSaveRule = document.getElementById('btn-save-rule');
  if (btnSaveRule) {
    btnSaveRule.addEventListener('click', saveAgronomyRule);
  }

  // Evaluate Sensors click
  const btnEvalRules = document.getElementById('btn-evaluate-rules');
  if (btnEvalRules) {
    btnEvalRules.addEventListener('click', evaluateAgronomySensors);
  }

  // Heatmap Toggle click
  const btnToggleHeatmap = document.getElementById('btn-toggle-heatmap');
  if (btnToggleHeatmap) {
    btnToggleHeatmap.addEventListener('click', toggleCoverageHeatmap);
  }

  // Digital Twin Scrubber slider
  const dtScrubber = document.getElementById('digital-twin-scrubber');
  if (dtScrubber) {
    dtScrubber.addEventListener('input', handleDigitalTwinScrub);
  }

  // Initial history load requests on navigation click
  const navAgri = document.getElementById('nav-vpa1');
  if (navAgri) {
    navAgri.addEventListener('click', () => {
      loadEstimatorHistory();
      loadAgronomyRulesAndOrders();
    });
  }
  
  const navSec = document.getElementById('nav-vpa2');
  if (navSec) {
    navSec.addEventListener('click', () => {
      loadHandoverHistory();
      loadSecurityNodesTelemetry();
    });
  }

  const navPos = document.getElementById('nav-vpa3');
  if (navPos) {
    navPos.addEventListener('click', () => {
      loadPosPromotions();
    });
  }
});

// --- CYCLE 4 FUNCTIONS ---

let cycle4NodesData = [];
let cycle4ObstaclesData = [];
let isHeatmapVisible = false;

function initPointerDragNodes() {
  const svgMap = document.getElementById('perimeter-map');
  if (!svgMap) return;

  const draggableGroups = svgMap.querySelectorAll('.map-node-group.draggable');
  draggableGroups.forEach((group, idx) => {
    let isDragging = false;
    let nodeId = idx === 0 ? 'node-1' : 'node-2';

    group.addEventListener('pointerdown', (e) => {
      isDragging = true;
      group.setPointerCapture(e.pointerId);
      group.classList.add('dragging');
    });

    group.addEventListener('pointermove', (e) => {
      if (!isDragging) return;
      const rect = svgMap.getBoundingClientRect();
      const xPx = e.clientX - rect.left;
      const yPx = e.clientY - rect.top;

      // Convert to normalized percentage (0 - 100)
      const xPct = Math.max(5, Math.min(95, (xPx / rect.width) * 100));
      const yPct = Math.max(5, Math.min(95, (yPx / rect.height) * 100));

      // Visual SVG position update (viewBox 600 x 350)
      const svgX = (xPct / 100) * 600;
      const svgY = (yPct / 100) * 350;

      const circle = group.querySelector('circle');
      const textLabel = group.querySelector('.node-label');
      const textRssi = group.querySelector('text[id$="-maplabel"]');

      if (circle) { circle.setAttribute('cx', svgX); circle.setAttribute('cy', svgY); }
      if (textLabel) { textLabel.setAttribute('x', svgX); textLabel.setAttribute('y', svgY - 5); }
      if (textRssi) { textRssi.setAttribute('x', svgX); textRssi.setAttribute('y', svgY + 30); }
    });

    const stopDrag = async (e) => {
      if (!isDragging) return;
      isDragging = false;
      group.classList.remove('dragging');

      const rect = svgMap.getBoundingClientRect();
      const xPx = e.clientX - rect.left;
      const yPx = e.clientY - rect.top;

      const xPct = Math.max(5, Math.min(95, (xPx / rect.width) * 100));
      const yPct = Math.max(5, Math.min(95, (yPx / rect.height) * 100));

      // Persist node position via LWW API
      try {
        await secureFetch(`/api/security/nodes/${nodeId}/position`, {
          method: 'PUT',
          body: JSON.stringify({
            x_pct: xPct,
            y_pct: yPct,
            client_id: state.currentUser ? state.currentUser.username : 'operator',
            timestamp_utc: new Date().toISOString()
          })
        });
        loadSecurityNodesTelemetry();
      } catch (err) {
        console.error(err);
      }
    };

    group.addEventListener('pointerup', stopDrag);
    group.addEventListener('pointercancel', stopDrag);
  });
}

async function loadSecurityNodesTelemetry() {
  try {
    const res = await secureFetch('/api/security/nodes');
    if (!res.ok) return;

    const data = await res.json();
    cycle4NodesData = data.nodes || [];
    cycle4ObstaclesData = data.obstacles || [];

    const activePill = document.getElementById('security-active-pill');
    const onlineCount = cycle4NodesData.filter(n => n.online === 1).length;
    if (activePill) activePill.textContent = `${onlineCount} Nodes Active (R*Tree Monitored)`;

    // Update map positions and RSSI labels
    cycle4NodesData.forEach(n => {
      const isNode1 = n.id === 'node-1';
      const nodeDot = document.getElementById(isNode1 ? 'map-node1-dot' : 'map-node2-dot');
      const rssiLabel = document.getElementById(isNode1 ? 'node1-rssi-maplabel' : 'node2-rssi-maplabel');
      const fresnelLine = document.getElementById(isNode1 ? 'fresnel-node1' : 'fresnel-node2');

      const svgX = (n.x_pct / 100) * 600;
      const svgY = (n.y_pct / 100) * 350;

      if (nodeDot) {
        nodeDot.setAttribute('cx', svgX);
        nodeDot.setAttribute('cy', svgY);

        let strokeColor = 'var(--success)';
        let fillColor = 'rgba(16, 185, 129, 0.2)';
        if (n.status === 'meshed') { strokeColor = 'var(--warning)'; fillColor = 'rgba(245, 158, 11, 0.2)'; }
        if (n.status === 'offline') { strokeColor = 'var(--danger)'; fillColor = 'rgba(239, 68, 68, 0.2)'; }

        nodeDot.setAttribute('stroke', strokeColor);
        nodeDot.setAttribute('fill', fillColor);
      }

      if (rssiLabel) {
        rssiLabel.setAttribute('x', svgX);
        rssiLabel.setAttribute('y', svgY + 30);
        rssiLabel.textContent = `${n.rssi} dBm (${n.status.toUpperCase()})`;
      }

      if (fresnelLine) {
        fresnelLine.setAttribute('x2', svgX);
        fresnelLine.setAttribute('y2', svgY);
      }
    });

    if (isHeatmapVisible) {
      drawCoverageHeatmap();
    }
  } catch (err) {
    console.error(err);
  }
}

function toggleCoverageHeatmap() {
  const canvas = document.getElementById('heatmap-canvas');
  if (!canvas) return;

  isHeatmapVisible = !isHeatmapVisible;
  canvas.style.opacity = isHeatmapVisible ? '0.65' : '0';
  const btn = document.getElementById('btn-toggle-heatmap');
  if (btn) btn.textContent = isHeatmapVisible ? 'Hide Signal Heatmap' : 'Toggle Signal Heatmap';

  if (isHeatmapVisible) {
    drawCoverageHeatmap();
  }
}

function drawCoverageHeatmap() {
  const canvas = document.getElementById('heatmap-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const hubX = 300, hubY = 175;
  const step = 15; // Grid resolution

  for (let x = 0; x < canvas.width; x += step) {
    for (let y = 0; y < canvas.height; y += step) {
      const distPx = Math.sqrt((x - hubX)**2 + (y - hubY)**2);
      const distM = (distPx / 600) * 500;
      let rssi = -30.0 - (10.0 * 2.5 * Math.log10(Math.max(distM, 1.0)));

      // Obstacle attenuation penalty
      cycle4ObstaclesData.forEach(obs => {
        const oXmin = (obs.x_min / 100) * 600;
        const oYmin = (obs.y_min / 100) * 350;
        const oXmax = (obs.x_max / 100) * 600;
        const oYmax = (obs.y_max / 100) * 350;
        if (x >= oXmin && x <= oXmax && y >= oYmin && y <= oYmax) {
          rssi -= obs.attenuation_db;
        }
      });

      let color = 'rgba(239, 68, 68, 0.3)'; // Red
      if (rssi >= -65) color = 'rgba(16, 185, 129, 0.35)'; // Green
      else if (rssi >= -85) color = 'rgba(245, 158, 11, 0.35)'; // Amber

      ctx.fillStyle = color;
      ctx.fillRect(x, y, step, step);
    }
  }
}

function handleDigitalTwinScrub(e) {
  const hour = parseInt(e.target.value, 10);
  const timeLabel = document.getElementById('twin-time-val');
  if (timeLabel) {
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 === 0 ? 12 : hour % 12;
    const solarNote = (hour >= 10 && hour <= 15) ? '(Peak Solar Charging)' : (hour >= 20 || hour <= 5) ? '(Nighttime Battery Draw)' : '(Standard Run)';
    timeLabel.textContent = `${displayHour}:00 ${ampm} ${solarNote}`;
  }

  // Simulate battery adjustments
  cycle4NodesData.forEach(n => {
    if (hour >= 20 || hour <= 5) {
      n.battery_pct = Math.max(10, n.battery_pct - 1.5);
    } else if (hour >= 10 && hour <= 15) {
      n.battery_pct = Math.min(100, n.battery_pct + 2.0);
    }
  });
}

async function loadAgronomyRulesAndOrders() {
  try {
    const [rulesRes, ordersRes] = await Promise.all([
      secureFetch('/api/agriculture/rules'),
      secureFetch('/api/agriculture/harvest-orders')
    ]);

    if (rulesRes.ok) {
      const rules = await rulesRes.json();
      renderRulesList(rules);
    }

    if (ordersRes.ok) {
      const orders = await ordersRes.json();
      renderHarvestOrdersTable(orders);
    }
  } catch (err) {
    console.error(err);
  }
}

function renderRulesList(rules) {
  const container = document.getElementById('rules-list-container');
  if (!container) return;

  if (rules.length === 0) {
    container.innerHTML = `<p class="neutral-message">No active agronomy rules found.</p>`;
    return;
  }

  container.innerHTML = rules.map(r => `
    <div style="background: var(--surface-card); border: 1px solid var(--border-light); padding: 10px; border-radius: 6px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <strong style="color: var(--text-main); font-size: 0.85rem;">${r.title}</strong>
        <span class="pill-badge ${r.action_type === 'actuator' ? 'info' : 'warning'}" style="font-size: 0.7rem;">${r.action_type.toUpperCase()}</span>
      </div>
      <p style="margin: 4px 0 0 0; font-size: 0.75rem; color: var(--text-muted);">${r.action_message}</p>
    </div>
  `).join('');
}

function renderHarvestOrdersTable(orders) {
  const tbody = document.getElementById('harvest-orders-tbody');
  if (!tbody) return;

  if (orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="padding:10px; text-align:center; color:var(--text-muted); font-style:italic;">No active harvest orders.</td></tr>`;
    return;
  }

  tbody.innerHTML = orders.map(o => `
    <tr style="border-bottom: 1px solid var(--border-light);">
      <td style="padding:8px; font-family:monospace; font-size:0.75rem;">${o.id.substring(0, 8)}</td>
      <td style="padding:8px; font-weight:600;">${o.crop_type}</td>
      <td style="padding:8px; font-size:0.75rem; color:var(--text-muted);">${new Date(o.spoilage_deadline_utc).toLocaleTimeString()}</td>
      <td style="padding:8px;">
        <select class="form-input" style="padding:2px 6px; font-size:0.75rem;" onchange="updateHarvestOrderStatus('${o.id}', this.value)">
          <option value="triggered" ${o.status === 'triggered' ? 'selected' : ''}>Triggered</option>
          <option value="assigned" ${o.status === 'assigned' ? 'selected' : ''}>Assigned</option>
          <option value="harvested" ${o.status === 'harvested' ? 'selected' : ''}>Harvested</option>
          <option value="pos_listed" ${o.status === 'pos_listed' ? 'selected' : ''}>POS Listed</option>
        </select>
      </td>
    </tr>
  `).join('');
}

async function updateHarvestOrderStatus(orderId, newStatus) {
  try {
    await secureFetch(`/api/agriculture/harvest-orders/${orderId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status: newStatus })
    });
    loadAgronomyRulesAndOrders();
  } catch (err) {
    console.error(err);
  }
}

async function saveAgronomyRule() {
  const title = document.getElementById('rule-title').value.trim();
  const crop = document.getElementById('rule-crop').value;
  const actionType = document.getElementById('rule-action-type').value;
  const actionMsg = document.getElementById('rule-action-message').value.trim();
  const tempVal = parseFloat(document.getElementById('sensor-temp').value) || 30.0;

  if (!title || !actionMsg) {
    alert("Please fill in rule title and notification message.");
    return;
  }

  const conditions = [{"metric": "temperature", "op": ">", "val": tempVal}];

  try {
    const res = await secureFetch('/api/agriculture/rules', {
      method: 'POST',
      body: JSON.stringify({
        title: title,
        crop_type: crop,
        conditions: conditions,
        action_type: actionType,
        action_message: actionMsg
      })
    });

    if (res.ok) {
      document.getElementById('rule-title').value = '';
      document.getElementById('rule-action-message').value = '';
      loadAgronomyRulesAndOrders();
    }
  } catch (err) {
    console.error(err);
  }
}

async function evaluateAgronomySensors() {
  const temp = parseFloat(document.getElementById('sensor-temp').value) || 34.5;
  const moisture = parseFloat(document.getElementById('sensor-moisture').value) || 18.0;

  try {
    const res = await secureFetch('/api/agriculture/rules/evaluate', {
      method: 'POST',
      body: JSON.stringify({
        sensor_inputs: {
          temperature: temp,
          soil_moisture: moisture,
          time: new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' })
        }
      })
    });

    if (res.ok) {
      const data = await res.json();
      loadAgronomyRulesAndOrders();
      loadPosPromotions();
      if (data.triggered_rules.length > 0) {
        alert(`Rule Triggered! ${data.triggered_rules[0].action_message}`);
      } else {
        alert("Sensors evaluated: No rule thresholds breached.");
      }
    }
  } catch (err) {
    console.error(err);
  }
}

async function loadPosPromotions() {
  try {
    const res = await secureFetch('/api/pos/promotions');
    if (!res.ok) return;

    const items = await res.json();
    state.inventoryItems = items;

    // Update product select dropdown
    const select = document.getElementById('pos-product-select');
    if (select) {
      select.innerHTML = `<option value="">-- Select Product from Catalog --</option>` +
        items.map(item => {
          let label = `${item.name} ($${item.effective_price_usd.toFixed(2)})`;
          if (item.discount_applied > 0) {
            label += ` 🔥 Save $${item.discount_applied.toFixed(2)}`;
          }
          return `<option value="${item.id}" data-price="${item.effective_price_usd}" data-name="${item.name}">${label}</option>`;
        }).join('');
    }

    // Check if flash sale active
    const hasFlashSale = items.some(i => i.applied_promo_title && i.applied_promo_title.includes("Spoilage"));
    const flashBanner = document.getElementById('vpa34-flash-sale-banner');
    if (flashBanner) {
      flashBanner.style.display = hasFlashSale ? 'flex' : 'none';
    }
  } catch (err) {
    console.error(err);
  }
}

function initMobileNav() {
  const hamburger = document.getElementById('btn-mobile-hamburger');
  const sidebar = document.getElementById('app-sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  const collapseBtn = document.getElementById('btn-sidebar-collapse');
  const mainContent = document.querySelector('.main-content');
  
  if (collapseBtn && sidebar && mainContent) {
    collapseBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
      mainContent.classList.toggle('collapsed-rail');
    });
  }
  
  const featuredBtn = document.getElementById('btn-sidebar-featured');
  if (featuredBtn) {
    featuredBtn.addEventListener('click', () => {
      const vpa2Btn = document.getElementById('nav-vpa2');
      if (vpa2Btn) vpa2Btn.click();
    });
  }
  
  if (!hamburger || !sidebar || !backdrop) return;
  
  hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('mobile-open');
    backdrop.classList.toggle('active');
  });
  
  backdrop.addEventListener('click', () => {
    sidebar.classList.remove('mobile-open');
    backdrop.classList.remove('active');
  });
  
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.remove('mobile-open');
        backdrop.classList.remove('active');
      }
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
});




