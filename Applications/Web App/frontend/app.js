/**
 * MADN Web Application - Stage 1 Core SPA Logic
 * Coordinates RBAC, Dynamic Decay Pricing, Agricultural Costs,
 * Visitor Gatekeeper, Social Media Hub, and Cluster Node Discovery.
 */

// --- GLOBAL APPLICATION STATE ---
const state = {
  activeView: 'dashboard',
  currentRole: 'admin',
  activeBusinessId: 'biz-green-valley',
  businesses: [],
  user: { username: 'admin', role: 'admin' },
  plantings: [],
  harvests: [],
  dispositions: [],
  activeVisitors: [],
  allVisitors: [],
  socialPosts: [],
  socialStories: [],
  clusterNodes: [],
  posProducts: [],
  cart: [],
  cartTotalUsd: 0.0,
  currentReceipt: null,
  exchangeRates: { ZAR: 18.50, ZWG: 26.50 },
  selectedTipCurrency: 'USD'
};

// --- BULAWAYO CLIMATE DATA ---
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

// --- UNIVERSAL LATEX & MATHEMATICAL EQUATION RENDERER ---
function renderLatexInUI(rootEl) {
  const container = rootEl || document.body;
  if (!container) return;

  // 1. If KaTeX Auto-Renderer is available, run it
  if (typeof window.renderMathInElement === 'function') {
    try {
      window.renderMathInElement(container, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false }
        ],
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option"],
        throwOnError: false
      });
      return;
    } catch (e) {
      console.warn("KaTeX render notice:", e);
    }
  }

  // 2. High-Fidelity Standalone Fallback Parser for offline/instant rendering
  const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
  const textNodes = [];
  let node;
  while ((node = walker.nextNode())) {
    const p = node.parentElement;
    if (p && !['SCRIPT', 'STYLE', 'CODE', 'PRE', 'TEXTAREA', 'INPUT', 'OPTION'].includes(p.tagName)) {
      if (node.nodeValue && (/\\\(|\$\$|\$|\\\[|\\frac|\\ge|\\le|\\lambda|\\mu|\\cdot|\\text\{/.test(node.nodeValue))) {
        textNodes.push(node);
      }
    }
  }

  textNodes.forEach(textNode => {
    let raw = textNode.nodeValue;
    if (!raw) return;

    // Convert \( ... \) and $ ... $ LaTeX syntax into formatted HTML
    let transformed = raw.replace(/\\?\(([\s\S]*?)\\?\)|(?:\$([^\$]+?)\$)/g, (match, p1, p2) => {
      let eq = (p1 !== undefined ? p1 : p2).trim();
      return formatLatexToHtml(eq);
    });

    if (transformed !== raw) {
      const span = document.createElement('span');
      span.innerHTML = transformed;
      if (textNode.parentNode) {
        textNode.parentNode.replaceChild(span, textNode);
      }
    }
  });
}

function formatLatexToHtml(latex) {
  let s = latex
    .replace(/\\text\{([^}]+)\}/g, '$1')
    .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, '<span style="display:inline-block;vertical-align:middle;text-align:center;font-size:0.9em;padding:0 2px;"><span style="display:block;border-bottom:1px solid currentColor;padding:0 1px;">$1</span><span style="display:block;padding:0 1px;">$2</span></span>')
    .replace(/\\cdot/g, '&middot;')
    .replace(/\\times/g, '&times;')
    .replace(/\\ge/g, '&ge;')
    .replace(/\\le/g, '&le;')
    .replace(/\\lambda/g, '&lambda;')
    .replace(/\\mu/g, '&mu;')
    .replace(/\\max/g, 'max')
    .replace(/\\min/g, 'min')
    .replace(/\\left\(/g, '(')
    .replace(/\\right\)/g, ')')
    .replace(/\\_|\_/g, '_')
    .replace(/([a-zA-Z])_\{([^}]+)\}/g, '<i>$1</i><sub>$2</sub>')
    .replace(/([a-zA-Z])_([a-zA-Z0-9])/g, '<i>$1</i><sub>$2</sub>')
    .replace(/\^\{([^}]+)\}/g, '<sup>$1</sup>')
    .replace(/\^([a-zA-Z0-9\-]+)/g, '<sup>$1</sup>');

  // Wrap variables
  s = s.replace(/\b([PCEFMNt])\b/g, '<i>$1</i>');
  return `<span class="math-expr">${s}</span>`;
}

window.renderLatexInUI = renderLatexInUI;

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
  initAuthSystem();
  initLoginPossibilitiesTicker();
  initNavigation();
  initAgriModule();
  initSecurityModule();
  initSocialModule();
  initPOSModule();
  initClusterModule();

  // Initial Mathematical LaTeX Rendering pass
  renderLatexInUI();

  // Discover local network addresses in background
  fetchNetworkInfo();

  // Check active session & load data ONLY if user is authenticated
  checkActiveSession().then((user) => {
    if (user) {
      loadAllSubsystemData();
      renderLatexInUI();
    }
  });

  // Ticker for continuous decay update every 10 seconds
  setInterval(() => {
    if (state.activeView === 'vpa3' && state.user) {
      loadPosProducts();
      loadMarketplaceCatalog();
    }
  }, 10000);
});

// --- CORE SECURE FETCH HELPERS ---
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

let pendingStepUpResolve = null;
let pendingStepUpReject = null;

async function secureFetch(url, options = {}) {
  const csrfToken = getCookie("csrf_token");
  if (!options.headers) options.headers = {};
  if (csrfToken) {
    options.headers["X-CSRF-Token"] = csrfToken;
  }
  if (!options.headers["Content-Type"] && !(options.body instanceof FormData)) {
    options.headers["Content-Type"] = "application/json";
  }

  try {
    const response = await fetch(url, options);
    if (response.status === 401) {
      showLoginOverlay();
      throw new Error("Unauthorized");
    }
    if (response.status === 403) {
      const errData = await response.json().catch(() => ({}));
      const detail = errData.detail || "";
      if (detail.includes("step-up") || detail.includes("elevate")) {
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

// --- AUTHENTICATION & SESSION ---
function initAuthSystem() {
  const btnLogin = document.getElementById('btn-login-submit');
  const formLogin = document.getElementById('form-login');

  const executeLogin = async () => {
    const u = document.getElementById('login-username').value.trim();
    const p = document.getElementById('login-password').value;
    const mfa = document.getElementById('login-mfa-token').value.trim();
    const errBox = document.getElementById('login-error');

    if (!u || !p) {
      if (errBox) {
        errBox.style.display = 'block';
        errBox.innerText = "Please enter both username and password.";
      }
      return;
    }

    if (errBox) errBox.style.display = 'none';
    if (btnLogin) {
      btnLogin.disabled = true;
      btnLogin.innerText = "Signing in...";
    }

    try {
      const body = { username: u, password: p };
      if (mfa) body.totp_token = mfa;

      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Authentication failed." }));
        if (data.detail && data.detail.includes("MFA code required")) {
          document.getElementById('login-mfa-group').style.display = 'block';
          if (errBox) {
            errBox.style.display = 'block';
            errBox.innerText = "MFA code required for this account.";
          }
          return;
        }
        if (errBox) {
          errBox.style.display = 'block';
          errBox.innerText = data.detail || "Authentication failed.";
        }
        return;
      }

      const data = await res.json();
      state.user = data;
      state.currentRole = data.role;
      updateUserUI(data);
      hideLoginOverlay();
      loadAllSubsystemData();
    } catch (e) {
      if (errBox) {
        errBox.style.display = 'block';
        errBox.innerText = e.message || "Network error. Server might be restarting.";
      }
    } finally {
      if (btnLogin) {
        btnLogin.disabled = false;
        btnLogin.innerText = "Sign In to Your Workspace 🚀";
      }
    }
  };

  if (btnLogin) {
    btnLogin.addEventListener('click', (e) => {
      e.preventDefault();
      executeLogin();
    });
  }

  if (formLogin) {
    formLogin.addEventListener('submit', (e) => {
      e.preventDefault();
      executeLogin();
    });
  }

  const btnLogout = document.getElementById('btn-logout');
  if (btnLogout) {
    btnLogout.addEventListener('click', async (e) => {
      e.preventDefault();
      try {
        await secureFetch("/api/auth/logout", { method: "POST" });
      } catch (err) {
        try {
          await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
        } catch (e2) {}
      }
      showLoginOverlay();
    });
  }

  const linkGotoReg = document.getElementById('link-goto-register');
  if (linkGotoReg) {
    linkGotoReg.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('card-login').style.display = 'none';
      document.getElementById('card-register').style.display = 'block';
      const regUser = document.getElementById('register-username');
      if (regUser) regUser.focus();
    });
  }

  const linkGotoLog = document.getElementById('link-goto-login');
  if (linkGotoLog) {
    linkGotoLog.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('card-register').style.display = 'none';
      document.getElementById('card-login').style.display = 'block';
    });
  }

  const btnRegSubmit = document.getElementById('btn-register-submit');
  if (btnRegSubmit) {
    btnRegSubmit.addEventListener('click', handleRegister);
  }

  const btnChangePwSubmit = document.getElementById('btn-change-pw-submit');
  if (btnChangePwSubmit) {
    btnChangePwSubmit.addEventListener('click', (e) => {
      e.preventDefault();
      submitChangePassword();
    });
  }

  const btnChangePwCancel = document.getElementById('btn-change-pw-cancel');
  if (btnChangePwCancel) {
    btnChangePwCancel.addEventListener('click', (e) => {
      e.preventDefault();
      hideModals();
    });
  }
}

async function handleRegister(e) {
  if (e) e.preventDefault();
  const username = document.getElementById('register-username').value.trim();
  const password = document.getElementById('register-password').value;
  const confirm = document.getElementById('register-confirm').value;
  const errEl = document.getElementById('register-error');
  const succEl = document.getElementById('register-success');

  if (errEl) { errEl.style.display = 'none'; errEl.innerText = ''; }
  if (succEl) { succEl.style.display = 'none'; succEl.innerText = ''; }

  if (!username) {
    if (errEl) { errEl.innerText = 'Please enter a username.'; errEl.style.display = 'block'; }
    return;
  }

  if (password.length < 12) {
    if (errEl) { errEl.innerText = 'Password must be at least 12 characters.'; errEl.style.display = 'block'; }
    return;
  }

  if (password !== confirm) {
    if (errEl) { errEl.innerText = 'Passwords do not match.'; errEl.style.display = 'block'; }
    return;
  }

  try {
    const res = await secureFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ username: username, password: password })
    });

    const data = await res.json();
    if (res.ok) {
      if (succEl) {
        succEl.innerText = data.message || 'Registration successful! Switching to login...';
        succEl.style.display = 'block';
      }
      setTimeout(() => {
        document.getElementById('form-register').reset();
        if (succEl) succEl.style.display = 'none';
        document.getElementById('card-register').style.display = 'none';
        document.getElementById('card-login').style.display = 'block';
        document.getElementById('login-username').value = username;
        document.getElementById('login-password').value = '';
        const pw = document.getElementById('login-password');
        if (pw) pw.focus();
      }, 1500);
    } else {
      if (errEl) {
        errEl.innerText = data.detail || 'Registration failed.';
        errEl.style.display = 'block';
      }
    }
  } catch (err) {
    if (errEl) {
      errEl.innerText = 'Network error during registration: ' + err.message;
      errEl.style.display = 'block';
    }
  }
}

function quickFillLogin(role) {
  document.getElementById('login-username').value = role;
  document.getElementById('login-password').value = "";
  const pwInput = document.getElementById('login-password');
  if (pwInput) pwInput.focus();
}

async function checkActiveSession() {
  try {
    const res = await fetch("/api/auth/session");
    if (res.ok) {
      const user = await res.json();
      state.user = user;
      state.currentRole = user.role;
      updateUserUI(user);
      hideLoginOverlay();
      return user;
    } else {
      showLoginOverlay();
      return null;
    }
  } catch (e) {
    showLoginOverlay();
    return null;
  }
}

function showLoginOverlay() {
  state.user = null;
  state.currentRole = 'guest';

  // Securely clear all input fields (passwords, usernames, OTP tokens)
  const pwInput = document.getElementById('login-password');
  const userInput = document.getElementById('login-username');
  const totpInput = document.getElementById('login-totp');
  const regPw = document.getElementById('register-password');
  const regConfirm = document.getElementById('register-confirm');
  const regUser = document.getElementById('register-username');
  const errBox = document.getElementById('login-error');
  const mfaGroup = document.getElementById('login-mfa-group');

  if (pwInput) pwInput.value = '';
  if (userInput) userInput.value = '';
  if (totpInput) totpInput.value = '';
  if (regPw) regPw.value = '';
  if (regConfirm) regConfirm.value = '';
  if (regUser) regUser.value = '';
  if (errBox) { errBox.style.display = 'none'; errBox.innerText = ''; }
  if (mfaGroup) mfaGroup.style.display = 'none';

  // Explicitly wipe client session and CSRF cookies across all path and domain configurations
  const expireStr = "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
  document.cookie = "madn_session" + expireStr;
  document.cookie = "madn_session" + expireStr + " SameSite=Lax;";
  document.cookie = "madn_session" + expireStr + " SameSite=Lax; Secure;";
  document.cookie = "madn_session" + expireStr + " SameSite=Strict;";
  document.cookie = "madn_session" + expireStr + " SameSite=Strict; Secure;";
  document.cookie = "csrf_token" + expireStr;
  document.cookie = "csrf_token" + expireStr + " SameSite=Lax;";
  document.cookie = "csrf_token" + expireStr + " SameSite=Lax; Secure;";
  document.cookie = "csrf_token" + expireStr + " SameSite=Strict;";
  document.cookie = "csrf_token" + expireStr + " SameSite=Strict; Secure;";

  const authOverlay = document.getElementById('auth-overlay');
  const cardLogin = document.getElementById('card-login');
  const cardRegister = document.getElementById('card-register');

  if (authOverlay) authOverlay.style.display = 'flex';
  if (cardLogin) cardLogin.style.display = 'block';
  if (cardRegister) cardRegister.style.display = 'none';

  hideModals();

  if (userInput) userInput.focus();
}

function hideLoginOverlay() {
  document.getElementById('auth-overlay').style.display = 'none';
}

function updateUserUI(user) {
  const profileUser = document.getElementById('profile-username');
  const profileRole = document.getElementById('profile-role');
  const avatarPic = document.getElementById('user-avatar-pic');
  const roleSelect = document.getElementById('role-switcher-select');

  if (profileUser) profileUser.innerText = user.username;
  if (avatarPic) avatarPic.innerText = user.username.charAt(0).toUpperCase();

  const roleClassMap = {
    admin: 'role-badge-admin',
    agronomist: 'role-badge-agronomist',
    guard: 'role-badge-guard',
    merchant: 'role-badge-merchant',
    customer: 'role-badge-customer',
    guest: 'role-badge-guest'
  };

  if (profileRole) {
    profileRole.className = `role-pill-badge ${roleClassMap[user.role] || 'role-badge-guest'}`;
    profileRole.innerText = user.role.toUpperCase();
  }

  if (roleSelect) {
    roleSelect.value = user.role;
  }

  // Adjust sidebar permissions
  const navAdmin = document.getElementById('nav-admin');
  if (navAdmin) {
    navAdmin.style.display = (user.role === 'admin') ? 'flex' : 'none';
  }
}

function handleLiveRoleSwitch(newRole) {
  quickFillLogin(newRole);
}

function showStepUpModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-step-up').style.display = 'block';
  document.getElementById('modal-change-password').style.display = 'none';
  document.getElementById('modal-mfa-setup').style.display = 'none';
  document.getElementById('modal-social-tip').style.display = 'none';
  document.getElementById('modal-create-post').style.display = 'none';
  const recEl = document.getElementById('modal-thermal-receipt');
  if (recEl) recEl.style.display = 'none';
}

function hideModals() {
  const overlay = document.getElementById('modal-overlay');
  if (overlay) overlay.style.display = 'none';

  const modalIds = [
    'modal-step-up',
    'modal-change-password',
    'modal-mfa-setup',
    'modal-social-tip',
    'modal-create-post',
    'modal-thermal-receipt',
    'modal-assign-operator',
    'modal-p2p-transfer',
    'modal-deposit-voucher',
    'modal-generate-portable-node',
    'modal-network-qr',
    'modal-new-planting',
    'modal-checkin-visitor',
    'modal-create-business',
    'modal-operator-profile'
  ];

  modalIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });

  if (pendingStepUpReject) {
    pendingStepUpReject();
    pendingStepUpResolve = null;
    pendingStepUpReject = null;
  }
}

