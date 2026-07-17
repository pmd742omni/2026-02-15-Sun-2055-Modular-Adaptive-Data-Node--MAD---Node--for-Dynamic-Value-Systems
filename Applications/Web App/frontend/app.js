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
  initNavigation();
  initTime();
  initAgriModule();
  initSecurityModule();
  initPOSModule();
  
  // Dashboard mock controls
  document.getElementById('btn-mock-telemetry').addEventListener('click', runMockNodeActivity);
  document.getElementById('btn-clear-db').addEventListener('click', resetLocalCache);
  
  // Update summaries
  updateSummaries();
});

// --- NAVIGATION ---
function initNavigation() {
  const navButtons = document.querySelectorAll('.nav-btn');
  const sections = document.querySelectorAll('.view-section');
  const pageTitle = document.getElementById('page-title');
  const localStatus = document.getElementById('local-status');

  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.target;
      
      // Update sidebar state
      navButtons.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      
      // Update visible section
      sections.forEach(sec => {
        if (sec.id === `view-${target}`) {
          sec.classList.add('active');
          sec.setAttribute('aria-hidden', 'false');
        } else {
          sec.classList.remove('active');
          sec.setAttribute('aria-hidden', 'true');
        }
      });

      // Update page header
      state.activeView = target;
      let titleText = 'System Dashboard';
      if (target === 'vpa1') titleText = 'Agricultural Aid';
      if (target === 'vpa2') titleText = 'Perimeter Security';
      if (target === 'vpa3') titleText = 'Point of Sale';
      pageTitle.textContent = titleText;
    });
  });

  // Check if server is reachable (simulating offline mode)
  setTimeout(() => {
    localStatus.classList.remove('offline');
    localStatus.classList.add('online');
    localStatus.innerHTML = '<span class="status-dot"></span><span class="status-text">Hub Online (Offline-First)</span>';
  }, 1500);
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

// --- VPA 3.1: POINT OF SALE LEDGER ---
function initPOSModule() {
  const inputDueUsd = document.getElementById('cart-amount-usd');
  const inputZar = document.getElementById('rate-zar');
  const inputZwg = document.getElementById('rate-zwg');
  const inputTenderUsd = document.getElementById('tender-usd');
  const inputTenderZar = document.getElementById('tender-zar');
  const inputTenderZwg = document.getElementById('tender-zwg');
  const btnProcess = document.getElementById('btn-process-sale');
  
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
  
  btnProcess.addEventListener('click', () => {
    const dueUsd = parseFloat(inputDueUsd.value) || 0;
    const rateZar = parseFloat(inputZar.value) || 18;
    const rateZwg = parseFloat(inputZwg.value) || 25;
    const tenderUsd = parseFloat(inputTenderUsd.value) || 0;
    const tenderZar = parseFloat(inputTenderZar.value) || 0;
    const tenderZwg = parseFloat(inputTenderZwg.value) || 0;
    
    const outcome = recalculateTender(dueUsd, rateZar, rateZwg, tenderUsd, tenderZar, tenderZwg);
    
    if (outcome.paid) {
      // Record transaction
      const newTx = {
        id: `tx_${Date.now()}`,
        time: new Date().toLocaleTimeString(),
        dueUsd: dueUsd,
        tenderedUsdEquiv: outcome.tenderedUsd,
        changeUsd: outcome.changeUsd
      };
      
      state.pos.transactions.unshift(newTx);
      
      // Persist to localStorage
      localStorage.setItem('madn_transactions', JSON.stringify(state.pos.transactions));
      
      // Update transaction list
      renderTransactionHistory();
      
      // Flash inputs to signal success
      btnProcess.textContent = "Transaction Logged! ✓";
      btnProcess.classList.add('active');
      setTimeout(() => {
        btnProcess.textContent = "Commit Sale & Calculate Change";
        btnProcess.classList.remove('active');
      }, 1500);
    }
  });

  // Load from local storage
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
}