// --- OPERATOR PROFILE & SECURITY SETTINGS ---
async function openProfileModal() {
  try {
    const res = await secureFetch("/api/user/profile");
    if (!res.ok) {
      showErrorToast("Failed to load operator profile.");
      return;
    }
    const profile = await res.json();
    state.operatorProfile = profile;

    // Populate modal elements
    const avatarEl = document.getElementById('profile-modal-avatar');
    const titleEl = document.getElementById('profile-modal-title');
    const roleBadgeEl = document.getElementById('profile-modal-role-badge');
    const accEl = document.getElementById('profile-modal-acc-num');
    const usdEl = document.getElementById('profile-modal-bal-usd');
    const zarEl = document.getElementById('profile-modal-bal-zar');
    const zwgEl = document.getElementById('profile-modal-bal-zwg');

    const fnInput = document.getElementById('profile-input-fullname');
    const unInput = document.getElementById('profile-input-username');
    const phInput = document.getElementById('profile-input-phone');
    const emInput = document.getElementById('profile-input-email');
    const pinInput = document.getElementById('profile-input-pin');

    const displayName = profile.full_name || profile.username;
    if (avatarEl) avatarEl.innerText = displayName.charAt(0).toUpperCase();
    if (titleEl) titleEl.innerText = `${displayName}'s Profile`;
    if (roleBadgeEl) {
      roleBadgeEl.innerText = (profile.role || 'OPERATOR').toUpperCase();
      roleBadgeEl.className = `role-pill-badge role-badge-${profile.role || 'admin'}`;
    }
    if (accEl) accEl.innerText = profile.account_number || "ACC-2026-******";
    if (usdEl) usdEl.innerText = `$${(profile.wallet?.balance_usd || 0).toFixed(2)}`;
    if (zarEl) zarEl.innerText = `R ${(profile.wallet?.balance_zar || 0).toFixed(2)}`;
    if (zwgEl) zwgEl.innerText = `${(profile.wallet?.balance_zwg || 0).toFixed(2)}`;

    if (fnInput) fnInput.value = profile.full_name || '';
    if (unInput) unInput.value = profile.username || '';
    if (phInput) phInput.value = profile.phone || '';
    if (emInput) emInput.value = profile.email || '';
    if (pinInput) pinInput.value = profile.pin_set ? '1234' : '';

    // Show modal
    hideModals();
    const overlay = document.getElementById('modal-overlay');
    const modal = document.getElementById('modal-operator-profile');
    if (overlay) overlay.style.display = 'flex';
    if (modal) modal.style.display = 'block';
  } catch (e) {
    showErrorToast(e.message || "Failed to load operator profile.");
  }
}

async function submitSaveProfile() {
  const fnInput = document.getElementById('profile-input-fullname');
  const unInput = document.getElementById('profile-input-username');
  const phInput = document.getElementById('profile-input-phone');
  const emInput = document.getElementById('profile-input-email');
  const pinInput = document.getElementById('profile-input-pin');

  const payload = {
    full_name: fnInput ? fnInput.value.trim() : "",
    username: unInput ? unInput.value.trim() : "",
    phone: phInput ? phInput.value.trim() : "",
    email: emInput ? emInput.value.trim() : "",
    pin: pinInput ? pinInput.value.trim() : ""
  };

  try {
    const res = await secureFetch("/api/user/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      showErrorToast(data.detail || "Failed to update profile.");
      return;
    }

    showSuccessToast("Operator profile updated successfully! 💾");
    if (data.profile) {
      state.user.username = data.profile.username;
      updateUserUI(state.user);
    }
    hideModals();
  } catch (e) {
    showErrorToast(e.message || "Network error updating profile.");
  }
}

function openChangePasswordModal() {
  hideModals();
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('modal-change-password');
  const errBox = document.getElementById('change-pw-error');
  if (errBox) { errBox.style.display = 'none'; errBox.innerText = ''; }

  const curr = document.getElementById('change-pw-current');
  const nw = document.getElementById('change-pw-new');
  if (curr) curr.value = '';
  if (nw) nw.value = '';

  if (overlay) overlay.style.display = 'flex';
  if (modal) modal.style.display = 'block';
}

async function submitChangePassword() {
  const curr = document.getElementById('change-pw-current')?.value || '';
  const nw = document.getElementById('change-pw-new')?.value || '';
  const errBox = document.getElementById('change-pw-error');

  if (errBox) { errBox.style.display = 'none'; errBox.innerText = ''; }

  if (!curr) {
    if (errBox) { errBox.style.display = 'block'; errBox.innerText = "Please enter your current password."; }
    return;
  }
  if (!nw || nw.length < 12) {
    if (errBox) { errBox.style.display = 'block'; errBox.innerText = "New password must be at least 12 characters."; }
    return;
  }

  try {
    const res = await secureFetch("/api/user/change-password", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: curr, new_password: nw })
    });

    const data = await res.json();
    if (!res.ok) {
      if (errBox) { errBox.style.display = 'block'; errBox.innerText = data.detail || "Password change failed."; }
      return;
    }

    showSuccessToast("Password updated successfully! 🔑");
    hideModals();
  } catch (e) {
    if (errBox) { errBox.style.display = 'block'; errBox.innerText = e.message || "Network error changing password."; }
  }
}

// --- MULTI-BUSINESS / TENANCY HANDLERS ---
async function loadBusinesses() {
  try {
    const res = await secureFetch("/api/businesses");
    if (!res.ok) return;
    const data = await res.json();
    state.businesses = data.businesses || [];

    const select = document.getElementById('header-business-select');
    const adminBizName = document.getElementById('admin-current-biz-name');

    if (select) {
      if (state.businesses.length === 0) {
        select.innerHTML = `<option value="">➕ Register Business</option>`;
        state.activeBusinessId = null;
        if (adminBizName) adminBizName.innerText = "No Registered Business";
      } else {
        if (!state.activeBusinessId || !state.businesses.find(b => b.id === state.activeBusinessId)) {
          state.activeBusinessId = state.businesses[0].id;
        }

        select.innerHTML = state.businesses.map(b => `
          <option value="${b.id}" ${b.id === state.activeBusinessId ? 'selected' : ''}>${b.name.length > 22 ? b.name.substring(0, 20) + '...' : b.name}</option>
        `).join('') + `<option value="__NEW__">➕ Register New Store...</option>`;

        const activeBiz = state.businesses.find(b => b.id === state.activeBusinessId);
        if (adminBizName && activeBiz) {
          adminBizName.innerText = activeBiz.name;
        }
      }
    }
  } catch (e) {
    console.error("Failed to load businesses:", e);
  }
}

function handleLiveBusinessSwitch(bizId) {
  if (bizId === '__NEW__' || !bizId) {
    openCreateBusinessModal();
    return;
  }

  state.activeBusinessId = bizId;
  console.log(`[MADN] Active business switched to: ${bizId}`);
  
  // Update admin header text
  const currentBiz = state.businesses.find(b => b.id === bizId);
  const nameEl = document.getElementById('admin-current-biz-name');
  if (nameEl && currentBiz) {
    nameEl.innerText = currentBiz.name;
  }

  loadPosProducts();
  loadMarketplaceCatalog();
  loadPlantings();
  loadHarvests();
  loadBusinessOperators(bizId);
  updateUIPermissions();
}

function openCreateBusinessModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-create-business').style.display = 'block';
  setTimeout(() => {
    const el = document.getElementById('new-biz-name');
    if (el) el.focus();
  }, 100);
}

async function submitCreateBusiness() {
  const name = document.getElementById('new-biz-name').value.trim();
  const category = document.getElementById('new-biz-category').value;
  const currency = document.getElementById('new-biz-currency').value;
  const phone = document.getElementById('new-biz-phone').value.trim();
  const taxId = document.getElementById('new-biz-tax-id').value.trim();
  const address = document.getElementById('new-biz-address').value.trim();
  const header = document.getElementById('new-biz-header').value.trim();
  const footer = document.getElementById('new-biz-footer').value.trim();

  if (!name) {
    alert("Please enter a Business Name.");
    return;
  }

  try {
    const res = await secureFetch("/api/businesses", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        category: category,
        currency_preference: currency,
        contact_phone: phone,
        tax_id: taxId,
        location_address: address,
        receipt_header: header,
        receipt_footer_note: footer
      })
    });

    if (res.ok) {
      const data = await res.json();
      hideModals();
      document.getElementById('form-create-business').reset();
      await loadBusinesses();
      if (data.business && data.business.id) {
        handleLiveBusinessSwitch(data.business.id);
      }
      alert(`Business profile "${name}" successfully registered and synchronized to Data Node!`);
    } else {
      const err = await res.json();
      alert("Failed to create business: " + (err.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Network error creating business: " + e.message);
  }
}

// --- BUSINESS OPERATOR DELEGATION & PERMISSIONS ---
async function loadBusinessOperators(bizId = null) {
  const targetBiz = bizId || state.activeBusinessId;
  const tbody = document.getElementById('business-operators-table-body');
  if (!tbody) return;

  if (!targetBiz) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">No business selected. Register a business to assign operators.</td></tr>`;
    return;
  }

  try {
    const res = await secureFetch(`/api/businesses/${targetBiz}/operators`);
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">Operator roster restricted to Business Administrators.</td></tr>`;
      return;
    }

    const data = await res.json();
    const ops = data.operators || [];

    if (ops.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">No delegated operators assigned yet. Click "Grant Operator Access" to add staff.</td></tr>`;
      return;
    }

    const permLabels = {
      pos: '🏪 POS & Inv',
      vouchers: '🎟️ Vouchers',
      agriculture: '🌾 Agri',
      security: '🛡️ Security',
      social: '🌐 Social',
      reports: '📊 Reports',
      admin: '👑 Full Admin'
    };

    tbody.innerHTML = ops.map(op => {
      const perms = op.permissions || [];
      const badges = perms.map(p => `<span class="decay-discount-tag" style="background: rgba(0,229,255,0.15); color: var(--accent-cyan); margin: 2px;">${permLabels[p] || p}</span>`).join(' ');
      return `
        <tr>
          <td><strong style="color: #fff;">@${op.username}</strong></td>
          <td><span class="role-pill-badge" style="text-transform: capitalize;">${op.role_in_business}</span></td>
          <td>${badges || '<span style="color: var(--text-muted);">None</span>'}</td>
          <td><small style="color: var(--text-muted);">${op.granted_by}</small></td>
          <td><span style="color: #10b981; font-weight: 600;">Active</span></td>
          <td style="text-align: center;">
            <button class="btn-pill-small" style="color: #f87171;" onclick="revokeOperator('${op.username}')">Revoke ✕</button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error("Failed to load business operators:", e);
  }
}

function openAssignOperatorModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-assign-operator').style.display = 'block';
  applyRolePreset('cashier');
}

function applyRolePreset(role) {
  const pPos = document.getElementById('perm-pos');
  const pVouch = document.getElementById('perm-vouchers');
  const pAgri = document.getElementById('perm-agri');
  const pSec = document.getElementById('perm-security');
  const pSoc = document.getElementById('perm-social');
  const pRep = document.getElementById('perm-reports');

  if (role === 'cashier') {
    if (pPos) pPos.checked = true;
    if (pVouch) pVouch.checked = true;
    if (pAgri) pAgri.checked = false;
    if (pSec) pSec.checked = false;
    if (pSoc) pSoc.checked = false;
    if (pRep) pRep.checked = false;
  } else if (role === 'agronomist') {
    if (pPos) pPos.checked = false;
    if (pVouch) pVouch.checked = false;
    if (pAgri) pAgri.checked = true;
    if (pSec) pSec.checked = false;
    if (pSoc) pSoc.checked = true;
    if (pRep) pRep.checked = true;
  } else if (role === 'guard') {
    if (pPos) pPos.checked = false;
    if (pVouch) pVouch.checked = false;
    if (pAgri) pAgri.checked = false;
    if (pSec) pSec.checked = true;
    if (pSoc) pSoc.checked = true;
    if (pRep) pRep.checked = false;
  } else if (role === 'manager') {
    if (pPos) pPos.checked = true;
    if (pVouch) pVouch.checked = true;
    if (pAgri) pAgri.checked = true;
    if (pSec) pSec.checked = true;
    if (pSoc) pSoc.checked = true;
    if (pRep) pRep.checked = true;
  }
}

async function submitAssignOperator() {
  const username = document.getElementById('op-assign-username')?.value;
  const role = document.getElementById('op-assign-role')?.value || 'operator';
  
  const perms = [];
  if (document.getElementById('perm-pos')?.checked) perms.push('pos', 'inventory');
  if (document.getElementById('perm-vouchers')?.checked) perms.push('vouchers');
  if (document.getElementById('perm-agri')?.checked) perms.push('agriculture');
  if (document.getElementById('perm-security')?.checked) perms.push('security');
  if (document.getElementById('perm-social')?.checked) perms.push('social');
  if (document.getElementById('perm-reports')?.checked) perms.push('reports');

  if (!username) {
    alert("Please select an operator username.");
    return;
  }

  try {
    const res = await secureFetch(`/api/businesses/${state.activeBusinessId}/operators`, {
      method: "POST",
      body: JSON.stringify({
        username: username,
        role_in_business: role,
        permissions: perms
      })
    });

    const data = await res.json();
    if (res.ok && data.status === 'success') {
      alert(`Operator @${username} granted ${role} access with permissions: ${perms.join(', ')}`);
      hideModals();
      loadBusinessOperators();
    } else {
      alert("Failed to assign operator: " + (data.detail || "Error occurred"));
    }
  } catch (e) {
    alert("Assignment error: " + e.message);
  }
}

async function revokeOperator(username) {
  if (!confirm(`Are you sure you want to revoke access for @${username} in this business?`)) return;

  try {
    const res = await secureFetch(`/api/businesses/${state.activeBusinessId}/operators/${username}`, {
      method: "DELETE"
    });

    if (res.ok) {
      alert(`Access revoked for @${username}`);
      loadBusinessOperators();
    } else {
      const data = await res.json();
      alert("Revocation failed: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Revocation error: " + e.message);
  }
}

// --- ADMIN USER & GLOBAL PRIVILEGE MANAGEMENT ---
async function loadAdminUsers() {
  const tbody = document.getElementById('admin-users-table-body');
  if (!tbody) return;

  try {
    const res = await secureFetch("/api/admin/users");
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">User directory restricted to Administrators.</td></tr>`;
      return;
    }

    const data = await res.json();
    const users = data.users || [];

    if (users.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 16px;">No registered users found.</td></tr>`;
      return;
    }

    tbody.innerHTML = users.map(u => {
      const isSelf = (state.user && state.user.username === u.username);
      const isStatusActive = (u.status === 'active');
      const createdStr = u.created_at ? new Date(u.created_at * 1000).toISOString().substring(0, 10) : 'Genesis';

      return `
        <tr>
          <td><code style="color: var(--accent-cyan); font-weight: 700;">#${u.id}</code></td>
          <td><strong style="color: #fff;">@${u.username}</strong> ${isSelf ? '<span style="color: var(--accent-cyan); font-size: 0.72rem;">(You)</span>' : ''}</td>
          <td>
            <select id="user-role-select-${u.id}" class="role-switcher-select" style="padding: 4px 8px; font-size: 0.78rem;" ${isSelf ? 'disabled title="Cannot demote yourself"' : ''}>
              <option value="admin" ${u.role === 'admin' ? 'selected' : ''}>👑 Admin</option>
              <option value="agronomist" ${u.role === 'agronomist' ? 'selected' : ''}>🌾 Agronomist</option>
              <option value="guard" ${u.role === 'guard' ? 'selected' : ''}>🛡️ Guard</option>
              <option value="merchant" ${u.role === 'merchant' ? 'selected' : ''}>🏪 Merchant</option>
              <option value="customer" ${u.role === 'customer' ? 'selected' : ''}>🛒 Customer</option>
              <option value="guest" ${u.role === 'guest' ? 'selected' : ''}>👤 Guest</option>
            </select>
          </td>
          <td>
            <span style="display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; background: ${isStatusActive ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}; color: ${isStatusActive ? '#10b981' : '#f87171'};">
              ${u.status.toUpperCase()}
            </span>
          </td>
          <td><small style="color: var(--text-muted);">${createdStr}</small></td>
          <td style="text-align: center;">
            <div style="display: inline-flex; gap: 6px;">
              <button class="btn-pill-small" onclick="saveAdminUserRole(${u.id}, '${u.username}')" ${isSelf ? 'disabled' : ''}>Save Role 💾</button>
              <button class="btn-pill-small ${isStatusActive ? 'danger' : ''}" onclick="toggleAdminUserStatus(${u.id}, '${u.status}', '${u.username}')" ${isSelf ? 'disabled' : ''}>
                ${isStatusActive ? 'Suspend ⛔' : 'Activate ✅'}
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Also populate operator assignment dropdown
    const assignSelect = document.getElementById('assign-operator-username');
    if (assignSelect) {
      assignSelect.innerHTML = users.map(u => `<option value="${u.username}">@${u.username} (${u.role})</option>`).join('');
    }
  } catch (e) {
    console.error("Failed to load admin users:", e);
  }
}

async function saveAdminUserRole(userId, username) {
  const select = document.getElementById(`user-role-select-${userId}`);
  if (!select) return;
  const newRole = select.value;

  try {
    const res = await secureFetch(`/api/admin/users/${userId}/role`, {
      method: "PUT",
      body: JSON.stringify({ role: newRole })
    });

    const data = await res.json();
    if (res.ok) {
      alert(`User @${username} role successfully updated to "${newRole}".`);
      loadAdminUsers();
    } else {
      alert("Failed to update role: " + (data.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Role update error: " + e.message);
  }
}

async function toggleAdminUserStatus(userId, currentStatus, username) {
  const newStatus = currentStatus === 'active' ? 'disabled' : 'active';
  if (!confirm(`Are you sure you want to change @${username} account status to "${newStatus}"?`)) return;

  try {
    const res = await secureFetch(`/api/admin/users/${userId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status: newStatus })
    });

    const data = await res.json();
    if (res.ok) {
      alert(`User @${username} account is now ${newStatus.toUpperCase()}.`);
      loadAdminUsers();
    } else {
      alert("Failed to update status: " + (data.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Status update error: " + e.message);
  }
}

async function updateUIPermissions() {
  try {
    const res = await secureFetch(`/api/businesses/${state.activeBusinessId}/my-permissions`);
    if (!res.ok) return;
    const data = await res.json();
    state.myPermissions = data.permissions || [];
    state.isBusinessAdmin = data.is_business_admin || false;
  } catch (e) {
    console.error("Failed to update UI permissions:", e);
  }
}

// --- NAVIGATION ---
function initNavigation() {
  window.switchViewInternal = function(target) {
    state.activeView = target;
    document.querySelectorAll('.nav-item-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.target === target);
    });
    document.querySelectorAll('.mobile-nav-item').forEach(item => {
      item.classList.toggle('active', item.dataset.target === target);
    });
    document.querySelectorAll('.view-section').forEach(sec => {
      const isActive = (sec.id === `view-${target}`);
      sec.classList.toggle('active', isActive);
      sec.style.display = isActive ? 'block' : 'none';
    });
    if (typeof updateSubNav === 'function') {
      updateSubNav(target);
    }
    if (target === 'admin') {
      loadCurrencies();
      loadAdminUsers();
      loadBusinessOperators();
    }
    if (target === 'banking') {
      loadCurrencies();
      loadCustomerWallet();
      loadCustomerReceipts();
      loadWalletLedger();
    }
    if (target === 'cluster') {
      loadDiscoveredClusterNodes();
      loadExportedNodePackages();
    }
    // Re-render LaTeX math formulas in active view
    setTimeout(() => {
      renderLatexInUI();
    }, 50);
  };
}

function handleQuickCTA() {
  if (state.currentRole === 'agronomist') {
    switchView('vpa1');
    togglePlantingForm();
  } else if (state.currentRole === 'guard') {
    switchView('vpa2');
  } else if (state.currentRole === 'merchant') {
    switchView('vpa3');
  } else if (state.currentRole === 'customer') {
    switchView('banking');
    openTopupModal();
  } else {
    openCreatePostModal('thread');
  }
}

function loadAllSubsystemData() {
  loadCurrencies();
  loadBusinesses();
  loadBusinessOperators();
  loadAdminUsers();
  updateUIPermissions();
  loadCustomerWallet();
  loadCustomerReceipts();
  loadWalletLedger();
  loadPlantings();
  loadHarvests();
  loadDispositions();
  loadActiveVisitors();
  loadVisitorHistory();
  loadSocialStories();
  loadSocialPosts();
  loadPosProducts();
  loadMarketplaceCatalog();
  loadDiscoveredClusterNodes();
  loadExportedNodePackages();
  if (state.currentRole === 'admin') {
    loadAdminUsers();
    loadAdminDevices();
    loadAdminAuditLogs();
  }
  updateDashboardLiveFeeds();
}

function updateDashboardLiveFeeds() {
  // 1. Cluster Discovery & Data Nodes Feed
  const feedClusterText = document.getElementById('feed-cluster-nodes-text');
  const feedClusterStatus = document.getElementById('feed-cluster-nodes-status');
  const widgetClusterText = document.getElementById('widget-cluster-nodes-text');

  const clusterCount = state.clusterNodes ? state.clusterNodes.length : 0;
  if (feedClusterText) {
    if (clusterCount === 0) {
      feedClusterText.innerText = "Local Vault Node (:8000) active. Standalone Data Node (:8002) ready for UDP 224.0.0.251 multicast discovery.";
    } else {
      feedClusterText.innerText = `${clusterCount} external Data Node(s) synchronized on local mesh (${state.clusterNodes.map(n => n.node_id).join(', ')}).`;
    }
  }
  if (feedClusterStatus) {
    feedClusterStatus.innerText = clusterCount > 0 ? `● ${clusterCount} Nodes Discovered` : "● Discovery Beacon Active";
  }
  if (widgetClusterText) {
    widgetClusterText.innerText = clusterCount > 0 ? `${clusterCount + 1} Nodes Online` : "1 Node (Vault Hub)";
  }

  // 2. Network Interface & Operator Sessions Feed
  const feedNetText = document.getElementById('feed-network-audit-text');
  const feedNetStatus = document.getElementById('feed-network-audit-status');
  if (feedNetText) {
    const net = state.networkInfo || {};
    const primaryUrl = net.primary_url || `http://${window.location.host}`;
    const userRole = state.user ? `${state.user.username} (${state.currentRole})` : 'Guest';
    feedNetText.innerText = `Endpoint: ${primaryUrl} • Active Operator: ${userRole}`;
  }
  if (feedNetStatus) {
    feedNetStatus.innerText = state.user ? `● Authenticated (${state.user.role})` : "● Unauthenticated";
  }

  // 3. Security Gatekeeper & Visitor Telemetry Feed
  const feedSecText = document.getElementById('feed-security-visitors-text');
  const feedSecStatus = document.getElementById('feed-security-visitors-status');
  const widgetVisitorsText = document.getElementById('widget-active-visitors-text');
  const dashActiveVisitors = document.getElementById('dash-active-visitors-count');

  const visitorCount = state.activeVisitors ? state.activeVisitors.length : 0;
  if (feedSecText) {
    feedSecText.innerText = `${visitorCount} visitor(s) currently checked in on-premises. Entry logs synchronized.`;
  }
  if (feedSecStatus) {
    feedSecStatus.innerText = visitorCount > 0 ? `● ${visitorCount} Visitors On-Site` : "● Perimeter Log Active";
  }
  if (widgetVisitorsText) {
    widgetVisitorsText.innerText = `${visitorCount} On-Premises`;
  }
  if (dashActiveVisitors) {
    dashActiveVisitors.innerText = `● ${visitorCount} Active Visitors`;
  }

  // 4. Agricultural Field Telemetry Feed
  const feedAgriText = document.getElementById('feed-agri-telemetry-text');
  const feedAgriStatus = document.getElementById('feed-agri-telemetry-status');
  const widgetPlantingsText = document.getElementById('widget-active-plantings-text');
  const dashPlantings = document.getElementById('dash-plantings-count');

  const plantCount = state.plantings ? state.plantings.length : 0;
  if (feedAgriText) {
    feedAgriText.innerText = `${plantCount} active crop batch(es) recorded. Dynamic decay price floors enabled.`;
  }
  if (feedAgriStatus) {
    feedAgriStatus.innerText = plantCount > 0 ? `● ${plantCount} Batches Active` : "● Production Engine Ready";
  }
  if (widgetPlantingsText) {
    widgetPlantingsText.innerText = `${plantCount} Batches in Soil`;
  }
  if (dashPlantings) {
    dashPlantings.innerText = `● ${plantCount} Active Plantings`;
  }

  // 5. Community Posts & Catalog Counts
  const dashPosts = document.getElementById('dash-posts-count');
  if (dashPosts) {
    const postCount = state.socialPosts ? state.socialPosts.length : 0;
    dashPosts.innerText = `● ${postCount} Community Posts`;
  }
  const dashCatalog = document.getElementById('dash-catalog-count');
  if (dashCatalog) {
    const catCount = state.posProducts ? state.posProducts.length : 0;
    dashCatalog.innerText = `● ${catCount} Catalog Items`;
  }
}

// =====================================================================
// STAGE 1 CORE: AGRICULTURE MODULE
// =====================================================================
function initAgriModule() {
  const btnAgriCalc = document.getElementById('btn-calculate-agri');
  if (btnAgriCalc) {
    btnAgriCalc.addEventListener('click', calculateBulawayoSchedule);
  }
}

function togglePlantingForm() {
  const form = document.getElementById('new-planting-form-container');
  if (form) {
    form.style.display = (form.style.display === 'none' || !form.style.display) ? 'block' : 'none';
  }
}

async function loadPlantings() {
  try {
    const res = await secureFetch("/api/agri/plantings");
    if (!res.ok) return;
    const data = await res.json();
    state.plantings = data.plantings || [];
    updateDashboardLiveFeeds();

    const dashPlantings = document.getElementById('dash-plantings-count');
    if (dashPlantings) {
      dashPlantings.innerText = `● ${state.plantings.length} Active Plantings`;
    }

    const tbody = document.getElementById('agri-plantings-table-body');
    const select = document.getElementById('harvest-planting-select');

    if (tbody) {
      if (state.plantings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No active crop plantings found. Click <strong style="color: #10b981;">"+ Add Planting"</strong> above to record your first plot.</td></tr>`;
      } else {
        tbody.innerHTML = state.plantings.map(p => `
          <tr>
            <td><strong style="font-family: monospace; color: var(--accent-cyan);">${p.id}</strong></td>
            <td><strong>${p.crop_variety}</strong></td>
            <td>${p.plot_bed_id}</td>
            <td>${p.planting_date_utc ? p.planting_date_utc.substring(0, 10) : 'N/A'}</td>
            <td>${p.seeding_density || 0} /m²</td>
            <td><span style="color: var(--success); font-weight: 600;">${p.initial_soil_hydration_pct || 0}%</span></td>
            <td><span style="padding: 2px 8px; border-radius: 9999px; background: rgba(16, 185, 129, 0.2); color: #10b981; font-size: 0.75rem; font-weight: 700;">${p.status.toUpperCase()}</span></td>
            <td><button class="btn-pill-small" onclick="selectPlantingForHarvest('${p.id}', '${p.crop_variety}')">Harvest 🚜</button></td>
          </tr>
        `).join('');
      }
    }

    if (select) {
      select.innerHTML = state.plantings.map(p => `
        <option value="${p.id}">${p.crop_variety} (${p.plot_bed_id})</option>
      `).join('');
    }
  } catch (e) {
    console.error("Failed to load plantings:", e);
  }
}

async function submitNewPlanting() {
  const crop = document.getElementById('planting-crop-variety').value.trim();
  const plot = document.getElementById('planting-plot-bed-id').value.trim();
  const density = parseFloat(document.getElementById('planting-seeding-density').value || "0");
  const hydration = parseFloat(document.getElementById('planting-soil-hydration').value || "0");
  const notes = document.getElementById('planting-notes').value.trim();

  if (!crop || !plot) {
    alert("Crop variety and Plot Bed ID are required.");
    return;
  }

  try {
    const res = await secureFetch("/api/agri/plantings", {
      method: "POST",
      body: JSON.stringify({
        crop_variety: crop,
        plot_bed_id: plot,
        seeding_density: density,
        initial_soil_hydration_pct: hydration,
        notes: notes
      })
    });

    if (res.ok) {
      togglePlantingForm();
      loadPlantings();
    }
  } catch (e) {
    alert("Failed to create planting: " + e.message);
  }
}

function recalculateCosts() {
  const cSeeds = parseFloat(document.getElementById('calc-cost-seeds').value || "0");
  const cFert = parseFloat(document.getElementById('calc-cost-fert').value || "0");
  const cWater = parseFloat(document.getElementById('calc-cost-water').value || "0");
  const cLabor = parseFloat(document.getElementById('calc-cost-labor').value || "0");
  const cPest = parseFloat(document.getElementById('calc-cost-pest').value || "0");
  const cPack = parseFloat(document.getElementById('calc-cost-pack').value || "0");
  const cLog = parseFloat(document.getElementById('calc-cost-log').value || "0");
  const cOver = parseFloat(document.getElementById('calc-cost-over').value || "0");

  const totalCost = cSeeds + cFert + cWater + cLabor + cPest + cPack + cLog + cOver;
  document.getElementById('calc-total-cost-usd').innerText = `$${totalCost.toFixed(2)}`;

  const mHarvest = parseFloat(document.getElementById('calc-mass-harvest').value || "0");
  const mSelf = parseFloat(document.getElementById('calc-mass-self').value || "0");
  const mComm = Math.max(0, mHarvest - mSelf);
  document.getElementById('calc-comm-mass-val').innerText = `${mComm.toFixed(0)} kg`;

  const markup = parseFloat(document.getElementById('calc-markup-slider').value || "1.0");
  document.getElementById('calc-markup-label').innerText = `${(markup * 100).toFixed(0)}% (${(1 + markup).toFixed(1)}x)`;

  const costFloor = mComm > 0 ? (totalCost / mComm) : 0.50;
  const basePrice = costFloor * (1.0 + markup);

  document.getElementById('calc-cost-floor-val').innerText = `$${costFloor.toFixed(2)} / kg`;
  document.getElementById('calc-base-price-val').innerText = `$${basePrice.toFixed(2)} / kg`;
}

function selectPlantingForHarvest(plantingId, cropName) {
  switchView('vpa1');
  const tabBtn = document.querySelectorAll('.tab-pill-btn')[2];
  if (tabBtn) tabBtn.click();
  const select = document.getElementById('harvest-planting-select');
  if (select) select.value = plantingId;
  const nameInput = document.getElementById('harvest-crop-name');
  if (nameInput) nameInput.value = cropName;
}

async function submitHarvest() {
  const pId = document.getElementById('harvest-planting-select').value;
  const crop = document.getElementById('harvest-crop-name').value.trim();
  const mHarvest = parseFloat(document.getElementById('harvest-total-mass').value || "0");
  const mSelf = parseFloat(document.getElementById('harvest-self-mass').value || "0");
  const grade = document.getElementById('harvest-quality-grade').value;
  const halfLife = parseFloat(document.getElementById('harvest-half-life').value || "2.5");

  if (!pId || !crop || mHarvest <= 0) {
    alert("Please select a planting and enter positive harvest mass.");
    return;
  }

  try {
    const res = await secureFetch("/api/agri/harvests", {
      method: "POST",
      body: JSON.stringify({
        planting_id: pId,
        crop_name: crop,
        mass_harvest_kg: mHarvest,
        mass_self_kg: mSelf,
        quality_grade: grade,
        shelf_life_half_life_days: halfLife
      })
    });

    if (res.ok) {
      alert(`Harvest logged successfully! Commercial batch synchronized to POS inventory.`);
      loadPlantings();
      loadHarvests();
      loadDispositions();
      loadPosProducts();
      loadMarketplaceCatalog();
    }
  } catch (e) {
    alert("Harvest logging failed: " + e.message);
  }
}

async function loadHarvests() {
  try {
    const res = await secureFetch("/api/agri/harvests");
    if (!res.ok) return;
    const data = await res.json();
    state.harvests = data.harvests || [];
  } catch (e) {
    console.error(e);
  }
}

async function loadDispositions() {
  try {
    const res = await secureFetch("/api/agri/dispositions");
    if (!res.ok) return;
    const data = await res.json();
    state.dispositions = data.dispositions || [];

    const tbody = document.getElementById('agri-dispositions-table-body');
    if (tbody) {
      if (state.dispositions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 16px;">No dispositions recorded.</td></tr>`;
      } else {
        tbody.innerHTML = state.dispositions.map(d => `
          <tr>
            <td><code style="color: var(--accent-cyan);">${d.id}</code></td>
            <td><code style="color: var(--text-muted);">${d.harvest_id}</code></td>
            <td><strong style="color: ${d.disposition_type.includes('self') ? '#fbbf24' : '#10b981'};">${d.disposition_type}</strong></td>
            <td><strong>${d.quantity_kg} kg</strong></td>
            <td>${d.destination}</td>
            <td>${d.timestamp_utc ? d.timestamp_utc.substring(0, 19).replace('T', ' ') : 'N/A'}</td>
            <td>${d.logged_by}</td>
          </tr>
        `).join('');
      }
    }
  } catch (e) {
    console.error(e);
  }
}

function calculateBulawayoSchedule() {
  const crop = document.getElementById('agri-crop-select').value;
  const out = document.getElementById('recommendation-output');
  if (!out) return;

  const currentMonth = new Date().toLocaleString('default', { month: 'long' });
  const profile = climateData.find(c => c.month === currentMonth) || climateData[0];

  out.innerHTML = `
    <div style="font-size: 0.88rem; line-height: 1.6;">
      <h4 style="color: var(--accent-cyan); margin-bottom: 8px;">🌾 Agronomic Prescription for ${crop} (${profile.month})</h4>
      <p><strong>Historical Temp:</strong> ${profile.temp}°C | <strong>Average Rainfall:</strong> ${profile.rainfall} mm (${profile.rainyDays} rainy days)</p>
      <p style="margin-top: 6px;"><strong>Prescription:</strong> Apply drip irrigation cycle at 06:00 and 17:30. Ensure soil moisture threshold remains above 60%.</p>
    </div>
  `;
}

// =====================================================================
// STAGE 1 CORE: SECURITY VISITOR GATEKEEPER MODULE
// =====================================================================
function initSecurityModule() {
  // Handlers attached inline
}

async function submitVisitorCheckin() {
  const nid = document.getElementById('vis-national-id').value.trim();
  const name = document.getElementById('vis-full-name').value.trim();
  const env = document.getElementById('vis-destination-env').value;
  const escort = document.getElementById('vis-escort-officer').value.trim();
  const purpose = document.getElementById('vis-purpose').value.trim();
  const notes = document.getElementById('vis-notes').value.trim();

  if (!nid || !name) {
    alert("National ID and Full Name are required.");
    return;
  }

  try {
    const res = await secureFetch("/api/security/visitors/checkin", {
      method: "POST",
      body: JSON.stringify({
        national_id: nid,
        full_name: name,
        destination_env: env,
        escort_officer: escort,
        purpose: purpose,
        notes: notes
      })
    });

    if (res.ok) {
      alert(`Visitor ${name} checked in successfully!`);
      document.getElementById('form-visitor-checkin').reset();
      loadActiveVisitors();
      loadVisitorHistory();
    }
  } catch (e) {
    alert("Check-in failed: " + e.message);
  }
}

async function loadActiveVisitors() {
  try {
    const res = await secureFetch("/api/security/visitors/active");
    if (!res.ok) return;
    const data = await res.json();
    state.activeVisitors = data.active_visitors || [];
    updateDashboardLiveFeeds();

    const tbody = document.getElementById('security-active-visitors-table-body');
    const dashCount = document.getElementById('dash-active-visitors-count');
    const widgetText = document.getElementById('widget-active-visitors-text');

    if (dashCount) dashCount.innerText = `● ${state.activeVisitors.length} Active Visitors`;
    if (widgetText) widgetText.innerText = `${state.activeVisitors.length} On-Premises`;

    if (tbody) {
      if (state.activeVisitors.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 16px;">No visitors currently on premises.</td></tr>`;
      } else {
        tbody.innerHTML = state.activeVisitors.map(v => `
          <tr>
            <td><code style="color: var(--accent-cyan);">${v.id}</code></td>
            <td><strong>${v.full_name}</strong></td>
            <td><code style="color: var(--text-muted);">${v.national_id}</code></td>
            <td>${v.destination_env}</td>
            <td>${v.time_in_utc ? v.time_in_utc.substring(11, 16) : 'N/A'}</td>
            <td>${v.escort_officer || 'None'}</td>
            <td><span style="padding: 2px 8px; border-radius: 9999px; background: rgba(16, 185, 129, 0.2); color: #10b981; font-size: 0.75rem; font-weight: 700;">ACTIVE</span></td>
            <td style="text-align: center;">
              <button class="btn-pill-small" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border-color: rgba(239, 68, 68, 0.4);" onclick="checkoutVisitor('${v.id}')">Check Out 🚪</button>
            </td>
          </tr>
        `).join('');
      }
    }
  } catch (e) {
    console.error("Failed to load active visitors:", e);
  }
}

async function checkoutVisitor(visId) {
  try {
    const res = await secureFetch("/api/security/visitors/checkout", {
      method: "POST",
      body: JSON.stringify({ visitor_id: visId })
    });

    if (res.ok) {
      loadActiveVisitors();
      loadVisitorHistory();
    }
  } catch (e) {
    alert("Checkout failed: " + e.message);
  }
}

async function loadVisitorHistory() {
  try {
    const res = await secureFetch("/api/security/visitors");
    if (!res.ok) return;
    const data = await res.json();
    state.allVisitors = data.visitors || [];
    renderVisitorHistory(state.allVisitors);
  } catch (e) {
    console.error("Failed to load visitor history:", e);
  }
}

function filterVisitorHistory() {
  const q = (document.getElementById('vis-search-filter').value || "").toLowerCase();
  const env = document.getElementById('vis-env-filter').value;

  const filtered = state.allVisitors.filter(v => {
    const matchQ = !q || v.full_name.toLowerCase().includes(q) || v.national_id.toLowerCase().includes(q);
    const matchEnv = !env || v.destination_env === env;
    return matchQ && matchEnv;
  });

  renderVisitorHistory(filtered);
}

function renderVisitorHistory(list) {
  const tbody = document.getElementById('security-history-visitors-table-body');
  if (!tbody) return;

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 16px;">No visitor logs found.</td></tr>`;
  } else {
    tbody.innerHTML = list.map(v => `
      <tr>
        <td><code style="color: var(--text-muted);">${v.id}</code></td>
        <td><strong>${v.full_name}</strong> (${v.national_id})</td>
        <td>${v.destination_env}</td>
        <td>${v.time_in_utc ? v.time_in_utc.substring(11, 16) : 'N/A'}</td>
        <td>${v.time_out_utc ? v.time_out_utc.substring(11, 16) : '<span style="color: #10b981;">Active</span>'}</td>
        <td>${v.purpose || '-'}</td>
        <td><span style="font-size: 0.75rem; font-weight: 700; color: ${v.status === 'Active' ? '#10b981' : '#94a3b8'};">${v.status}</span></td>
      </tr>
    `).join('');
  }
}

// =====================================================================
// STAGE 1 CORE: HYBRID SOCIAL MEDIA HUB (4-IN-1)
// =====================================================================
function initSocialModule() {
  const btnPostSubmit = document.getElementById('btn-submit-create-post');
  if (btnPostSubmit) btnPostSubmit.addEventListener('click', submitCreatePost);

  const btnTipSubmit = document.getElementById('btn-submit-tip');
  if (btnTipSubmit) btnTipSubmit.addEventListener('click', submitSocialTip);
}

async function loadSocialStories() {
  try {
    const res = await secureFetch("/api/social/stories");
    if (!res.ok) return;
    const data = await res.json();
    state.socialStories = data.stories || [];

    const container = document.getElementById('social-stories-container');
    if (!container) return;

    if (state.socialStories.length === 0) {
      container.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-muted); padding: 10px;">No active 24h stories. Click "+ Post Story" to share one.</span>`;
    } else {
      container.innerHTML = state.socialStories.map(s => `
        <div class="story-bubble" onclick="alert('Story from @${s.author}: ${s.content_text}')">
          <div class="story-ring">
            <div class="story-avatar">${s.author.charAt(0).toUpperCase()}</div>
          </div>
          <span class="story-author-label">@${s.author}</span>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error("Failed to load stories:", e);
  }
}

async function loadSocialPosts(postType = null) {
  try {
    let url = "/api/social/posts";
    if (postType) url += `?post_type=${postType}`;

    const res = await secureFetch(url);
    if (!res.ok) return;
    const data = await res.json();
    state.socialPosts = data.posts || [];
    updateDashboardLiveFeeds();

    const feed = document.getElementById('social-feed-stream');
    if (!feed) return;

    const dashPosts = document.getElementById('dash-posts-count');
    if (dashPosts) {
      dashPosts.innerText = `● ${state.socialPosts.length} Community Posts`;
    }

    if (state.socialPosts.length === 0) {
      feed.innerHTML = `
        <div class="glass-panel" style="padding: 36px 20px; text-align: center; border-radius: 20px;">
          <div style="font-size: 2.4rem; margin-bottom: 8px;">🌐</div>
          <h4 style="margin: 0 0 6px 0; color: #fff;">Community Hub is Live</h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); max-width: 360px; margin: 0 auto 16px auto;">
            No public posts published yet. Share field updates, crop listings, or store notices.
          </p>
          <button class="btn-pill-primary" onclick="openCreatePostModal('thread')">+ Create First Post</button>
        </div>
      `;
      return;
    }

    feed.innerHTML = state.socialPosts.map(p => {
      const typeIcons = { thread: '💬', carousel: '📸', story: '👻', reel: '🎬' };
      const tags = (p.tags || []).map(t => `<span style="color: var(--accent-cyan); font-size: 0.78rem; margin-right: 6px;">#${t}</span>`).join('');

      return `
        <div class="social-card" id="card-${p.id}">
          <div class="social-card-header">
            <div class="social-card-author-group">
              <div class="user-avatar-badge" style="width: 38px; height: 38px; font-size: 0.9rem;">${p.author.charAt(0).toUpperCase()}</div>
              <div>
                <strong style="color: #fff; font-size: 0.95rem;">@${p.author}</strong>
                <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 8px;">${p.created_at_utc ? p.created_at_utc.substring(0, 16).replace('T', ' ') : ''}</span>
              </div>
            </div>
            <span class="role-pill-badge" style="background: rgba(255,255,255,0.06);">${typeIcons[p.post_type] || '💬'} ${p.post_type.toUpperCase()}</span>
          </div>

          <p style="font-size: 0.92rem; line-height: 1.5; color: var(--text-main); margin-bottom: 8px;">${p.content_text}</p>
          <div style="margin-bottom: 8px;">${tags}</div>

          <div class="social-card-actions">
            <button class="social-action-btn" onclick="openTipModal('${p.id}')">
              <span>⚡ Tip</span>
              <strong style="color: var(--accent-cyan);">$${(p.tips_usd || 0).toFixed(2)}</strong>
            </button>
            <button class="social-action-btn" onclick="toggleComments('${p.id}')">
              <span>💬 Comments</span>
            </button>
          </div>

          <!-- Comments container (collapsible) -->
          <div id="comments-${p.id}" style="display: none; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.06);">
            <div id="comments-list-${p.id}" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px;"></div>
            <div style="display: flex; gap: 8px;">
              <input type="text" id="comment-input-${p.id}" class="search-input" style="flex-grow: 1; padding: 8px 14px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); border-radius: 9999px;" placeholder="Write a reply...">
              <button class="btn-pill-small" onclick="submitComment('${p.id}')">Reply</button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error("Failed to load social posts:", e);
  }
}

function filterSocialFeed(postType) {
  document.querySelectorAll('#btn-tab-feed-all, #btn-tab-feed-threads, #btn-tab-feed-carousels, #btn-tab-feed-reels').forEach(btn => btn.classList.remove('active'));
  if (!postType) {
    document.getElementById('btn-tab-feed-all').classList.add('active');
  } else if (postType === 'thread') {
    document.getElementById('btn-tab-feed-threads').classList.add('active');
  } else if (postType === 'carousel') {
    document.getElementById('btn-tab-feed-carousels').classList.add('active');
  } else if (postType === 'reel') {
    document.getElementById('btn-tab-feed-reels').classList.add('active');
  }
  loadSocialPosts(postType);
}

function openCreatePostModal(defaultType = 'thread') {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-create-post').style.display = 'block';
  document.getElementById('post-type-select').value = defaultType;
}

async function submitCreatePost() {
  const pType = document.getElementById('post-type-select').value;
  const content = document.getElementById('post-content-text').value.trim();
  const tagsRaw = document.getElementById('post-tags-input').value.trim();
  const tags = tagsRaw ? tagsRaw.split(',').map(t => t.trim()) : [];

  if (!content) {
    alert("Post caption cannot be empty.");
    return;
  }

  try {
    const res = await secureFetch("/api/social/posts", {
      method: "POST",
      body: JSON.stringify({
        post_type: pType,
        content_text: content,
        tags: tags
      })
    });

    if (res.ok) {
      hideModals();
      document.getElementById('post-content-text').value = '';
      document.getElementById('post-tags-input').value = '';
      loadSocialStories();
      loadSocialPosts();
    }
  } catch (e) {
    alert("Post creation failed: " + e.message);
  }
}

function openTipModal(postId) {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-social-tip').style.display = 'block';
  document.getElementById('tip-target-post-id').value = postId;
  selectTipCurrency('USD');
}

function selectTipCurrency(curr) {
  state.selectedTipCurrency = curr;
  document.querySelectorAll('#tip-currency-buttons-container button').forEach(b => {
    b.classList.toggle('active', b.id === `tip-curr-${curr.toLowerCase()}`);
  });
}

async function submitSocialTip() {
  const postId = document.getElementById('tip-target-post-id').value;
  const amt = parseFloat(document.getElementById('tip-amount-input').value || "0");

  if (amt <= 0) {
    alert("Tip amount must be positive.");
    return;
  }

  try {
    const res = await secureFetch(`/api/social/posts/${postId}/tip`, {
      method: "POST",
      body: JSON.stringify({
        currency: state.selectedTipCurrency,
        amount: amt
      })
    });

    if (res.ok) {
      hideModals();
      loadSocialPosts();
    }
  } catch (e) {
    alert("Tipping failed: " + e.message);
  }
}

async function toggleComments(postId) {
  const cBox = document.getElementById(`comments-${postId}`);
  if (!cBox) return;

  if (cBox.style.display === 'none') {
    cBox.style.display = 'block';
    try {
      const res = await secureFetch(`/api/social/posts/${postId}/comments`);
      if (res.ok) {
        const data = await res.json();
        const list = document.getElementById(`comments-list-${postId}`);
        if (list) {
          list.innerHTML = (data.comments || []).map(c => `
            <div style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 12px; font-size: 0.82rem;">
              <strong style="color: var(--accent-cyan);">@${c.author}:</strong> ${c.comment_text}
            </div>
          `).join('') || `<span style="font-size: 0.75rem; color: var(--text-muted);">No comments yet.</span>`;
        }
      }
    } catch (e) {
      console.error(e);
    }
  } else {
    cBox.style.display = 'none';
  }
}

async function submitComment(postId) {
  const input = document.getElementById(`comment-input-${postId}`);
  if (!input || !input.value.trim()) return;

  try {
    const res = await secureFetch(`/api/social/posts/${postId}/comments`, {
      method: "POST",
      body: JSON.stringify({ comment_text: input.value.trim() })
    });

    if (res.ok) {
      input.value = '';
      toggleComments(postId); // refresh
      toggleComments(postId);
    }
  } catch (e) {
    alert("Comment failed: " + e.message);
  }
}

// =====================================================================
// STAGE 1 CORE: POS & MARKETPLACE MODULE (CONTINUOUS DECAY)
// =====================================================================
function initPOSModule() {
  const btnAddCart = document.getElementById('btn-add-cart');
  if (btnAddCart) {
    btnAddCart.addEventListener('click', () => {
      const select = document.getElementById('pos-product-select');
      const qty = parseFloat(document.getElementById('pos-qty-input').value || "1");
      const itemId = select.value;
      if (!itemId) return;

      const prod = state.posProducts.find(p => p.id === itemId);
      if (!prod) return;

      const existing = state.cart.find(c => c.id === itemId);
      if (existing) {
        existing.qty += qty;
      } else {
        state.cart.push({ ...prod, qty: qty });
      }

      renderCart();
    });
  }

  const btnCheckout = document.getElementById('btn-complete-checkout');
  if (btnCheckout) {
    btnCheckout.addEventListener('click', submitPOSCheckout);
  }
}

async function loadPosProducts() {
  try {
    const res = await secureFetch("/api/pos/promotions");
    if (!res.ok) return;
    const items = await res.json();
    state.posProducts = items || [];
    updateDashboardLiveFeeds();

    const dashCatalog = document.getElementById('dash-catalog-count');
    if (dashCatalog) {
      dashCatalog.innerText = `● ${state.posProducts.length} Catalog Items`;
    }

    const select = document.getElementById('pos-product-select');
    if (select) {
      if (state.posProducts.length === 0) {
        select.innerHTML = `<option value="">No inventory items available</option>`;
      } else {
        select.innerHTML = state.posProducts.map(p => `
          <option value="${p.id}">${p.name} ($${p.current_price_usd.toFixed(2)} / ${p.unit}) - Qty: ${p.quantity}</option>
        `).join('');
      }
    }
  } catch (e) {
    console.error("Failed to load POS products:", e);
  }
}

async function loadMarketplaceCatalog() {
  try {
    const res = await secureFetch("/api/marketplace/catalog");
    if (!res.ok) return;
    const data = await res.json();
    const catalog = data.catalog || [];

    const grid = document.getElementById('customer-marketplace-grid');
    if (!grid) return;

    if (catalog.length === 0) {
      grid.innerHTML = `<div class="glass-panel" style="padding: 24px; text-align: center; color: var(--text-muted);">No fresh produce listed in the marketplace right now.</div>`;
      return;
    }

    grid.innerHTML = catalog.map(item => `
      <div class="node-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
          <h4 style="font-size: 1.05rem; color: #fff;">${item.name}</h4>
          ${item.is_floor_active ? '<span class="decay-floor-active-tag">Floor Active</span>' : (item.discount_pct > 0 ? `<span class="decay-discount-tag">-${item.discount_pct.toFixed(0)}% Off</span>` : '')}
        </div>
        <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 12px;">Available: <strong>${item.quantity} ${item.unit}</strong></p>

        <div class="decay-price-box" style="margin-bottom: 14px;">
          <span style="font-size: 0.72rem; color: var(--text-muted);">Live Decay Price:</span>
          <span class="decay-live-price">$${item.current_price_usd.toFixed(2)} USD</span>
          <div style="font-size: 0.75rem; color: var(--text-muted); display: flex; justify-content: space-between; margin-top: 4px;">
            <span>R${item.price_zar.toFixed(2)} ZAR</span>
            <span>${item.price_zwg.toFixed(2)} ZWG</span>
          </div>
        </div>

        <button class="btn-pill-primary" style="width: 100%; margin: 0;" onclick="quickAddToCart('${item.id}')">Add to Cart 🛒</button>
      </div>
    `).join('');
  } catch (e) {
    console.error("Failed to load customer marketplace:", e);
  }
}

function quickAddToCart(itemId) {
  const prod = state.posProducts.find(p => p.id === itemId);
  if (!prod) return;
  const existing = state.cart.find(c => c.id === itemId);
  if (existing) existing.qty += 1;
  else state.cart.push({ ...prod, qty: 1 });
  renderCart();
  switchView('vpa3');
}

function renderCart() {
  const tbody = document.getElementById('pos-cart-table-body');
  const totalDisplay = document.getElementById('pos-cart-total-usd');

  let total = 0.0;
  if (state.cart.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:16px; color: var(--text-muted);">Cart is empty.</td></tr>`;
  } else {
    tbody.innerHTML = state.cart.map((c, idx) => {
      const subtotal = c.current_price_usd * c.qty;
      total += subtotal;
      return `
        <tr>
          <td><strong>${c.name}</strong></td>
          <td>${c.qty}</td>
          <td>$${c.current_price_usd.toFixed(2)}</td>
          <td><strong>$${subtotal.toFixed(2)}</strong></td>
          <td style="text-align: center;"><button class="btn-pill-small" style="color: #f87171;" onclick="removeFromCart(${idx})">✕</button></td>
        </tr>
      `;
    }).join('');
  }

  state.cartTotalUsd = total;
  if (totalDisplay) totalDisplay.innerText = `$${total.toFixed(2)}`;
  recalculateTender();
}

function removeFromCart(idx) {
  state.cart.splice(idx, 1);
  renderCart();
}

function recalculateTender() {
  const tUsd = parseFloat(document.getElementById('pos-tender-usd').value || "0");
  const tZar = parseFloat(document.getElementById('pos-tender-zar').value || "0");
  const tZwg = parseFloat(document.getElementById('pos-tender-zwg').value || "0");

  const rZar = state.exchangeRates.ZAR;
  const rZwg = state.exchangeRates.ZWG;

  const totalPaidUsd = tUsd + (tZar / rZar) + (tZwg / rZwg);
  const cartTotal = state.cartTotalUsd || 0.0;
  const diffUsd = totalPaidUsd - cartTotal;

  const changeUsd = document.getElementById('pos-change-usd');
  const changeZar = document.getElementById('change-opt-zar');
  const changeZwg = document.getElementById('change-opt-zwg');

  if (diffUsd >= 0) {
    if (changeUsd) changeUsd.innerText = `$${diffUsd.toFixed(2)}`;
    if (changeZar) changeZar.innerText = `R${(diffUsd * rZar).toFixed(2)}`;
    if (changeZwg) changeZwg.innerText = `${(diffUsd * rZwg).toFixed(2)} ZWG`;
  } else {
    if (changeUsd) changeUsd.innerText = `-$${Math.abs(diffUsd).toFixed(2)} (Due)`;
    if (changeZar) changeZar.innerText = `R0.00`;
    if (changeZwg) changeZwg.innerText = `0.00 ZWG`;
  }
}

async function redeemVoucherAtPOS() {
  const vidInput = document.getElementById('pos-voucher-input');
  const vid = vidInput ? vidInput.value.trim() : '';
  if (!vid) {
    alert("Please enter or scan a Voucher ID.");
    return;
  }

  try {
    const res = await secureFetch("/api/vouchers/redeem", {
      method: "POST",
      body: JSON.stringify({
        vid: vid,
        business_id: state.activeBusinessId
      })
    });

    const data = await res.json();
    if (res.ok && data.status === "success") {
      const red = data.redemption;
      alert(`🎟️ Voucher verified & redeemed!\nID: ${red.vid}\nAmount: ${red.value_amount} ${red.currency} ($${red.equivalent_usd.toFixed(2)} USD equiv)\nCredit applied to USD tender.`);
      const tUsdEl = document.getElementById('pos-tender-usd');
      if (tUsdEl) {
        tUsdEl.value = (parseFloat(tUsdEl.value || "0") + red.equivalent_usd).toFixed(2);
        recalculateTender();
      }
      vidInput.value = '';
    } else {
      alert("Voucher Redemption Failed: " + (data.detail || "Invalid, already redeemed, or expired voucher."));
    }
  } catch (e) {
    alert("Error redeeming voucher: " + e.message);
  }
}

function showReceiptModal(receipt) {
  if (!receipt) return;
  state.currentReceipt = receipt;
  
  // Populate header
  const b = receipt.business || {};
  document.getElementById('receipt-biz-name').innerText = b.name || "MADN Agribusiness Hub";
  document.getElementById('receipt-biz-category').innerText = b.category || "Horticulture";
  document.getElementById('receipt-biz-address').innerText = b.location_address || "Bulawayo, Zimbabwe";
  document.getElementById('receipt-biz-phone').innerText = `Tel: ${b.contact_phone || "N/A"} • Tax: ${b.tax_id || "N/A"}`;
  document.getElementById('receipt-inv-num').innerText = receipt.invoice_number || "INV-001";
  document.getElementById('receipt-date-time').innerText = (receipt.timestamp_iso || "").substring(0, 19).replace('T', ' ');
  document.getElementById('receipt-operator').innerText = receipt.operator || "merchant";
  document.getElementById('receipt-footer-note').innerText = b.receipt_footer_note || "Thank you for supporting community smallholders!";

  // Items table
  const tbody = document.getElementById('receipt-items-tbody');
  tbody.innerHTML = (receipt.items || []).map(item => `
    <tr>
      <td style="padding: 4px 0;"><strong>${item.item_name || 'Item'}</strong></td>
      <td style="text-align: center; padding: 4px 0;">${item.quantity}</td>
      <td style="text-align: right; padding: 4px 0;">$${item.price_usd_at_sale.toFixed(2)}</td>
      <td style="text-align: right; padding: 4px 0;"><strong>$${(item.quantity * item.price_usd_at_sale).toFixed(2)}</strong></td>
    </tr>
  `).join('');

  // Total
  document.getElementById('receipt-total-usd').innerText = `$${receipt.total_due_usd.toFixed(2)} USD`;

  // Tenders
  const tendersList = document.getElementById('receipt-tenders-list');
  tendersList.innerHTML = (receipt.tenders || []).map(t => `
    <div style="display: flex; justify-content: space-between;">
      <span>Tendered ${t.currency}:</span>
      <span>${t.amount_tendered.toFixed(2)} ${t.currency} ($${t.amount_usd_equiv.toFixed(2)} USD)</span>
    </div>
  `).join('');

  // Change voucher box
  const vouchBox = document.getElementById('receipt-voucher-box');
  if (receipt.voucher_issued) {
    vouchBox.style.display = 'block';
    const v = receipt.voucher_issued;
    document.getElementById('receipt-voucher-val').innerText = `${v.value_amount.toFixed(2)} ${v.currency} ($${v.equivalent_usd.toFixed(2)} USD)`;
    document.getElementById('receipt-voucher-vid').innerText = `ID: ${v.vid} • Sig: ${v.signature_hmac.substring(0, 16)}...`;
  } else {
    vouchBox.style.display = 'none';
  }

  // Draw QR code onto canvas
  drawReceiptQRCode(receipt);

  // Open modal
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-thermal-receipt').style.display = 'block';
}

function drawReceiptQRCode(receipt) {
  const canvas = document.getElementById('receipt-qr-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Synthesize cryptographic QR matrix pattern
  const payload = receipt.voucher_issued ?
    `MADN-VOUCHER:${receipt.voucher_issued.vid}|${receipt.voucher_issued.business_id}|${receipt.voucher_issued.value_amount}|${receipt.voucher_issued.currency}|${receipt.voucher_issued.signature_hmac}` :
    `MADN-RECEIPT:${receipt.invoice_number}|${receipt.transaction_id}|${receipt.total_due_usd}|${receipt.audit_hash}`;

  const gridSize = 21;
  const cellSize = Math.floor(canvas.width / gridSize);
  ctx.fillStyle = '#000000';

  function drawFinder(x, y) {
    ctx.fillRect(x * cellSize, y * cellSize, 7 * cellSize, 7 * cellSize);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect((x + 1) * cellSize, (y + 1) * cellSize, 5 * cellSize, 5 * cellSize);
    ctx.fillStyle = '#000000';
    ctx.fillRect((x + 2) * cellSize, (y + 2) * cellSize, 3 * cellSize, 3 * cellSize);
  }
  drawFinder(1, 1);
  drawFinder(gridSize - 8, 1);
  drawFinder(1, gridSize - 8);

  let hashVal = 0;
  for (let i = 0; i < payload.length; i++) {
    hashVal = (hashVal << 5) - hashVal + payload.charCodeAt(i);
    hashVal |= 0;
  }
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      if ((r < 8 && c < 8) || (r < 8 && c >= gridSize - 8) || (r >= gridSize - 8 && c < 8)) continue;
      const bit = Math.abs((hashVal ^ (r * 31 + c * 17))) % 2;
      if (bit === 1) {
        ctx.fillRect(c * cellSize, r * cellSize, cellSize - 1, cellSize - 1);
      }
    }
  }
}

function printReceiptSlip() {
  window.print();
}

function downloadReceiptPDF() {
  const receipt = state.currentReceipt;
  if (!receipt) return;
  const b = receipt.business || {};

  const receiptText = `
============================================================
              ${(b.name || "MADN Agribusiness Hub").toUpperCase()}
       ${b.category || "Horticulture & Agricultural Hub"}
       ${b.location_address || "Bulawayo, Zimbabwe"}
       Tel: ${b.contact_phone || "N/A"} | Tax ID: ${b.tax_id || "N/A"}
============================================================
Invoice Number : ${receipt.invoice_number}
Transaction ID : ${receipt.transaction_id}
Date & Time    : ${receipt.timestamp_iso}
Cashier        : ${receipt.operator}
Node ID        : node-vault-01
------------------------------------------------------------
ITEM                     QTY     PRICE        TOTAL
------------------------------------------------------------
${(receipt.items || []).map(i => `${(i.item_name || "Item").padEnd(24)} ${String(i.quantity).padEnd(7)} $${i.price_usd_at_sale.toFixed(2).padEnd(11)} $${(i.quantity * i.price_usd_at_sale).toFixed(2)}`).join('\n')}
------------------------------------------------------------
TOTAL DUE (USD) : $${receipt.total_due_usd.toFixed(2)}
------------------------------------------------------------
TENDERS:
${(receipt.tenders || []).map(t => `  - ${t.currency}: ${t.amount_tendered.toFixed(2)} ${t.currency} ($${t.amount_usd_equiv.toFixed(2)} USD equiv)`).join('\n')}
${receipt.voucher_issued ? `
------------------------------------------------------------
*** OFFLINE CRYPTOGRAPHIC QR VOUCHER CHANGE ***
Voucher ID     : ${receipt.voucher_issued.vid}
Value          : ${receipt.voucher_issued.value_amount.toFixed(2)} ${receipt.voucher_issued.currency} ($${receipt.voucher_issued.equivalent_usd.toFixed(2)} USD)
Expires At     : ${receipt.voucher_issued.expires_at_utc}
HMAC Signature : ${receipt.voucher_issued.signature_hmac}
` : ''}
------------------------------------------------------------
Audit Hash     : ${receipt.audit_hash}
${b.receipt_footer_note || "Thank you for supporting community smallholders!"}
============================================================
`;

  const blob = new Blob([receiptText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${receipt.invoice_number || 'receipt'}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function submitPOSCheckout() {
  if (state.cart.length === 0) {
    alert("Cart is empty.");
    return;
  }

  const tUsd = parseFloat(document.getElementById('pos-tender-usd').value || "0");
  const tZar = parseFloat(document.getElementById('pos-tender-zar').value || "0");
  const tZwg = parseFloat(document.getElementById('pos-tender-zwg').value || "0");
  const isWalletToggle = document.getElementById('pos-pay-wallet-toggle')?.checked || false;
  const isVouchToggle = document.getElementById('pos-issue-voucher-toggle')?.checked || false;

  const rZar = state.exchangeRates.ZAR;
  const rZwg = state.exchangeRates.ZWG;
  const totalPaidUsd = isWalletToggle ? state.cartTotalUsd : (tUsd + (tZar / rZar) + (tZwg / rZwg));
  const cartTotal = state.cartTotalUsd || 0.0;
  const diffUsd = totalPaidUsd - cartTotal;

  const vouchAmount = (!isWalletToggle && isVouchToggle && diffUsd > 0) ? Math.round(diffUsd * rZwg * 100) / 100 : 0.0;
  const customerUsername = state.user ? state.user.username : 'customer';
  const paymentMethod = isWalletToggle ? 'wallet' : 'cash';

  try {
    const res = await secureFetch("/api/pos/checkout", {
      method: "POST",
      body: JSON.stringify({
        business_id: state.activeBusinessId,
        cart_items: state.cart.map(c => ({ id: c.id, qty: c.qty })),
        tendered_usd: isWalletToggle ? cartTotal : tUsd,
        tendered_zar: isWalletToggle ? 0 : tZar,
        tendered_zwg: isWalletToggle ? 0 : tZwg,
        issue_voucher_change: isVouchToggle,
        voucher_change_amount: vouchAmount,
        voucher_change_currency: "ZWG",
        customer_username: customerUsername,
        payment_method: paymentMethod
      })
    });

    const data = await res.json();
    if (res.ok) {
      state.cart = [];
      renderCart();
      loadPosProducts();
      loadMarketplaceCatalog();
      loadCustomerWallet();
      loadCustomerReceipts();
      loadWalletLedger();

      // Show receipt modal
      if (data.receipt) {
        showReceiptModal(data.receipt);
      } else {
        alert("Transaction completed successfully!");
      }
    } else {
      alert("Checkout failed: " + (data.detail || "Transaction error"));
    }
  } catch (e) {
    alert("Checkout failed: " + e.message);
  }
}

// =====================================================================
// CUSTOMER DIGITAL BANKING & RECEIPT VAULT MODULE
// =====================================================================

function toggleWalletPayment(isWallet) {
  state.payWithWallet = isWallet;
  const tUsd = document.getElementById('pos-tender-usd');
  const tZar = document.getElementById('pos-tender-zar');
  const tZwg = document.getElementById('pos-tender-zwg');

  if (isWallet) {
    if (tUsd) tUsd.value = (state.cartTotalUsd || 0).toFixed(2);
    if (tZar) tZar.value = "0.00";
    if (tZwg) tZwg.value = "0.00";
  }
  recalculateTender();
}

// =====================================================================
// DYNAMIC MULTI-CURRENCY & VIRTUAL TOKEN ENGINE
// =====================================================================

async function loadCurrencies() {
  try {
    const res = await secureFetch("/api/currencies?include_inactive=true");
    if (!res.ok) return;
    const data = await res.json();
    state.currencies = data.currencies || [];
    renderAdminCurrencies();
    populateCurrencyDropdowns();
    if (state.wallet) {
      renderBankingBalances();
    }
    searchGlobalCatalog("");
  } catch (e) {
    console.error("Failed to load currencies:", e);
  }
}

function renderBankingBalances() {
  const grid = document.getElementById('wallet-balances-grid');
  if (!grid) return;

  const w = state.wallet || {};
  const balances = w.balances || {};
  const activeCurrs = (state.currencies || []).filter(c => c.is_active === 1);

  if (activeCurrs.length === 0) {
    grid.innerHTML = `
      <div class="glass-panel" style="padding: 20px; border-radius: 20px; background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.2);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 0.8rem; color: var(--accent-cyan); font-weight: 700; text-transform: uppercase;">USD Balance</span>
          <span style="font-size: 1.2rem;">💵</span>
        </div>
        <h2 style="font-size: 2rem; font-weight: 800; color: #fff; margin: 0;">$${(w.balance_usd || 0).toFixed(2)}</h2>
        <span style="font-size: 0.75rem; color: var(--text-muted); display: block; margin-top: 4px;">Primary Settlement</span>
      </div>
    `;
    return;
  }

  const typeGlows = {
    fiat: { bg: 'rgba(0, 229, 255, 0.05)', border: 'rgba(0, 229, 255, 0.2)', color: 'var(--accent-cyan)', badge: 'Sovereign Fiat' },
    gold_backed: { bg: 'rgba(255, 193, 7, 0.06)', border: 'rgba(255, 193, 7, 0.25)', color: '#ffc107', badge: 'Zimbabwe Gold (ZiG)' },
    virtual_token: { bg: 'rgba(168, 85, 247, 0.06)', border: 'rgba(168, 85, 247, 0.25)', color: '#c084fc', badge: 'Virtual Token' },
    community_credit: { bg: 'rgba(52, 211, 153, 0.06)', border: 'rgba(52, 211, 153, 0.25)', color: '#34d399', badge: 'Community Credit' }
  };

  grid.innerHTML = activeCurrs.map(c => {
    const code = c.code;
    let balVal = balances[code];
    if (balVal === undefined) {
      if (code === 'USD') balVal = w.balance_usd || 0.0;
      else if (code === 'ZAR') balVal = w.balance_zar || 0.0;
      else if (code === 'ZWG') balVal = w.balance_zwg || 0.0;
      else balVal = 0.0;
    }
    const glow = typeGlows[c.currency_type] || typeGlows.virtual_token;
    const formattedVal = `${c.symbol}${balVal.toFixed(2)}`;

    return `
      <div class="glass-panel" style="padding: 20px; border-radius: 20px; background: ${glow.bg}; border: 1px solid ${glow.border};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 0.8rem; color: ${glow.color}; font-weight: 700; text-transform: uppercase;">${code} Balance</span>
          <span style="font-size: 1.1rem; background: rgba(255,255,255,0.06); padding: 4px 8px; border-radius: 8px; font-weight: 700;">${c.symbol}</span>
        </div>
        <h2 style="font-size: 1.8rem; font-weight: 800; color: #fff; margin: 0;">${formattedVal}</h2>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
          <span style="font-size: 0.72rem; color: var(--text-muted);">${c.name}</span>
          <span style="font-size: 0.68rem; padding: 2px 6px; border-radius: 6px; background: rgba(255,255,255,0.06); color: ${glow.color}; font-weight: 600;">${glow.badge}</span>
        </div>
      </div>
    `;
  }).join('');
}

function populateCurrencyDropdowns() {
  const activeCurrs = (state.currencies || []).filter(c => c.is_active === 1);
  if (activeCurrs.length === 0) return;

  // 1. Topup modal dropdown
  const topupSelect = document.getElementById('topup-currency');
  if (topupSelect) {
    const currentVal = topupSelect.value;
    topupSelect.innerHTML = activeCurrs.map(c => `
      <option value="${c.code}" ${c.code === currentVal ? 'selected' : ''}>${c.symbol} ${c.code} - ${c.name}</option>
    `).join('');
  }

  // 2. P2P modal dropdown
  const p2pSelect = document.getElementById('p2p-currency');
  if (p2pSelect) {
    const currentVal = p2pSelect.value;
    p2pSelect.innerHTML = activeCurrs.map(c => `
      <option value="${c.code}" ${c.code === currentVal ? 'selected' : ''}>${c.symbol} ${c.code} - ${c.name}</option>
    `).join('');
  }

  // 3. Social tip buttons container
  const tipContainer = document.getElementById('tip-currency-buttons-container');
  if (tipContainer) {
    tipContainer.innerHTML = activeCurrs.map((c, idx) => `
      <button type="button" class="btn-pill-secondary ${idx === 0 ? 'active' : ''}" id="tip-curr-${c.code.toLowerCase()}" onclick="selectTipCurrency('${c.code}')">${c.symbol} ${c.code}</button>
    `).join('');
    if (!state.selectedTipCurrency && activeCurrs.length > 0) {
      state.selectedTipCurrency = activeCurrs[0].code;
    }
  }
}

function renderAdminCurrencies() {
  const tbody = document.getElementById('admin-currencies-table-body');
  if (!tbody) return;

  const currs = state.currencies || [];
  if (currs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 16px;">No currencies configured.</td></tr>`;
    return;
  }

  tbody.innerHTML = currs.map(c => {
    const isActive = c.is_active === 1;
    const statusBadge = isActive
      ? `<span class="role-pill-badge" style="background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3);">ACTIVE</span>`
      : `<span class="role-pill-badge" style="background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3);">INACTIVE</span>`;

    const isCore = c.code === 'USD';

    return `
      <tr>
        <td><strong style="font-family: monospace; color: var(--accent-cyan); font-size: 1rem;">${c.code}</strong></td>
        <td><strong>${c.name}</strong></td>
        <td><span style="font-size: 1.1rem; font-weight: 700;">${c.symbol}</span></td>
        <td><span style="font-family: monospace;">1 USD = ${c.exchange_rate_to_usd} ${c.code}</span></td>
        <td><span class="role-pill-badge">${(c.currency_type || 'fiat').replace('_', ' ').toUpperCase()}</span></td>
        <td>${statusBadge}</td>
        <td style="text-align: center;">
          <button class="btn-pill-secondary" onclick="promptUpdateCurrencyRate('${c.code}', ${c.exchange_rate_to_usd})" style="padding: 4px 10px; font-size: 0.75rem; margin-right: 4px;">Edit Rate ✏️</button>
          ${!isCore ? `
            <button class="btn-pill-secondary" onclick="toggleCurrencyActive('${c.code}', ${isActive ? 0 : 1})" style="padding: 4px 10px; font-size: 0.75rem; color: ${isActive ? 'var(--danger)' : 'var(--success)'};">
              ${isActive ? 'Deactivate ❌' : 'Activate ✔️'}
            </button>
          ` : ''}
        </td>
      </tr>
    `;
  }).join('');
}

async function submitCreateCurrency() {
  const code = (document.getElementById('new-curr-code').value || "").trim().toUpperCase();
  const name = (document.getElementById('new-curr-name').value || "").trim();
  const symbol = (document.getElementById('new-curr-symbol').value || "").trim();
  const rate = parseFloat(document.getElementById('new-curr-rate').value || "0");
  const type = document.getElementById('new-curr-type').value;

  if (!code || !name || !symbol) {
    alert("Please fill in all currency fields (Code, Name, Symbol).");
    return;
  }
  if (rate <= 0) {
    alert("Exchange rate must be a positive number.");
    return;
  }

  try {
    const res = await secureFetch("/api/admin/currencies", {
      method: "POST",
      body: JSON.stringify({
        code: code,
        name: name,
        symbol: symbol,
        exchange_rate_to_usd: rate,
        currency_type: type
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      alert(`🚀 Currency ${code} (${name}) successfully added to node!`);
      document.getElementById('new-curr-code').value = "";
      document.getElementById('new-curr-name').value = "";
      document.getElementById('new-curr-symbol').value = "";
      document.getElementById('new-curr-rate').value = "";
      await loadCurrencies();
      if (state.activeView === 'banking') {
        loadCustomerWallet();
      }
    } else {
      alert("Failed to add currency: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Error adding currency: " + e.message);
  }
}

async function promptUpdateCurrencyRate(code, currentRate) {
  const newRateStr = prompt(`Update exchange rate for ${code} (Units per 1 USD):`, currentRate);
  if (!newRateStr) return;
  const newRate = parseFloat(newRateStr);
  if (isNaN(newRate) || newRate <= 0) {
    alert("Please enter a valid positive number for exchange rate.");
    return;
  }

  try {
    const res = await secureFetch(`/api/admin/currencies/${code}`, {
      method: "PUT",
      body: JSON.stringify({ exchange_rate_to_usd: newRate })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      alert(`Updated exchange rate for ${code} to ${newRate} per USD.`);
      await loadCurrencies();
    } else {
      alert("Failed to update rate: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Error updating exchange rate: " + e.message);
  }
}

async function toggleCurrencyActive(code, newActiveState) {
  try {
    const res = await secureFetch(`/api/admin/currencies/${code}`, {
      method: "PUT",
      body: JSON.stringify({ is_active: newActiveState })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      await loadCurrencies();
      if (state.activeView === 'banking') {
        loadCustomerWallet();
      }
    } else {
      alert("Failed to update currency status: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Error updating currency status: " + e.message);
  }
}

let currencyValidationDebounce = null;
let lastMatchedValidation = null;

function handleCurrencyCodeInput(code) {
  clearTimeout(currencyValidationDebounce);
  const trimmed = (code || "").trim().toUpperCase();
  const statusTag = document.getElementById('curr-collision-status-tag');
  const msgEl = document.getElementById('curr-code-collision-msg');
  const adoptBtn = document.getElementById('btn-adopt-official-standard');

  if (!trimmed) {
    if (statusTag) statusTag.style.display = 'none';
    if (msgEl) msgEl.style.display = 'none';
    if (adoptBtn) adoptBtn.style.display = 'none';
    lastMatchedValidation = null;
    return;
  }

  currencyValidationDebounce = setTimeout(async () => {
    try {
      const res = await secureFetch(`/api/currencies/validate?code=${encodeURIComponent(trimmed)}`);
      if (!res.ok) return;
      const data = await res.json();
      const val = data.validation || {};
      lastMatchedValidation = val;

      if (statusTag && msgEl) {
        statusTag.style.display = 'inline-block';
        msgEl.style.display = 'block';

        if (val.collision_type === 'EXISTING_ACTIVE_CURRENCY') {
          statusTag.innerHTML = `<span class="role-pill-badge" style="background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid #ef4444;">ALREADY ACTIVE</span>`;
          msgEl.style.background = 'rgba(239,68,68,0.1)';
          msgEl.style.border = '1px solid rgba(239,68,68,0.3)';
          msgEl.style.color = '#fca5a5';
          msgEl.innerText = `⚠️ ${val.message}`;
          if (adoptBtn) adoptBtn.style.display = 'none';
        } else if (val.collision_type === 'OFFICIAL_ISO_FIAT') {
          statusTag.innerHTML = `<span class="role-pill-badge" style="background: rgba(0, 229, 255, 0.2); color: var(--accent-cyan); border: 1px solid var(--accent-cyan);">ISO 4217 FIAT</span>`;
          msgEl.style.background = 'rgba(0, 229, 255, 0.08)';
          msgEl.style.border = '1px solid rgba(0, 229, 255, 0.3)';
          msgEl.style.color = '#a5f3fc';
          msgEl.innerText = `💵 ${val.message}`;
          if (adoptBtn) {
            adoptBtn.style.display = 'block';
            adoptBtn.innerText = `Adopt '${val.suggested_name}' Standard 🪄`;
          }
        } else if (val.collision_type === 'MAJOR_CRYPTO') {
          statusTag.innerHTML = `<span class="role-pill-badge" style="background: rgba(245, 158, 11, 0.2); color: #f59e0b; border: 1px solid #f59e0b;">CRYPTO ASSET</span>`;
          msgEl.style.background = 'rgba(245, 158, 11, 0.08)';
          msgEl.style.border = '1px solid rgba(245, 158, 11, 0.3)';
          msgEl.style.color = '#fde68a';
          msgEl.innerText = `🪙 ${val.message}`;
          if (adoptBtn) {
            adoptBtn.style.display = 'block';
            adoptBtn.innerText = `Adopt '${val.suggested_name}' Token Standard 🪄`;
          }
        } else if (val.collision_type === 'COMMODITY_ASSET') {
          statusTag.innerHTML = `<span class="role-pill-badge" style="background: rgba(234, 179, 8, 0.2); color: #eab308; border: 1px solid #eab308;">COMMODITY</span>`;
          msgEl.style.background = 'rgba(234, 179, 8, 0.08)';
          msgEl.style.border = '1px solid rgba(234, 179, 8, 0.3)';
          msgEl.style.color = '#fef08a';
          msgEl.innerText = `🏆 ${val.message}`;
          if (adoptBtn) {
            adoptBtn.style.display = 'block';
            adoptBtn.innerText = `Adopt '${val.suggested_name}' Standard 🪄`;
          }
        } else {
          statusTag.innerHTML = `<span class="role-pill-badge" style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981;">UNIQUE & AVAILABLE</span>`;
          msgEl.style.background = 'rgba(16, 185, 129, 0.08)';
          msgEl.style.border = '1px solid rgba(16, 185, 129, 0.3)';
          msgEl.style.color = '#a7f3d0';
          msgEl.innerText = `✨ ${val.message}`;
          if (adoptBtn) adoptBtn.style.display = 'none';
        }
      }
    } catch (e) {
      console.error("Collision validation error:", e);
    }
  }, 200);
}

function adoptMatchedOfficialCurrency() {
  if (!lastMatchedValidation || !lastMatchedValidation.can_adopt) return;
  const val = lastMatchedValidation;
  const nameInput = document.getElementById('new-curr-name');
  const symbolInput = document.getElementById('new-curr-symbol');
  const rateInput = document.getElementById('new-curr-rate');
  const typeInput = document.getElementById('new-curr-type');

  if (nameInput) nameInput.value = val.suggested_name || "";
  if (symbolInput) symbolInput.value = val.suggested_symbol || "";
  if (rateInput && val.suggested_rate) rateInput.value = val.suggested_rate;
  if (typeInput) typeInput.value = val.suggested_type || "fiat";
}

let catalogSearchDebounce = null;
async function searchGlobalCatalog(query = "") {
  clearTimeout(catalogSearchDebounce);
  catalogSearchDebounce = setTimeout(async () => {
    try {
      const catFilter = document.getElementById('catalog-category-filter');
      const category = catFilter ? catFilter.value : "";
      let url = `/api/currencies/catalog?q=${encodeURIComponent(query || "")}`;
      if (category) url += `&category=${encodeURIComponent(category)}`;
      const res = await secureFetch(url);
      if (!res.ok) return;
      const data = await res.json();
      const items = data.catalog || [];

      const tbody = document.getElementById('global-catalog-table-body');
      if (!tbody) return;

      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 12px;">No matching currencies found in global catalog.</td></tr>`;
        return;
      }

      const activeCodes = new Set((state.currencies || []).filter(c => c.is_active === 1).map(c => c.code));

      tbody.innerHTML = items.map(c => {
        const isAlreadyActive = activeCodes.has(c.code);
        const catBadge = c.category === 'fiat' ? '💵 FIAT' :
                         c.category === 'gold_backed' ? '🏆 GOLD' :
                         c.category === 'crypto' ? '🪙 CRYPTO' :
                         c.category === 'stablecoin' ? '⚖️ STABLE' : '📦 COMMODITY';

        return `
          <tr>
            <td><strong style="font-family: monospace; color: var(--accent-cyan);">${c.code}</strong></td>
            <td>${c.name}</td>
            <td><strong>${c.symbol}</strong></td>
            <td><span class="role-pill-badge" style="font-size: 0.68rem;">${catBadge}</span></td>
            <td style="color: var(--text-muted); font-size: 0.72rem;">${c.country_or_issuer || 'Global'}</td>
            <td style="text-align: center;">
              ${isAlreadyActive ? `
                <span style="font-size: 0.7rem; color: #10b981; font-weight: 700;">Active ✔️</span>
              ` : `
                <button type="button" class="btn-pill-secondary" style="padding: 2px 8px; font-size: 0.7rem;" onclick="adoptCatalogItem('${c.code}', '${c.name.replace(/'/g, "\\'")}', '${c.symbol.replace(/'/g, "\\'")}', '${c.category}', ${c.rate_to_usd || 1.0})">
                  Adopt 📥
                </button>
              `}
            </td>
          </tr>
        `;
      }).join('');
    } catch (e) {
      console.error("Failed to search global catalog:", e);
    }
  }, 150);
}

function adoptCatalogItem(code, name, symbol, category, rate) {
  const codeInput = document.getElementById('new-curr-code');
  const nameInput = document.getElementById('new-curr-name');
  const symbolInput = document.getElementById('new-curr-symbol');
  const rateInput = document.getElementById('new-curr-rate');
  const typeInput = document.getElementById('new-curr-type');

  if (codeInput) codeInput.value = code;
  if (nameInput) nameInput.value = name;
  if (symbolInput) symbolInput.value = symbol;
  if (rateInput) rateInput.value = rate;
  if (typeInput) {
    if (category === 'fiat') typeInput.value = 'fiat';
    else if (category === 'gold_backed') typeInput.value = 'gold_backed';
    else typeInput.value = 'virtual_token';
  }

  handleCurrencyCodeInput(code);
  switchCurrencySubTab('add');
  const formEl = document.getElementById('form-create-currency');
  if (formEl) formEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function switchCurrencySubTab(subTab) {
  const tabs = ['active', 'add', 'catalog'];
  tabs.forEach(t => {
    const btn = document.getElementById(`tab-btn-curr-${t}`);
    const view = document.getElementById(`curr-subview-${t}`);
    if (btn) btn.classList.toggle('active', t === subTab);
    if (view) view.style.display = (t === subTab ? 'block' : 'none');
  });
  if (subTab === 'catalog') {
    searchGlobalCatalog(document.getElementById('catalog-search-input')?.value || "");
  }
}

function togglePanelFullscreen(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const isFs = panel.classList.toggle('panel-fullscreen');
  const btn = panel.querySelector('.btn-panel-expand');
  if (btn) {
    btn.innerHTML = isFs ? '🗗 Restore (Esc)' : '⛶ Expand';
    btn.title = isFs ? 'Exit Fullscreen Mode (or press Esc)' : 'Expand to Fullscreen';
  }
  if (isFs) {
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Global escape key listener to close any expanded panel
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    const fsPanels = document.querySelectorAll('.panel-fullscreen');
    fsPanels.forEach(panel => {
      panel.classList.remove('panel-fullscreen');
      const btn = panel.querySelector('.btn-panel-expand');
      if (btn) {
        btn.innerHTML = '⛶ Expand';
        btn.title = 'Expand to Fullscreen';
      }
    });
  }
});

const LOGIN_POSSIBILITIES = [
  "🌱 <strong>Smart Farming:</strong> Plan crop plantings, get weather advice & maximize harvest yield effortlessly.",
  "💸 <strong>Offline Digital Banking:</strong> Transfer funds & pay for items seamlessly without needing internet.",
  "🏪 <strong>Effortless Touch Register:</strong> Lightning-fast checkouts, automatic change vouchers & live stock sync.",
  "🔒 <strong>100% Private & Sovereign:</strong> Your records stay in your hands, safe, private, and always accessible.",
  "🌐 <strong>Multi-Currency Freedom:</strong> Trade freely in USD, Zimbabwe Gold (ZiG), and custom community tokens.",
  "🤝 <strong>Connected Communities:</strong> Manage multiple shops, staff, and customer accounts in one unified hub."
];

let loginTickerIndex = 0;
let loginTickerTimer = null;

function initLoginPossibilitiesTicker() {
  const textEl = document.getElementById('login-possibilities-text');
  if (!textEl) return;
  clearInterval(loginTickerTimer);

  loginTickerTimer = setInterval(() => {
    loginTickerIndex = (loginTickerIndex + 1) % LOGIN_POSSIBILITIES.length;
    textEl.style.opacity = '0';
    setTimeout(() => {
      textEl.innerHTML = LOGIN_POSSIBILITIES[loginTickerIndex];
      textEl.style.opacity = '1';
    }, 350);
  }, 4200);
}

async function syncGlobalCurrencyCatalog() {
  try {
    const res = await secureFetch("/api/currencies/catalog/sync", { method: "POST" });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      alert(`🌐 Synchronized ${data.result.synced_count || 0} world currencies from Data Node!`);
      searchGlobalCatalog("");
    } else {
      alert("Currency catalog sync completed: " + (data.detail || "Refreshed"));
      searchGlobalCatalog("");
    }
  } catch (e) {
    alert("Currency catalog sync error: " + e.message);
  }
}

async function syncDataNodes() {
  try {
    const res = await secureFetch("/api/cluster/sync-data-nodes", { method: "POST" });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      alert("🔄 State synchronization with connected Data Node storage completed successfully!");
      loadDiscoveredClusterNodes();
    } else {
      alert("Data node sync note: " + (data.detail || "Partial sync"));
    }
  } catch (e) {
    alert("Data node sync error: " + e.message);
  }
}

async function loadCustomerWallet() {
  try {
    const res = await secureFetch("/api/banking/wallet");
    if (!res.ok) return;
    const data = await res.json();
    const w = data.wallet || {};
    state.wallet = w;

    const accNumEl = document.getElementById('wallet-acc-num');
    const ownerEl = document.getElementById('wallet-owner-name');

    if (accNumEl) accNumEl.innerText = w.account_number || "ACC-2026-N/A";
    if (ownerEl) ownerEl.innerText = w.username || (state.user ? state.user.username : 'customer');

    // Dynamically render multi-currency balance cards
    renderBankingBalances();
  } catch (e) {
    console.error("Failed to load wallet:", e);
  }
}

async function loadCustomerReceipts(query = "") {
  try {
    let url = "/api/banking/receipts";
    if (query) url += `?query=${encodeURIComponent(query)}`;
    const res = await secureFetch(url);
    if (!res.ok) return;
    const data = await res.json();
    state.receipts = data.receipts || [];

    const tbody = document.getElementById('customer-receipts-tbody');
    if (!tbody) return;

    if (state.receipts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:16px; color: var(--text-muted);">No archived receipts found in vault.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.receipts.map((rcv, idx) => {
      let rData = {};
      try { rData = JSON.parse(rcv.receipt_json || "{}"); } catch (e) {}
      const itemsPreview = (rData.items || []).map(i => `${i.name || 'Item'} (${i.quantity} ${i.unit || 'unit'})`).join(', ') || "Produce Purchase";
      const totalPaid = rcv.total_due_usd ? `$${rcv.total_due_usd.toFixed(2)} USD` : `$0.00`;
      const dateStr = (rcv.created_at_utc || "").substring(0, 19).replace('T', ' ');

      return `
        <tr>
          <td><strong style="font-family: monospace; color: var(--accent-cyan);">${rcv.invoice_number}</strong></td>
          <td>${dateStr}</td>
          <td><span class="role-pill-badge">${rcv.business_id || 'Primary'}</span></td>
          <td><strong style="color: #fff;">${totalPaid}</strong></td>
          <td style="font-size: 0.78rem; color: var(--text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${itemsPreview}</td>
          <td><code style="font-size: 0.7rem; color: var(--text-muted);">${(rcv.audit_hash || '').substring(0, 16)}...</code></td>
          <td style="text-align: center;">
            <button class="btn-pill-small" onclick="viewArchivedReceipt(${idx})">View Slip 🧾</button>
          </td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error("Failed to load customer receipts:", e);
  }
}

let searchReceiptDebounce = null;
function searchReceiptVault(val) {
  clearTimeout(searchReceiptDebounce);
  searchReceiptDebounce = setTimeout(() => {
    loadCustomerReceipts(val);
  }, 300);
}

function viewArchivedReceipt(idx) {
  const rcv = state.receipts[idx];
  if (!rcv) return;
  try {
    const receiptData = JSON.parse(rcv.receipt_json || "{}");
    const biz = state.businesses.find(b => b.id === rcv.business_id) || { name: rcv.business_id, category: "Produce", location_address: "Bulawayo, Zimbabwe" };
    receiptData.business = biz;
    receiptData.items = (receiptData.items || []).map(i => ({
      item_name: i.name || "Item",
      quantity: i.quantity,
      price_usd_at_sale: i.price_usd_at_sale
    }));
    showReceiptModal(receiptData);
  } catch (e) {
    alert("Could not load receipt: " + e.message);
  }
}

async function loadWalletLedger() {
  try {
    const res = await secureFetch("/api/banking/ledger?limit=50");
    if (!res.ok) return;
    const data = await res.json();
    state.walletLedger = data.ledger || [];

    const tbody = document.getElementById('wallet-ledger-tbody');
    if (!tbody) return;

    if (state.walletLedger.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:16px; color: var(--text-muted);">No ledger activity recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.walletLedger.map(entry => {
      const isPositive = entry.amount >= 0;
      const amtColor = isPositive ? '#10b981' : '#f87171';
      const sign = isPositive ? '+' : '';
      const dateStr = (entry.timestamp_utc || "").substring(0, 19).replace('T', ' ');

      return `
        <tr>
          <td><code style="font-size: 0.75rem;">${entry.id}</code></td>
          <td>${dateStr}</td>
          <td><span class="role-pill-badge">${entry.transaction_type.toUpperCase()}</span></td>
          <td><strong>${entry.currency}</strong></td>
          <td style="color: ${amtColor}; font-weight: 700;">${sign}${entry.amount.toFixed(2)} ${entry.currency}</td>
          <td><strong>${entry.balance_after.toFixed(2)} ${entry.currency}</strong></td>
          <td>${entry.counterparty || 'system'}</td>
          <td style="font-size: 0.75rem; color: var(--text-muted);">${entry.notes || ''}</td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error("Failed to load wallet ledger:", e);
  }
}

function openTopupModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-topup-wallet').style.display = 'block';
}

async function submitTopupWallet() {
  const curr = document.getElementById('topup-currency').value;
  const amt = parseFloat(document.getElementById('topup-amount').value || "0");
  const notes = document.getElementById('topup-notes').value.trim() || "Cash Deposit at Node";

  if (amt <= 0) {
    alert("Please enter a valid deposit amount.");
    return;
  }

  try {
    const res = await secureFetch("/api/banking/topup", {
      method: "POST",
      body: JSON.stringify({
        currency: curr,
        amount: amt,
        notes: notes
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      alert(`💵 Successfully deposited ${amt.toFixed(2)} ${curr} to your account!`);
      hideModals();
      loadCustomerWallet();
      loadWalletLedger();
    } else {
      alert("Deposit failed: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Deposit error: " + e.message);
  }
}

function openP2PModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-p2p-transfer').style.display = 'block';
}

async function submitP2PTransfer() {
  const toUser = document.getElementById('p2p-to-user').value.trim();
  const curr = document.getElementById('p2p-currency').value;
  const amt = parseFloat(document.getElementById('p2p-amount').value || "0");
  const notes = document.getElementById('p2p-notes').value.trim() || "P2P Transfer";

  if (!toUser) {
    alert("Please enter a recipient username.");
    return;
  }
  if (amt <= 0) {
    alert("Please enter a valid transfer amount.");
    return;
  }

  try {
    const res = await secureFetch("/api/banking/transfer", {
      method: "POST",
      body: JSON.stringify({
        to_user: toUser,
        currency: curr,
        amount: amt,
        notes: notes
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      alert(`↗️ Sent ${amt.toFixed(2)} ${curr} to @${toUser} successfully!`);
      hideModals();
      loadCustomerWallet();
      loadWalletLedger();
    } else {
      alert("Transfer failed: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Transfer error: " + e.message);
  }
}

function openDepositVoucherModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-deposit-voucher').style.display = 'block';
}

async function submitDepositVoucher() {
  const vid = document.getElementById('vouch-deposit-input').value.trim();
  if (!vid) {
    alert("Please enter a Voucher ID.");
    return;
  }

  try {
    const res = await secureFetch("/api/banking/deposit-voucher", {
      method: "POST",
      body: JSON.stringify({ vid: vid })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      const dep = data.deposit;
      alert(`🎟️ Voucher ${dep.vid} converted!\nCredited ${dep.amount_credited} ${dep.currency} to your wallet.\nNew Balance: ${dep.new_balance.toFixed(2)} ${dep.currency}`);
      hideModals();
      loadCustomerWallet();
      loadWalletLedger();
    } else {
      alert("Voucher deposit failed: " + (data.detail || "Invalid or redeemed voucher."));
    }
  } catch (e) {
    alert("Voucher deposit error: " + e.message);
  }
}

// =====================================================================
// STAGE 1 CORE: CLUSTER TOPOLOGY & PORTABLE NODE GENERATOR MODULE
// =====================================================================
function initClusterModule() {
  loadDiscoveredClusterNodes();
  loadExportedNodePackages();
}

async function loadDiscoveredClusterNodes() {
  try {
    const res = await secureFetch("/api/nodes/discovered");
    if (!res.ok) return;
    const data = await res.json();
    state.clusterNodes = data.cluster_nodes || [];
    updateDashboardLiveFeeds();

    const grid = document.getElementById('cluster-nodes-grid');
    if (!grid) return;

    if (state.clusterNodes.length === 0) {
      grid.innerHTML = `<div class="glass-panel" style="padding: 24px; text-align: center; color: var(--text-muted); grid-column: 1 / -1;">No external Data Nodes broadcasting beacons right now. Launching <code>python start.py</code> or <code>python Applications/Data_Node/data_node.py</code> will broadcast discovery heartbeats on UDP 224.0.0.251:8001.</div>`;
      return;
    }

    grid.innerHTML = state.clusterNodes.map(n => {
      const meta = n.metadata || {};
      const isActive = meta.is_active !== false;
      const statusBadge = isActive ? '<span style="color:#10b981; font-weight:700;">🟢 Active</span>' : '<span style="color:#f43f5e; font-weight:700;">🔴 Deactivated (Standby)</span>';
      const toggleAction = isActive ? 'Deactivate' : 'Activate';
      const toggleColor = isActive ? 'border: 1px solid rgba(244,63,94,0.4); color: #f43f5e;' : 'border: 1px solid rgba(16,185,129,0.4); color: #10b981;';

      return `
        <div class="node-card" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <strong style="color: #fff; font-size: 1.05rem; font-family: monospace;">${n.node_id}</strong>
            ${statusBadge}
          </div>

          <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">Name: <strong style="color: #fff;">${meta.node_name || n.node_id}</strong></p>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">Role: <span class="role-pill-badge">${(n.node_type || 'data_node').toUpperCase()}</span></p>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 6px;">Network Address: <code style="color: var(--accent-cyan);">${n.ip}:${n.port}</code></p>
          <p style="font-size: 0.8rem; color: var(--text-muted); margin-bottom: 14px;">Free Storage: <strong>${meta.free_mb ? meta.free_mb.toLocaleString() + ' MB' : 'Available'}</strong></p>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; gap: 8px;">
            <span style="font-size: 0.72rem; color: var(--text-muted);">Age: ${n.age_seconds || 0}s</span>
            <button class="btn-pill-small" style="${toggleColor}" onclick="toggleNodeActiveState('${n.node_id}', ${!isActive})">
              ${toggleAction} Node ⚡
            </button>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error("Failed to load cluster nodes:", e);
  }
}

async function toggleNodeActiveState(nodeId, targetState) {
  try {
    const res = await secureFetch(`/api/cluster/nodes/${encodeURIComponent(nodeId)}/toggle-active`, {
      method: "POST",
      body: JSON.stringify({ is_active: targetState })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      alert(`Node '${nodeId}' set to ${targetState ? 'ACTIVE' : 'DEACTIVATED'}!`);
      loadDiscoveredClusterNodes();
    } else {
      alert("Failed to toggle node: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Node toggle error: " + e.message);
  }
}

function openGenerateNodeModal() {
  document.getElementById('modal-overlay').style.display = 'flex';
  document.getElementById('modal-generate-portable-node').style.display = 'block';
}

async function submitGenerateNodePack() {
  const name = document.getElementById('gen-node-name').value.trim();
  const nType = document.getElementById('gen-node-type').value;
  const port = parseInt(document.getElementById('gen-node-port').value || "8005", 10);
  const quota = parseInt(document.getElementById('gen-node-quota').value || "2048", 10);

  if (!name) {
    alert("Please enter a Node Name.");
    return;
  }

  try {
    const res = await secureFetch("/api/cluster/nodes/generate-portable", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        node_type: nType,
        port: port,
        storage_quota_mb: quota
      })
    });
    const data = await res.json();
    if (res.ok && data.status === "success") {
      const pkg = data.package;
      alert(`📦 Standalone Portable Node Pack '${name}' Created!\n\nFolder: ${pkg.node_dir}\nPort: ${pkg.port}\nLaunch: python "${pkg.node_dir}/start.py"`);
      hideModals();
      loadExportedNodePackages();
    } else {
      alert("Bundle generation failed: " + (data.detail || "Error"));
    }
  } catch (e) {
    alert("Generation error: " + e.message);
  }
}

async function loadExportedNodePackages() {
  try {
    const res = await secureFetch("/api/cluster/nodes/exported-list");
    if (!res.ok) return;
    const data = await res.json();
    const packs = data.exported_nodes || [];
    const tbody = document.getElementById('exported-nodes-table-body');
    if (!tbody) return;

    if (packs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding:16px; color: var(--text-muted);">No standalone node packages generated yet. Click "Export Portable Node Pack" above to create one.</td></tr>`;
      return;
    }

    tbody.innerHTML = packs.map(p => `
      <tr>
        <td><strong style="color: #fff;">${p.node_name || p.node_id}</strong></td>
        <td><span class="role-pill-badge">${(p.node_type || 'data_node').toUpperCase()}</span></td>
        <td><code style="color: var(--accent-cyan); font-weight:700;">:${p.port}</code></td>
        <td style="font-size:0.75rem; color: var(--text-muted); max-width:260px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${p.node_dir || 'Applications/Exported_Nodes/'}</td>
        <td><code style="font-size:0.78rem; background:rgba(0,0,0,0.3); padding:4px 8px; border-radius:6px;">python "${p.node_dir ? p.node_dir + '/start.py' : 'start.py'}"</code></td>
      </tr>
    `).join('');
  } catch (e) {
    console.error("Failed to load exported node packages:", e);
  }
}

// =====================================================================
// STAGE 1 CORE: ADMIN CONTROL MODULE
// =====================================================================
async function loadAdminUsers() {
  try {
    const res = await secureFetch("/api/admin/users");
    if (!res.ok) return;
    const users = await res.json();
    const tbody = document.getElementById('admin-users-table-body');
    if (tbody) {
      tbody.innerHTML = users.map(u => `
        <tr>
          <td><strong>${u.username}</strong></td>
          <td><span class="role-pill-badge">${u.role.toUpperCase()}</span></td>
          <td><span style="color: ${u.status === 'active' ? '#10b981' : '#f87171'}; font-weight: 700;">${u.status.toUpperCase()}</span></td>
          <td style="text-align: center;"><button class="btn-pill-small" onclick="alert('Manage user: ${u.username}')">Configure</button></td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.error(e);
  }
}

async function loadAdminDevices() {
  try {
    const res = await secureFetch("/api/security/devices");
    if (!res.ok) return;
    const devices = await res.json();
    const tbody = document.getElementById('admin-devices-table-body');
    if (tbody) {
      tbody.innerHTML = devices.map(d => `
        <tr>
          <td><code>${d.ip}</code></td>
          <td>${d.type}</td>
          <td><span style="font-size: 0.75rem; color: var(--text-muted);">${(d.user_agent || '').substring(0, 30)}...</span></td>
          <td>${d.last_user || 'guest'}</td>
          <td><span style="color: ${d.status === 'allowed' ? '#10b981' : '#f87171'}; font-weight: 700;">${d.status.toUpperCase()}</span></td>
          <td style="text-align: center;"><button class="btn-pill-small" onclick="alert('Device: ${d.ip}')">Inspect</button></td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.error(e);
  }
}

async function loadAdminAuditLogs() {
  try {
    const res = await secureFetch("/api/security/audit-logs");
    if (!res.ok) return;
    const logs = await res.json();
    const tbody = document.getElementById('admin-audit-table-body');
    if (tbody) {
      tbody.innerHTML = logs.map(l => `
        <tr>
          <td>${l.seq}</td>
          <td>${l.time ? l.time.substring(11, 19) : ''}</td>
          <td><strong>${l.actor}</strong></td>
          <td style="color: var(--accent-cyan);">${l.action}</td>
          <td>${l.details}</td>
          <td><code style="font-size: 0.7rem; color: var(--text-muted);">${(l.record_hash || '').substring(0, 16)}...</code></td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.error(e);
  }
}

// --- PASSWORD VISIBILITY TOGGLE ---
function togglePasswordVisibility(inputId, btnElement) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    if (btnElement) btnElement.innerText = '🔒';
  } else {
    input.type = 'password';
    if (btnElement) btnElement.innerText = '👁️';
  }
}

// --- LOCAL NETWORK & MOBILE QR GATEWAY ---
async function fetchNetworkInfo() {
  try {
    const res = await fetch("/api/network/info");
    if (res.ok) {
      const data = await res.json();
      state.networkInfo = data;
      const lanBadge = document.getElementById('header-lan-ip-text');
      if (lanBadge && data.primary_url) {
        const shortUrl = data.primary_url.replace("https://", "").replace("http://", "");
        const isHttps = data.primary_url.startsWith("https://") || window.location.protocol === "https:";
        lanBadge.innerText = `${isHttps ? '🔒 HTTPS:' : 'LAN:'} ${shortUrl}`;
      }
      updateDashboardLiveFeeds();
    }
  } catch (e) {
    console.warn("Could not fetch network interface info:", e);
  }
}

function drawNetworkQRCode(url) {
  const canvas = document.getElementById('canvas-network-qr');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const gridSize = 25;
  const cellSize = Math.floor(canvas.width / gridSize);
  ctx.fillStyle = '#000000';

  function drawFinder(x, y) {
    ctx.fillRect(x * cellSize, y * cellSize, 7 * cellSize, 7 * cellSize);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect((x + 1) * cellSize, (y + 1) * cellSize, 5 * cellSize, 5 * cellSize);
    ctx.fillStyle = '#000000';
    ctx.fillRect((x + 2) * cellSize, (y + 2) * cellSize, 3 * cellSize, 3 * cellSize);
  }
  drawFinder(1, 1);
  drawFinder(gridSize - 8, 1);
  drawFinder(1, gridSize - 8);

  let hashVal = 0;
  for (let i = 0; i < url.length; i++) {
    hashVal = (hashVal << 5) - hashVal + url.charCodeAt(i);
    hashVal |= 0;
  }
  for (let r = 0; r < gridSize; r++) {
    for (let c = 0; c < gridSize; c++) {
      if ((r < 8 && c < 8) || (r < 8 && c >= gridSize - 8) || (r >= gridSize - 8 && c < 8)) continue;
      const bit = Math.abs((hashVal ^ (r * 37 + c * 23 + (r * c)))) % 2;
      if (bit === 1) {
        ctx.fillRect(c * cellSize, r * cellSize, cellSize - 1, cellSize - 1);
      }
    }
  }
}

function openNetworkQRModal() {
  const isHttps = window.location.protocol === 'https:';
  const defScheme = isHttps ? 'https' : 'http';
  const net = state.networkInfo || {
    primary_url: `${defScheme}://${window.location.host}`,
    local_ips: [window.location.hostname],
    network_urls: [`${defScheme}://${window.location.host}`]
  };

  const primaryUrl = net.primary_url || `${defScheme}://${window.location.host}`;
  const codeEl = document.getElementById('modal-lan-primary-url');
  if (codeEl) codeEl.innerText = primaryUrl;

  const ipsList = document.getElementById('modal-lan-ips-list');
  if (ipsList) {
    ipsList.innerHTML = '';
    const allUrls = (net.network_urls && net.network_urls.length > 0) ? net.network_urls : [primaryUrl];
    allUrls.forEach(url => {
      const row = document.createElement('div');
      row.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; background: rgba(255,255,255,0.04); border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);';
      row.innerHTML = `
        <span style="color: #38bdf8; font-weight: 600;">${url}</span>
        <button type="button" class="btn-pill-small" style="padding: 3px 10px; font-size: 0.7rem;" onclick="navigator.clipboard.writeText('${url}'); showToast('Copied ${url} to clipboard!', 'success');">Copy</button>
      `;
      ipsList.appendChild(row);
    });
  }

  drawNetworkQRCode(primaryUrl);

  const modalOverlay = document.getElementById('modal-overlay');
  const networkModal = document.getElementById('modal-network-qr');
  if (modalOverlay && networkModal) {
    modalOverlay.style.display = 'flex';
    networkModal.style.display = 'block';
  }
}

function copyPrimaryLanUrl() {
  const isHttps = window.location.protocol === 'https:';
  const defScheme = isHttps ? 'https' : 'http';
  const url = (state.networkInfo && state.networkInfo.primary_url) || `${defScheme}://${window.location.host}`;
  navigator.clipboard.writeText(url).then(() => {
    showToast(`Copied ${url} to clipboard!`, 'success');
  }).catch(() => {
    showToast(`URL: ${url}`, 'info');
  });
}

// --- NEW PLANTING MODAL HANDLERS ---
function openNewPlantingModal() {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('modal-new-planting');
  if (overlay && modal) {
    overlay.style.display = 'flex';
    modal.style.display = 'block';
  }
}

async function submitNewPlanting() {
  const crop = (document.getElementById('planting-crop-variety') || {}).value?.trim();
  const plot = (document.getElementById('planting-plot-bed') || document.getElementById('planting-plot-bed-id') || {}).value?.trim();
  const density = parseFloat((document.getElementById('planting-density') || document.getElementById('planting-seeding-density') || {}).value || "4.0");
  const hydration = parseFloat((document.getElementById('planting-hydration') || document.getElementById('planting-soil-hydration') || {}).value || "65.0");
  const pDate = (document.getElementById('planting-date') || {}).value || new Date().toISOString().substring(0, 10);
  const mDate = (document.getElementById('planting-maturity-date') || {}).value || "";
  const notes = (document.getElementById('planting-notes') || {}).value?.trim() || "";

  if (!crop || !plot) {
    showToast("Please enter crop variety and plot identifier.", "warning");
    return;
  }

  try {
    const res = await secureFetch("/api/agri/plantings", {
      method: "POST",
      body: JSON.stringify({
        crop_variety: crop,
        plot_bed_id: plot,
        seeding_density: density,
        initial_soil_hydration_pct: hydration,
        planting_date_utc: pDate,
        target_maturity_date_utc: mDate,
        notes: notes,
        business_id: state.activeBusinessId || "biz-green-valley"
      })
    });

    if (res.ok) {
      hideModals();
      showToast(`Logged planting: ${crop} in ${plot}!`, "success");
      loadPlantings();
    } else {
      const err = await res.json().catch(() => ({ detail: "Failed to create planting." }));
      showToast(err.detail || "Failed to create planting.", "danger");
    }
  } catch (e) {
    showToast("Failed to create planting: " + e.message, "danger");
  }
}

// --- VISITOR CHECK-IN MODAL HANDLERS ---
function openCheckinVisitorModal() {
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('modal-checkin-visitor');
  if (overlay && modal) {
    overlay.style.display = 'flex';
    modal.style.display = 'block';
  }
}

async function submitCheckinVisitor() {
  const name = (document.getElementById('vis-full-name') || {}).value?.trim();
  const nid = (document.getElementById('vis-national-id') || {}).value?.trim();
  const env = (document.getElementById('vis-destination') || document.getElementById('vis-destination-env') || {}).value || "Administration Hub";
  const purpose = (document.getElementById('vis-purpose') || {}).value?.trim() || "Official Business";
  const escort = (document.getElementById('vis-escort') || document.getElementById('vis-escort-officer') || {}).value?.trim() || "Duty Officer";
  const notes = (document.getElementById('vis-notes') || {}).value?.trim() || "";

  if (!name || !nid) {
    showToast("Visitor Full Name and National ID are required.", "warning");
    return;
  }

  try {
    const res = await secureFetch("/api/security/visitors/checkin", {
      method: "POST",
      body: JSON.stringify({
        national_id: nid,
        full_name: name,
        destination_env: env,
        escort_officer: escort,
        purpose: purpose,
        notes: notes
      })
    });

    if (res.ok) {
      hideModals();
      showToast(`Visitor ${name} authorized & checked in!`, "success");
      loadActiveVisitors();
      loadVisitorHistory();
    } else {
      const err = await res.json().catch(() => ({ detail: "Check-in failed." }));
      showToast(err.detail || "Check-in failed.", "danger");
    }
  } catch (e) {
    showToast("Check-in failed: " + e.message, "danger");
  }
}

// --- TUTORIALS & GUIDED SYSTEM TOUR ---
function switchTutorialTrack(trackId, btnElement) {
  const allPanes = document.querySelectorAll('.tutorial-track-pane');
  allPanes.forEach(p => p.style.display = 'none');

  const targetPane = document.getElementById(`tut-pane-${trackId}`);
  if (targetPane) targetPane.style.display = 'block';

  const allTabs = document.querySelectorAll('#view-tutorials .tab-pill-btn');
  allTabs.forEach(t => t.classList.remove('active'));

  if (btnElement) {
    btnElement.classList.add('active');
  } else {
    const defaultBtn = document.getElementById(`btn-tut-track-${trackId}`);
    if (defaultBtn) defaultBtn.classList.add('active');
  }
}

function startInteractiveTour() {
  const steps = [
    { el: '#header-business-select', text: "🏢 Store Switcher: Seamlessly switch between different businesses without logging out." },
    { el: '#role-switcher-select', text: "👑 Composable Role: Switch your operating context between Admin, Agronomist, Guard, Merchant, and Customer." },
    { el: '#btn-header-lan-info', text: "📱 Mobile LAN QR Connect: Click here to show the QR code for smartphones on your Wi-Fi to connect instantly." },
    { el: '#app-sidebar', text: "🧭 Navigation Drawer: Access Precision Agriculture, Security Gatekeeper, POS, Digital Banking, Cluster Nodes, and Tutorials." },
    { el: '#nav-tutorials', text: "📖 Tutorial Center: Open comprehensive system masterclasses and mathematical guides at any time!" }
  ];

  let currentStep = 0;

  function showStep(idx) {
    if (idx >= steps.length) {
      showToast("🎓 Guided Tour Complete! You're ready to operate MADN.", "success");
      return;
    }
    const step = steps[idx];
    const target = document.querySelector(step.el);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      target.style.transition = 'all 0.3s ease';
      target.style.outline = '3px solid #00e5ff';
      target.style.boxShadow = '0 0 25px rgba(0, 229, 255, 0.6)';

      showToast(`Step ${idx + 1}/${steps.length}: ${step.text}`, 'info');

      setTimeout(() => {
        target.style.outline = '';
        target.style.boxShadow = '';
        showStep(idx + 1);
      }, 3500);
    } else {
      showStep(idx + 1);
    }
  }

  showStep(0);
}

