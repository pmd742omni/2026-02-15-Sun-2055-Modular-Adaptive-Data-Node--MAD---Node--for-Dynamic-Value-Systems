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

// --- CORE UTILITY FUNCTIONS ---
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// --- CREDENTIAL & FIELD MASKING VISIBILITY ENGINE ---
function toggleFieldMasking(inputId, btnElement) {
  const input = document.getElementById(inputId);
  if (!input) return;
  
  if (input.type === 'password') {
    // Reveal text
    input.type = 'text';
    if (btnElement) {
      btnElement.innerHTML = '🙈';
      btnElement.title = 'Hide / Mask characters';
      btnElement.setAttribute('aria-label', btnElement.title);
    }
  } else {
    // Mask text
    input.type = 'password';
    if (btnElement) {
      btnElement.innerHTML = '👁️';
      btnElement.title = 'Show / Reveal characters';
      btnElement.setAttribute('aria-label', btnElement.title);
    }
  }
}

function togglePasswordVisibility(inputId, btnElement) {
  toggleFieldMasking(inputId, btnElement);
}

window.toggleFieldMasking = toggleFieldMasking;
window.togglePasswordVisibility = togglePasswordVisibility;

// --- SOVEREIGN OBSIDIAN GLASSMORPHIC TOAST NOTIFICATION ENGINE ---
function showToast(message, type = 'info', duration = 3500) {
  let toastContainer = document.getElementById('madn-toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'madn-toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      top: 24px;
      right: 24px;
      z-index: 99999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
      max-width: 420px;
      width: calc(100vw - 48px);
    `;
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  toast.className = `glass-panel madn-toast madn-toast-${type}`;
  
  const iconMap = {
    success: '✅',
    danger: '❌',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const borderMap = {
    success: 'rgba(16, 185, 129, 0.4)',
    danger: 'rgba(239, 68, 68, 0.4)',
    error: 'rgba(239, 68, 68, 0.4)',
    warning: 'rgba(245, 158, 11, 0.4)',
    info: 'rgba(0, 229, 255, 0.4)'
  };

  const bgMap = {
    success: 'rgba(16, 185, 129, 0.18)',
    danger: 'rgba(239, 68, 68, 0.22)',
    error: 'rgba(239, 68, 68, 0.22)',
    warning: 'rgba(245, 158, 11, 0.18)',
    info: 'rgba(0, 229, 255, 0.15)'
  };

  const currentIcon = iconMap[type] || '✨';
  const currentBorder = borderMap[type] || 'rgba(255,255,255,0.15)';
  const currentBg = bgMap[type] || 'rgba(15, 23, 42, 0.9)';

  toast.style.cssText = `
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 18px;
    border-radius: 16px;
    background: ${currentBg};
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid ${currentBorder};
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), 0 0 20px ${currentBorder};
    color: #fff;
    font-size: 0.88rem;
    line-height: 1.4;
    font-weight: 500;
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  `;

  toast.innerHTML = `
    <span style="font-size: 1.2rem; flex-shrink: 0;">${currentIcon}</span>
    <span style="flex-grow: 1; color: #fff; word-break: break-word;">${escapeHtml(message)}</span>
    <button type="button" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.9rem; padding: 2px 6px; margin-left: 4px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: color 0.2s;" onclick="this.parentElement.remove()">✕</button>
  `;

  toastContainer.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0) scale(1)';
  });

  // Auto dismiss
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(-10px) scale(0.95)';
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 350);
  }, duration);
}

function showSuccessToast(message, duration = 3500) {
  showToast(message, 'success', duration);
}

function showErrorToast(message, duration = 4000) {
  showToast(message, 'danger', duration);
}

function showInfoToast(message, duration = 3500) {
  showToast(message, 'info', duration);
}

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

// --- UNIVERSAL LATEX & MATHEMATICAL EQUATION RENDERER (FAST NON-BLOCKING EXECUTION) ---
function renderLatexInUI(rootEl) {
  const container = rootEl || document.querySelector('.view-section.active');
  if (!container || container.dataset.mathRendered) return;

  // 1. If KaTeX Auto-Renderer is available, run it on active view
  if (typeof window.renderMathInElement === 'function') {
    try {
      window.renderMathInElement(container, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '\\[', right: '\\]', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false }
        ],
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option", "input", "select", "table", "tbody", "thead", "tr", "td"],
        throwOnError: false
      });
      container.dataset.mathRendered = "true";
      return;
    } catch (e) {
      console.warn("KaTeX render notice:", e);
    }
  }

  // 2. High-Fidelity Standalone Fallback Parser (only runs on explicit math containers)
  const mathTargets = container.querySelectorAll('.math-expr, .katex-display, .latex-formula, [data-latex]');
  if (!mathTargets || !mathTargets.length) return;

  mathTargets.forEach(el => {
    if (el.dataset.latexRendered) return;
    el.dataset.latexRendered = "true";
    const raw = el.innerText || el.textContent;
    if (raw && (/\\\(|\$\$|\$|\\\[|\\frac|\\ge|\\le|\\lambda|\\mu|\\cdot|\\text\{/.test(raw))) {
      el.innerHTML = formatLatexToHtml(raw);
    }
  });
  container.dataset.mathRendered = "true";
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
window.openAvatarStudioModal = openAvatarStudioModal;
window.handleStudioAvatarFileSelected = handleStudioAvatarFileSelected;
window.submitStudioAvatarSave = submitStudioAvatarSave;
window.openAvatarLightbox = openAvatarLightbox;

let _modulesInitialized = false;
function ensureModulesInitialized() {
  if (_modulesInitialized) return;
  _modulesInitialized = true;
  initAgriModule();
  initSecurityModule();
  initSocialModule();
  initPOSModule();
  initClusterModule();
}

// --- INITIALIZATION (LIGHTWEIGHT ZERO-BLOCKING BOOTSTRAP) ---
document.addEventListener('DOMContentLoaded', () => {
  initAuthSystem();
  initLoginPossibilitiesTicker();
  initNavigation();

  // Check active session & load data ONLY if user is authenticated
  checkActiveSession().then((user) => {
    if (user) {
      ensureModulesInitialized();
      loadAllSubsystemData();
      renderLatexInUI();
      fetchNetworkInfo();
    }
  });

  // Ticker for continuous decay update and Data Node live telemetry sync (only when active)
  setInterval(() => {
    if (state.activeView === 'business' && state.user) {
      loadPosProducts();
      loadMarketplaceCatalog();
    }
    if (state.user) {
      pingDataNodeTelemetry();
    }
  }, 10000);
});

async function pingDataNodeTelemetry() {
  try {
    fetch("http://127.0.0.1:8002/api/node/status", { mode: "cors" }).catch(() => {});
  } catch (e) {}
}

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
  let sessionToken = null;
  try {
    sessionToken = sessionStorage.getItem("madn_session_token") || localStorage.getItem("madn_session_token");
  } catch (e) {}
  if (sessionToken) {
    if (!options.headers["X-Session-Token"]) options.headers["X-Session-Token"] = sessionToken;
    if (!options.headers["Authorization"]) options.headers["Authorization"] = `Bearer ${sessionToken}`;
  }
  if (!options.headers["Content-Type"] && !(options.body instanceof FormData)) {
    options.headers["Content-Type"] = "application/json";
  }
  if (!options.credentials) {
    options.credentials = "include";
  }

  try {
    const response = await fetch(url, options);
    if (response.status === 401) {
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

// --- FULLSCREEN CANVAS FIREWORK & PARTICLE EXPLOSION ENGINE ---
function triggerLaunchExplosion(buttonEl) {
  const oldCanvas = document.getElementById('auth-explosion-canvas');
  if (oldCanvas) oldCanvas.remove();

  const canvas = document.createElement('canvas');
  canvas.id = 'auth-explosion-canvas';
  canvas.style.position = 'fixed';
  canvas.style.top = '0px';
  canvas.style.left = '0px';
  canvas.style.width = '100vw';
  canvas.style.height = '100vh';
  canvas.style.pointerEvents = 'none';
  canvas.style.zIndex = '999999';
  document.body.appendChild(canvas);

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const ctx = canvas.getContext('2d');

  let rect = buttonEl ? buttonEl.getBoundingClientRect() : null;
  if (!rect || (rect.width === 0 && rect.height === 0)) {
    rect = { left: window.innerWidth / 2 - 60, top: window.innerHeight / 2 - 20, width: 120, height: 40 };
  }
  const originX = rect.left + rect.width / 2;
  const originY = rect.top + rect.height / 2;

  const particles = [];
  const colors = ['#00e5ff', '#10b981', '#fbbf24', '#38bdf8', '#ffffff'];

  // Lightweight high-speed sparks (zero shadowBlur for 120fps hardware acceleration)
  for (let i = 0; i < 36; i++) {
    const angle = Math.random() * Math.PI * 2;
    const speed = 4 + Math.random() * 10;
    particles.push({
      x: originX,
      y: originY,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed - 2,
      color: colors[Math.floor(Math.random() * colors.length)],
      radius: 2 + Math.random() * 3,
      alpha: 1,
      decay: 0.03 + Math.random() * 0.02,
      gravity: 0.18
    });
  }

  const startTime = performance.now();
  const duration = 650;

  function animate(currentTime) {
    const elapsed = currentTime - startTime;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    for (const p of particles) {
      if (p.alpha <= 0.02) continue;
      p.x += p.vx;
      p.y += p.vy;
      p.vy += p.gravity;
      p.vx *= 0.96;
      p.alpha -= p.decay;

      ctx.globalAlpha = Math.max(0, p.alpha);
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();
    }

    ctx.globalAlpha = 1;

    if (elapsed < duration) {
      requestAnimationFrame(animate);
    } else {
      canvas.remove();
    }
  }

  requestAnimationFrame(animate);
}

// --- AUTHENTICATION & SESSION ---
function initAuthSystem() {
  const btnLogin = document.getElementById('btn-login-submit');
  const formLogin = document.getElementById('form-login');
  let isAuthSubmitting = false;

  const executeLogin = async () => {
    if (isAuthSubmitting) return;

    const uEl = document.getElementById('login-username');
    const pEl = document.getElementById('login-password');
    const u = uEl ? uEl.value.trim() : '';
    const p = pEl ? pEl.value : '';
    const mfa = document.getElementById('login-mfa-token')?.value.trim() || '';
    const errBox = document.getElementById('login-error');

    if (!u || !p) {
      if (errBox) {
        errBox.style.display = 'block';
        errBox.innerText = "Please enter both username and password.";
      }
      if (!u && uEl) uEl.focus();
      else if (!p && pEl) pEl.focus();
      return;
    }

    isAuthSubmitting = true;
    if (errBox) errBox.style.display = 'none';

    const cardLogin = document.getElementById('card-login');
    const cardJourney = document.getElementById('card-journey');

    // 1. Show card-journey strictly as single active card
    if (cardLogin && cardJourney) {
      cardLogin.style.setProperty('display', 'none', 'important');
      cardJourney.style.setProperty('display', 'block', 'important');

      // Reset journey elements
      const iconEl = document.getElementById('journey-icon');
      const hlEl = document.getElementById('journey-headline');
      const subEl = document.getElementById('journey-subtext');
      const barEl = document.getElementById('journey-progress-bar');
      
      if (iconEl) iconEl.innerText = '✨';
      if (hlEl) hlEl.innerText = 'Opening your space... ✨';
      if (subEl) subEl.innerText = 'Checking your credentials... 🔑';
      if (barEl) barEl.style.width = '25%';

      for (let i = 1; i <= 4; i++) {
        const stepEl = document.getElementById(`journey-step-${i}`);
        const sIcon = document.getElementById(`journey-step-${i}-icon`);
        if (stepEl) stepEl.style.color = i === 1 ? '#fff' : 'var(--text-muted)';
        if (sIcon) sIcon.innerText = i === 1 ? '⏳' : '⚪';
      }
    }

    const resetToLoginCard = (errorMsg) => {
      if (cardJourney && cardLogin) {
        cardJourney.style.setProperty('display', 'none', 'important');
        cardLogin.style.setProperty('display', 'block', 'important');
      }
      if (errBox) {
        errBox.style.display = 'block';
        errBox.innerText = errorMsg || "Authentication failed.";
      }
      if (btnLogin) {
        btnLogin.disabled = false;
        btnLogin.innerHTML = `<span id="btn-login-text">Let's Go!</span> <span id="btn-login-rocket" style="display: inline-block; animation: rocketPulse 1.8s infinite ease-in-out; font-size: 1.2rem;">🚀✨</span>`;
      }
      const pwInput = document.getElementById('login-password');
      if (pwInput) pwInput.focus();
    };

    let authSucceeded = false;
    let authData = null;

    try {
      window._isAuthTransitioning = true;
      const authBody = { username: u, password: p };
      if (mfa) authBody.totp_token = mfa;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      // Start auth request in parallel with timeout protection & credentials: "include"
      const authPromise = fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(authBody),
        credentials: "include",
        signal: controller.signal
      });

      // Stage 1: Checking credentials in real-time
      const res = await authPromise;
      clearTimeout(timeoutId);

      if (!res.ok) {
        const data = await res.json().catch(() => ({ detail: "Invalid credentials." }));
        if (data.detail && data.detail.includes("MFA code required")) {
          document.getElementById('login-mfa-group').style.display = 'block';
          resetToLoginCard("MFA Authenticator code required for this account.");
          return;
        }
        resetToLoginCard(data.detail || "Invalid username or password.");
        return;
      }

      authData = await res.json();
      authSucceeded = true;
    } catch (e) {
      if (!authSucceeded) {
        resetToLoginCard(e.message || "Network error. Server might be restarting.");
        return;
      }
    }

    if (!authSucceeded || !authData) return;

    // --- FROM THIS POINT FORWARD, OPERATOR IS FULLY AUTHENTICATED ---
    try {
      if (authData.session_token) {
        try {
          sessionStorage.setItem("madn_session_token", authData.session_token);
          localStorage.setItem("madn_session_token", authData.session_token);
        } catch(e) {}
      }
      state.user = authData;
      state.currentRole = authData.role;
      updateUserUI(authData);

      // Stage 2: Connecting with community (fast 70ms step)
      const barEl = document.getElementById('journey-progress-bar');
      const subEl = document.getElementById('journey-subtext');
      const iconEl = document.getElementById('journey-icon');
      const s1Icon = document.getElementById('journey-step-1-icon');
      const s1El = document.getElementById('journey-step-1');
      const s2Icon = document.getElementById('journey-step-2-icon');
      const s2El = document.getElementById('journey-step-2');

      if (s1Icon) s1Icon.innerText = '✅';
      if (s1El) s1El.style.color = '#10b981';
      if (s2Icon) s2Icon.innerText = '⏳';
      if (s2El) s2El.style.color = '#fff';
      if (iconEl) iconEl.innerText = '🌐';
      if (subEl) subEl.innerText = 'Connecting with your community nodes... 🌐';
      if (barEl) barEl.style.width = '55%';

      await new Promise(r => setTimeout(r, 70));

      // Stage 3: Preparing workspace (fast 80ms step)
      const userRole = (authData.role || 'guest').toLowerCase();
      const displayName = authData.full_name || authData.username || 'Friend';
      
      const s3Icon = document.getElementById('journey-step-3-icon');
      const s3El = document.getElementById('journey-step-3');

      if (s2Icon) s2Icon.innerText = '✅';
      if (s2El) s2El.style.color = '#10b981';
      if (s3Icon) s3Icon.innerText = '⏳';
      if (s3El) s3El.style.color = '#fff';
      if (iconEl) iconEl.innerText = '✨';
      if (subEl) subEl.innerText = `Preparing your ${userRole} workspace... ✨`;
      if (barEl) barEl.style.width = '80%';

      await new Promise(r => setTimeout(r, 80));

      // Stage 4: Ready (snappy 120ms celebration)
      const s4Icon = document.getElementById('journey-step-4-icon');
      const s4El = document.getElementById('journey-step-4');
      const hlEl = document.getElementById('journey-headline');

      if (s3Icon) s3Icon.innerText = '✅';
      if (s3El) s3El.style.color = '#10b981';
      if (s4Icon) s4Icon.innerText = '🎉';
      if (s4El) s4El.style.color = '#38bdf8';
      if (iconEl) iconEl.innerText = '🚀';
      if (hlEl) hlEl.innerText = `Welcome, ${displayName}! 🎉`;
      if (subEl) subEl.innerText = "Everything is ready for you! ✨";
      if (barEl) barEl.style.width = '100%';

      await new Promise(r => setTimeout(r, 120));

      hideLoginOverlay();
      ensureModulesInitialized();
      switchView(state.activeView || 'dashboard');
      showSuccessToast(`Welcome back, ${displayName}! 🚀✨`, 4000);

      // Load subsystem data safely in background after overlay is dismissed
      setTimeout(() => {
        loadAllSubsystemData().catch(err => console.warn("Subsystem data sync error:", err));
      }, 50);

    } catch (err) {
      console.error("Post-login rendering exception caught safely:", err);
      hideLoginOverlay();
      switchView('dashboard');
    } finally {
      window._isAuthTransitioning = false;
      isAuthSubmitting = false;
      if (btnLogin) {
        btnLogin.disabled = false;
        btnLogin.innerHTML = `<span id="btn-login-text">Let's Go!</span> <span id="btn-login-rocket" style="display: inline-block; animation: rocketPulse 1.8s infinite ease-in-out; font-size: 1.2rem;">🚀✨</span>`;
      }
    }
  };
  window.executeLogin = executeLogin;

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

  // Keyboard Enter listener for instant submit across all authentication inputs
  ['login-username', 'login-password', 'login-mfa-token'].forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          e.stopPropagation();
          executeLogin();
        }
      });
    }
  });

  const btnLogout = document.getElementById('btn-logout');
  if (btnLogout) {
    btnLogout.addEventListener('click', (e) => {
      e.preventDefault();
      executeLogout();
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
    const headers = {};
    let sessToken = null;
    try {
      sessToken = sessionStorage.getItem("madn_session_token") || localStorage.getItem("madn_session_token");
    } catch (e) {}
    if (sessToken) {
      headers["X-Session-Token"] = sessToken;
      headers["Authorization"] = `Bearer ${sessToken}`;
    }

    const res = await fetch("/api/auth/session", {
      credentials: "include",
      headers: headers
    });
    if (res.ok) {
      const user = await res.json();
      state.user = user;
      state.currentRole = user.role;
      updateUserUI(user);
      hideLoginOverlay();
      switchView(state.activeView || 'dashboard');
      return user;
    } else {
      // Unauthenticated visitor
      document.body.classList.remove('authenticated');
      state.user = null;
      state.currentRole = 'guest';
      const authOverlay = document.getElementById('auth-overlay');
      const cardLogin = document.getElementById('card-login');
      if (authOverlay) authOverlay.style.display = 'flex';
      if (cardLogin) cardLogin.style.display = 'block';
      return null;
    }
  } catch (e) {
    return null;
  }
}

function showLoginOverlay(clearInputs = true) {
  document.body.classList.remove('authenticated');
  state.user = null;
  state.currentRole = 'guest';

  // Securely clear all input fields (passwords, usernames, OTP tokens) only if requested
  if (clearInputs) {
    const pwInput = document.getElementById('login-password');
    const userInput = document.getElementById('login-username');
    const totpInput = document.getElementById('login-totp');
    const regPw = document.getElementById('register-password');
    const regConfirm = document.getElementById('register-confirm');
    const regUser = document.getElementById('register-username');
    if (pwInput) pwInput.value = '';
    if (userInput) userInput.value = '';
    if (totpInput) totpInput.value = '';
    if (regPw) regPw.value = '';
    if (regConfirm) regConfirm.value = '';
    if (regUser) regUser.value = '';
  }

  const errBox = document.getElementById('login-error');
  const mfaGroup = document.getElementById('login-mfa-group');

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
  const cardJourney = document.getElementById('card-journey');
  const cardRegister = document.getElementById('card-register');
  const btnLogin = document.getElementById('btn-login-submit');
  const appContainer = document.getElementById('app-main-container') || document.querySelector('.app-container');

  document.body.classList.remove('authenticated');
  if (authOverlay) {
    authOverlay.classList.remove('hidden');
    authOverlay.style.setProperty('display', 'flex', 'important');
  }
  if (cardLogin) cardLogin.style.setProperty('display', 'block', 'important');
  if (cardJourney) cardJourney.style.setProperty('display', 'none', 'important');
  if (cardRegister) cardRegister.style.setProperty('display', 'none', 'important');
  if (appContainer) appContainer.style.setProperty('display', 'none', 'important');

  if (btnLogin) {
    btnLogin.disabled = false;
    btnLogin.innerHTML = `<span id="btn-login-text">Let's Go!</span> <span id="btn-login-rocket" style="display: inline-block; animation: rocketPulse 1.8s infinite ease-in-out; font-size: 1.2rem;">🚀✨</span>`;
  }

  hideModals();
}

function hideLoginOverlay() {
  document.body.classList.add('authenticated');
  const overlay = document.getElementById('auth-overlay');
  if (overlay) {
    overlay.classList.add('hidden');
    overlay.style.setProperty('display', 'none', 'important');
  }
  const appContainer = document.getElementById('app-main-container') || document.querySelector('.app-container');
  if (appContainer) {
    appContainer.style.setProperty('display', 'grid', 'important');
  }
}

function executeLogout() {
  try {
    sessionStorage.removeItem("madn_session_token");
    localStorage.removeItem("madn_session_token");
  } catch(e) {}
  showLoginOverlay(true);
  try {
    fetch("/api/auth/logout", { method: "POST", credentials: "include" }).catch(() => {});
  } catch (e) {}
}
window.executeLogout = executeLogout;
window.showLoginOverlay = showLoginOverlay;
window.hideLoginOverlay = hideLoginOverlay;

function updateUserUI(user) {
  if (!user) return;
  const profileUser = document.getElementById('profile-username');
  const profileRole = document.getElementById('profile-role');
  const avatarPic = document.getElementById('user-avatar-pic');
  const heroAvatar = document.getElementById('hero-operator-avatar');
  const heroName = document.getElementById('hero-header-operator-name');
  const heroRole = document.getElementById('hero-header-operator-role');
  const roleSelect = document.getElementById('role-switcher-select');
  const walletOwnerEl = document.getElementById('wallet-owner-name');
  const receiptOperatorEl = document.getElementById('receipt-operator');
  const visEscortEl = document.getElementById('vis-escort-officer');

  const displayName = user.full_name && user.full_name.trim() ? user.full_name.trim() : (user.username || 'Operator');
  const hasDistinctName = user.full_name && user.full_name.trim() && user.full_name.trim() !== user.username;

  // Sidebar User Drawer Name & Handle
  if (profileUser) {
    if (hasDistinctName) {
      profileUser.innerHTML = `${escapeHtml(user.full_name)} <span style="display: block; font-size: 0.72rem; color: var(--text-muted); font-weight: normal;">@${escapeHtml(user.username)}</span>`;
    } else {
      profileUser.innerText = user.username || 'Operator';
    }
  }

  // Hero Cover Header Title & Active Mesh Role
  if (heroName) {
    heroName.innerText = `MAD Node Hub • ${displayName}`;
  }
  if (heroRole) {
    heroRole.innerText = `Modular Adaptive Data Node • Primary Autonomous Mesh Vault #1 Active (${(user.role || 'operator').toUpperCase()})`;
  }

  // Sidebar Avatar with Organic Concentric Pattern
  if (avatarPic) {
    if (user.avatar_url && user.avatar_url.trim()) {
      avatarPic.style.backgroundImage = `url("${user.avatar_url}")`;
      avatarPic.style.backgroundSize = 'cover';
      avatarPic.style.backgroundPosition = 'center';
      avatarPic.innerHTML = '';
    } else {
      avatarPic.style.backgroundImage = 'none';
      avatarPic.innerHTML = displayName.charAt(0).toUpperCase();
    }
  }

  // Hero Header Avatar with Organic Concentric Pattern
  if (heroAvatar) {
    if (user.avatar_url && user.avatar_url.trim()) {
      heroAvatar.style.backgroundImage = `url("${user.avatar_url}")`;
      heroAvatar.style.backgroundSize = 'cover';
      heroAvatar.style.backgroundPosition = 'center';
      heroAvatar.innerHTML = '';
    } else {
      heroAvatar.style.backgroundImage = 'none';
      heroAvatar.innerHTML = displayName.charAt(0).toUpperCase();
    }
  }

  // Digital Banking Owner identity
  if (walletOwnerEl) {
    walletOwnerEl.innerText = `${displayName} (@${user.username})`;
  }

  // POS Cashier / Operator identity
  if (receiptOperatorEl) {
    receiptOperatorEl.innerText = `${displayName} (@${user.username})`;
  }

  // Gatekeeper Officer placeholder
  if (visEscortEl && !visEscortEl.value) {
    visEscortEl.placeholder = `e.g. Officer ${displayName}`;
  }

  // Profile modal preview sync if open
  renderProfileModalAvatarPreview(user.avatar_url, displayName);

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
    profileRole.innerText = (user.role || 'admin').toUpperCase();
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
  if (overlay) {
    overlay.style.display = 'none';
    overlay.querySelectorAll('.auth-card').forEach(el => {
      el.style.display = 'none';
    });
  }

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
    'modal-operator-profile',
    'modal-avatar-lightbox',
    'modal-avatar-uploader'
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
    state.pendingProfileAvatar = profile.avatar_url || state.user?.avatar_url || '';

    // Populate modal elements
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
    renderProfileModalAvatarPreview(state.pendingProfileAvatar, displayName);

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
    if (pinInput) pinInput.value = ''; // Clean blank state, preserves existing PIN unless changed

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

function renderProfileModalAvatarPreview(avatarUrl, fallbackName) {
  const avatarEl = document.getElementById('profile-modal-avatar');
  const viewBtn = document.getElementById('profile-avatar-view-btn');
  const removeBtn = document.getElementById('profile-avatar-remove-btn');
  if (!avatarEl) return;
  const name = fallbackName || document.getElementById('profile-input-fullname')?.value || document.getElementById('profile-input-username')?.value || 'A';
  
  const targetAvatar = avatarUrl !== undefined ? avatarUrl : (state.pendingProfileAvatar || state.user?.avatar_url || '');
  if (targetAvatar && targetAvatar.trim()) {
    avatarEl.style.backgroundImage = `url("${targetAvatar}")`;
    avatarEl.style.backgroundSize = 'cover';
    avatarEl.style.backgroundPosition = 'center';
    avatarEl.innerHTML = '';
    if (viewBtn) viewBtn.style.display = 'inline';
    if (removeBtn) removeBtn.style.display = 'inline';
  } else {
    avatarEl.style.backgroundImage = 'none';
    avatarEl.innerHTML = name.trim().charAt(0).toUpperCase() || 'A';
    if (viewBtn) viewBtn.style.display = 'none';
    if (removeBtn) removeBtn.style.display = 'none';
  }
}

function handleProfileModalAvatarClick() {
  const activeAvatar = state.pendingProfileAvatar || state.user?.avatar_url;
  if (activeAvatar && activeAvatar.trim()) {
    openAvatarLightbox(activeAvatar);
  } else {
    openAvatarStudioModal();
  }
}

function openAvatarLightbox(avatarUrl) {
  const targetUrl = avatarUrl || state.user?.avatar_url;
  const displayName = state.user?.full_name || state.user?.username || 'Operator';
  const roleName = (state.user?.role || 'OPERATOR').toUpperCase();

  const imgContainer = document.getElementById('lightbox-avatar-img-container');
  const nameEl = document.getElementById('lightbox-avatar-name');
  const roleEl = document.getElementById('lightbox-avatar-role');

  if (nameEl) nameEl.innerText = displayName;
  if (roleEl) roleEl.innerText = `${roleName} • SOVEREIGN IDENTITY`;

  if (imgContainer) {
    if (targetUrl && targetUrl.trim()) {
      imgContainer.style.backgroundImage = `url("${targetUrl}")`;
      imgContainer.style.backgroundSize = 'cover';
      imgContainer.style.backgroundPosition = 'center';
      imgContainer.innerHTML = '';
    } else {
      imgContainer.style.backgroundImage = 'none';
      imgContainer.innerHTML = displayName.charAt(0).toUpperCase();
    }
  }

  hideModals();
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('modal-avatar-lightbox');
  if (overlay) overlay.style.display = 'flex';
  if (modal) modal.style.display = 'block';
}

// --- DEDICATED AVATAR INGESTION & PROCESSING STUDIO ---
function openAvatarStudioModal() {
  hideModals();
  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('modal-avatar-uploader');
  const previewCore = document.getElementById('studio-avatar-preview-core');
  const progressContainer = document.getElementById('studio-progress-container');
  const metricsCard = document.getElementById('studio-metrics-card');
  const saveBtn = document.getElementById('studio-btn-save-avatar');
  const fileInput = document.getElementById('studio-avatar-file-input');

  if (fileInput) fileInput.value = '';
  if (progressContainer) progressContainer.style.display = 'none';
  if (metricsCard) metricsCard.style.display = 'none';
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerText = "Save & Set Profile Photo 💾";
  }

  // Reset steps
  ['studio-step-1', 'studio-step-2', 'studio-step-3', 'studio-step-4'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.className = 'step-badge';
  });

  const currentAvatar = state.pendingStudioAvatar || state.pendingProfileAvatar || state.user?.avatar_url;
  const displayName = state.user?.full_name || state.user?.username || 'Operator';
  if (previewCore) {
    if (currentAvatar && currentAvatar.trim()) {
      previewCore.style.backgroundImage = `url("${currentAvatar}")`;
      previewCore.style.backgroundSize = 'cover';
      previewCore.style.backgroundPosition = 'center';
      previewCore.innerHTML = '';
    } else {
      previewCore.style.backgroundImage = 'none';
      previewCore.innerHTML = displayName.charAt(0).toUpperCase();
    }
  }

  if (overlay) overlay.style.display = 'flex';
  if (modal) modal.style.display = 'block';

  initStudioDragAndDrop();
}

let studioDragDropInitialized = false;
function initStudioDragAndDrop() {
  if (studioDragDropInitialized) return;
  const dropzone = document.getElementById('avatar-studio-dropzone');
  if (!dropzone) return;

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      processStudioAvatarFile(files[0]);
    }
  }, false);

  studioDragDropInitialized = true;
}

function handleStudioAvatarFileSelected(event) {
  const input = event.target;
  if (input.files && input.files[0]) {
    processStudioAvatarFile(input.files[0]);
  }
}

async function processStudioAvatarFile(file) {
  if (!file) return;
  if (!file.type || !file.type.startsWith('image/')) {
    showErrorToast("Please select a valid image format (PNG, JPG, WebP, GIF).");
    return;
  }

  const progressContainer = document.getElementById('studio-progress-container');
  const progressBar = document.getElementById('studio-progress-bar');
  const progressStatus = document.getElementById('studio-progress-status');
  const progressPercent = document.getElementById('studio-progress-percent');
  const metricsCard = document.getElementById('studio-metrics-card');
  const origMetric = document.getElementById('studio-metric-orig-size');
  const optMetric = document.getElementById('studio-metric-opt-size');
  const saveBtn = document.getElementById('studio-btn-save-avatar');
  const previewCore = document.getElementById('studio-avatar-preview-core');

  if (progressContainer) progressContainer.style.display = 'block';
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerText = "Optimizing Image...";
  }

  const origSizeKB = (file.size / 1024).toFixed(1);
  if (origMetric) origMetric.innerText = `${origSizeKB} KB (${file.name})`;

  const setProgress = (percent, statusText, activeStepIdx) => {
    if (progressBar) progressBar.style.width = `${percent}%`;
    if (progressPercent) progressPercent.innerText = `${percent}%`;
    if (progressStatus) progressStatus.innerText = statusText;

    const stepIds = ['studio-step-1', 'studio-step-2', 'studio-step-3', 'studio-step-4'];
    stepIds.forEach((id, idx) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (idx < activeStepIdx) el.className = 'step-badge completed';
      else if (idx === activeStepIdx) el.className = 'step-badge active';
      else el.className = 'step-badge';
    });
  };

  // Instant 0ms Visual Preview using Blob Object URL
  if (previewCore) {
    try {
      const tempUrl = URL.createObjectURL(file);
      previewCore.style.backgroundImage = `url("${tempUrl}")`;
      previewCore.style.backgroundSize = 'cover';
      previewCore.style.backgroundPosition = 'center';
      previewCore.innerHTML = '';
    } catch (objUrlErr) {
      console.warn("createObjectURL notice:", objUrlErr);
    }
  }

  const finalizeImage = (dataUrl) => {
    state.pendingStudioAvatar = dataUrl;
    if (previewCore) {
      previewCore.style.backgroundImage = `url("${dataUrl}")`;
      previewCore.style.backgroundSize = 'cover';
      previewCore.style.backgroundPosition = 'center';
      previewCore.innerHTML = '';
    }

    const optBytes = Math.round((dataUrl.length * 3) / 4);
    const optKB = (optBytes / 1024).toFixed(1);
    const reduction = Math.max(0, Math.round(((file.size - optBytes) / file.size) * 100));

    if (optMetric) optMetric.innerText = `${optKB} KB (${reduction}% reduction)`;
    if (metricsCard) metricsCard.style.display = 'block';

    setProgress(100, "Image ready to save! ✨ Click 'Save & Set Profile Photo' below", 3);
    const step4 = document.getElementById('studio-step-4');
    if (step4) step4.className = 'step-badge completed';

    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerText = "Save & Set Profile Photo 💾";
      saveBtn.style.animation = "pulse 1.2s infinite";
    }
  };

  try {
    // Step 1: Read Buffer (Instant)
    setProgress(25, `Reading raw image buffer (${origSizeKB} KB)...`, 0);
    await new Promise(r => setTimeout(r, 10));

    // Step 2: Downscale using createImageBitmap (Hardware Accelerated)
    setProgress(55, "Hardware canvas scaling to 256x256...", 1);
    
    let sourceWidth, sourceHeight, drawSource;
    if (typeof window.createImageBitmap === 'function') {
      try {
        const bmp = await window.createImageBitmap(file);
        sourceWidth = bmp.width;
        sourceHeight = bmp.height;
        drawSource = bmp;
      } catch (bmpErr) {
        console.warn("createImageBitmap decode notice:", bmpErr);
      }
    }

    const canvas = document.createElement('canvas');
    const maxDim = 256;
    canvas.width = maxDim;
    canvas.height = maxDim;
    const ctx = canvas.getContext('2d');
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    if (drawSource) {
      const minEdge = Math.min(sourceWidth, sourceHeight);
      const sx = (sourceWidth - minEdge) / 2;
      const sy = (sourceHeight - minEdge) / 2;
      ctx.drawImage(drawSource, sx, sy, minEdge, minEdge, 0, 0, maxDim, maxDim);
      if (typeof drawSource.close === 'function') drawSource.close();
    } else {
      // Fallback via FileReader & Image
      const rawData = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = () => reject(new Error("File read error"));
        reader.readAsDataURL(file);
      });

      const img = await new Promise((resolve, reject) => {
        const i = new Image();
        i.onload = () => resolve(i);
        i.onerror = () => reject(new Error("Image decode error"));
        i.src = rawData;
      });

      const w = img.naturalWidth || img.width || 256;
      const h = img.naturalHeight || img.height || 256;
      const minEdge = Math.min(w, h);
      const sx = (w - minEdge) / 2;
      const sy = (h - minEdge) / 2;
      ctx.drawImage(img, sx, sy, minEdge, minEdge, 0, 0, maxDim, maxDim);
    }

    // Step 3: Compress
    setProgress(85, "Obsidian matrix color grading & compression...", 2);
    await new Promise(r => setTimeout(r, 10));

    let finalDataUrl = canvas.toDataURL('image/webp', 0.88);
    if (!finalDataUrl || finalDataUrl.length < 50) {
      finalDataUrl = canvas.toDataURL('image/jpeg', 0.88);
    }

    finalizeImage(finalDataUrl);
  } catch (err) {
    console.warn("Avatar pipeline fallback:", err);
    // Instant safety fallback: read raw as data URL
    const reader = new FileReader();
    reader.onload = (e) => finalizeImage(e.target.result);
    reader.onerror = () => {
      showErrorToast("Could not process image file.");
      setProgress(0, "Processing error", -1);
    };
    reader.readAsDataURL(file);
  }
}

async function submitStudioAvatarSave() {
  if (!state.pendingStudioAvatar) {
    showErrorToast("Please select an image first.");
    return;
  }

  const saveBtn = document.getElementById('studio-btn-save-avatar');
  const progressStatus = document.getElementById('studio-progress-status');
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerText = "Synchronizing Vault... ⏳";
    saveBtn.style.animation = "none";
  }
  if (progressStatus) {
    progressStatus.innerText = "Persisting avatar to local SQLite Vault...";
  }

  try {
    const payload = {
      username: state.user?.username || "",
      full_name: state.user?.full_name || "",
      phone: state.user?.phone || "",
      email: state.user?.email || "",
      avatar_url: state.pendingStudioAvatar
    };

    const res = await secureFetch("/api/user/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      showErrorToast(data.detail || "Failed to save avatar to vault.");
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerText = "Save & Set Profile Photo 💾";
      }
      return;
    }

    // Successfully saved!
    state.user.avatar_url = state.pendingStudioAvatar;
    state.pendingProfileAvatar = state.pendingStudioAvatar;
    updateUserUI(state.user);
    renderProfileModalAvatarPreview(state.pendingStudioAvatar);

    // Refresh all subsystem views with updated avatar
    loadSocialPosts();
    loadSocialStories();
    loadAdminUsers();
    loadCustomerWallet();

    // Visual Success Indication inside the Studio
    if (saveBtn) {
      saveBtn.innerText = "Saved & Synchronized! ✅";
      saveBtn.style.background = "#10b981";
      saveBtn.style.borderColor = "#10b981";
    }
    if (progressStatus) {
      progressStatus.innerText = "Profile picture active on Operator & Vault Nodes! ✨";
      progressStatus.style.color = "#10b981";
    }

    showSuccessToast("Profile picture saved and synchronized across all nodes! 📸✨");

    // Auto-close modal smoothly after brief confirmation
    setTimeout(() => {
      hideModals();
      if (saveBtn) {
        saveBtn.style.background = "";
        saveBtn.style.borderColor = "";
      }
    }, 600);
  } catch (err) {
    showErrorToast(err.message || "Network error saving avatar.");
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerText = "Save & Set Profile Photo 💾";
    }
  }
}

function removeProfileAvatar() {
  state.pendingProfileAvatar = "__REMOVED__";
  state.pendingStudioAvatar = "";
  renderProfileModalAvatarPreview("");
  showSuccessToast("Profile photo removed. Click 'Save Profile Settings' to save.");
}

async function submitSaveProfile() {
  const fnInput = document.getElementById('profile-input-fullname');
  const unInput = document.getElementById('profile-input-username');
  const phInput = document.getElementById('profile-input-phone');
  const emInput = document.getElementById('profile-input-email');
  const pinInput = document.getElementById('profile-input-pin');
  const saveBtn = document.getElementById('btn-save-profile-settings');

  const username = unInput ? unInput.value.trim() : "";
  if (!username || username.length < 3) {
    showErrorToast("Username must be at least 3 alphanumeric characters.");
    return;
  }

  const pin = pinInput ? pinInput.value.trim() : "";
  if (pin && (pin.length !== 4 || !/^\d{4}$/.test(pin))) {
    showErrorToast("Security PIN must be exactly 4 digits.");
    return;
  }

  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerText = "Saving Profile Settings... ⏳";
    saveBtn.style.animation = "none";
  }

  let activeAvatar = undefined;
  if (state.pendingProfileAvatar === "__REMOVED__") {
    activeAvatar = "";
  } else if (state.pendingProfileAvatar && state.pendingProfileAvatar.trim()) {
    activeAvatar = state.pendingProfileAvatar.trim();
  } else if (state.user?.avatar_url && state.user.avatar_url.trim()) {
    activeAvatar = state.user.avatar_url.trim();
  } else if (state.operatorProfile?.avatar_url && state.operatorProfile.avatar_url.trim()) {
    activeAvatar = state.operatorProfile.avatar_url.trim();
  }

  const payload = {
    full_name: fnInput ? fnInput.value.trim() : "",
    username: username,
    phone: phInput ? phInput.value.trim() : "",
    email: emInput ? emInput.value.trim() : ""
  };

  if (activeAvatar !== undefined) {
    payload.avatar_url = activeAvatar;
  }

  if (pin) {
    payload.pin = pin;
  }

  try {
    const res = await secureFetch("/api/user/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (!res.ok) {
      showErrorToast(data.detail || "Failed to update profile.");
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerText = "Save Profile Settings 💾";
      }
      return;
    }

    // In-place Visual Save Indication on Button
    if (saveBtn) {
      saveBtn.innerText = "Settings Saved Successfully! ✅";
      saveBtn.style.background = "#10b981";
      saveBtn.style.borderColor = "#10b981";
    }

    showSuccessToast("Operator profile settings saved and synchronized to Sovereign Vault! 💾✨");

    if (data.profile) {
      state.user.username = data.profile.username;
      state.user.full_name = data.profile.full_name;
      state.user.avatar_url = data.profile.avatar_url;
      state.user.phone = data.profile.phone;
      state.user.email = data.profile.email;
      updateUserUI(state.user);

      // Refresh all subsystem feeds with updated profile data
      loadSocialPosts();
      loadSocialStories();
      loadAdminUsers();
      loadCustomerWallet();
    }

    // Smoothly auto-dismiss after confirming
    setTimeout(() => {
      hideModals();
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.innerText = "Save Profile Settings 💾";
        saveBtn.style.background = "";
        saveBtn.style.borderColor = "";
      }
    }, 700);
  } catch (e) {
    showErrorToast(e.message || "Network error updating profile.");
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerText = "Save Profile Settings 💾";
    }
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
  if (curr) { curr.value = ''; curr.type = 'password'; }
  if (nw) { nw.value = ''; nw.type = 'password'; }

  // Reset toggle buttons to 👁️
  document.querySelectorAll('#modal-change-password .pw-toggle-btn').forEach(btn => {
    btn.innerHTML = '👁️';
    btn.title = 'View what you are typing';
  });

  // Reset live strength checker
  checkPasswordStrength('', 'change-pw');

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

// --- STATE EXTENSIONS FOR MODULAR STORE & MULTI-BUSINESS ---
state.selectedPosBusinessId = 'all';
state.activeBizFields = {
  branding: false,
  contact: false,
  tax: false,
  currency: false,
  web: false,
  hours: false,
  policy: false,
  receipt: false
};
state.pendingBizLogo = '';
state.pendingBizBanner = '';
state.isStoreSetupWorkspaceOpen = false;
state.businessAccounts = [];

// --- MULTI-BUSINESS & MODULAR STORE SETUP HANDLERS ---
async function loadBusinesses() {
  try {
    const res = await secureFetch("/api/businesses");
    if (!res.ok) return;
    const data = await res.json();
    state.businesses = data.businesses || [];

    const select = document.getElementById('header-business-select');
    const adminBizName = document.getElementById('admin-current-biz-name');
    const noStoreGate = document.getElementById('business-no-store-container');
    const launchpadMode = document.getElementById('business-launchpad-mode');
    const workspace = document.getElementById('business-setup-workspace-container');
    const titleText = document.getElementById('business-setup-title-text');
    const emptyPosBox = document.getElementById('pos-empty-store-container');
    const activePosBox = document.getElementById('pos-active-terminal-container');

    // Handle 0-Store Gatekeeper vs Active Store UI
    if (state.businesses.length === 0) {
      if (noStoreGate) {
        noStoreGate.style.display = 'block';
        if (state.isStoreSetupWorkspaceOpen) {
          if (launchpadMode) launchpadMode.style.display = 'none';
          if (workspace) workspace.style.display = 'block';
          if (titleText) titleText.innerText = 'Set Up Sovereign Business / Store';
        } else {
          if (launchpadMode) launchpadMode.style.display = 'block';
          if (workspace) workspace.style.display = 'none';
          if (titleText) titleText.innerText = 'Store Setup Launchpad';
        }
      }
      if (emptyPosBox) emptyPosBox.style.display = 'none';
      if (activePosBox) activePosBox.style.display = 'none';
      ['pos-terminal-box', 'biz-catalog-box', 'biz-marketplace-box', 'biz-inventory-box'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.style.display = 'none';
      });
      if (select) select.innerHTML = `<option value="">➕ Register Business</option>`;
      state.activeBusinessId = null;
      if (adminBizName) adminBizName.innerText = "No Registered Business";
    } else {
      state.isStoreSetupWorkspaceOpen = false;
      if (noStoreGate) noStoreGate.style.display = 'none';
      if (!state.activeBusinessId || !state.businesses.find(b => b.id === state.activeBusinessId)) {
        state.activeBusinessId = state.businesses[0].id;
      }

      if (select) {
        select.innerHTML = state.businesses.map(b => `
          <option value="${b.id}" ${b.id === state.activeBusinessId ? 'selected' : ''}>${b.name.length > 22 ? b.name.substring(0, 20) + '...' : b.name}</option>
        `).join('') + `<option value="__NEW__">➕ Register New Store...</option>`;
      }

      const activeBiz = state.businesses.find(b => b.id === state.activeBusinessId);
      if (adminBizName && activeBiz) {
        adminBizName.innerText = activeBiz.name;
      }
    }

    // Refresh dynamic subnav bar
    if (typeof updateSubNav === 'function' && state.activeView) {
      updateSubNav(state.activeView);
    }

    // Render POS Store Switcher Pills
    renderPosBusinessSwitcherPills();

    // Populate Analytics Store Dropdown
    const analyticsSelect = document.getElementById('biz-analytics-store-select');
    if (analyticsSelect) {
      const curVal = analyticsSelect.value || 'all';
      analyticsSelect.innerHTML = `<option value="all">🌐 All Businesses (Aggregated)</option>` +
        state.businesses.map(b => `<option value="${b.id}" ${b.id === curVal ? 'selected' : ''}>🏢 ${b.name}</option>`).join('');
    }

    // Refresh Analytics and Business Banking Accounts in background
    loadBusinessAnalytics(state.selectedPosBusinessId || 'all');
    loadBusinessBankingAccounts();
  } catch (e) {
    console.error("Failed to load businesses:", e);
  }
}

function renderPosBusinessSwitcherPills() {
  const container = document.getElementById('pos-business-switcher-pills');
  if (!container) return;

  const isAll = (state.selectedPosBusinessId === 'all');
  let html = `
    <button type="button" class="btn-pill-small ${isAll ? 'active' : ''}" onclick="switchPosBusinessFilter('all')" id="btn-biz-filter-all" style="${isAll ? 'background: var(--accent-cyan); color: #000; font-weight: 700;' : ''}">🌐 All Stores</button>
  `;

  state.businesses.forEach(b => {
    const isSelected = (state.selectedPosBusinessId === b.id);
    html += `
      <button type="button" class="btn-pill-small ${isSelected ? 'active' : ''}" onclick="switchPosBusinessFilter('${b.id}')" style="${isSelected ? 'background: #10b981; color: #fff; font-weight: 700;' : ''}">
        ${b.logo_url ? `<img src="${b.logo_url}" style="width: 14px; height: 14px; border-radius: 50%; vertical-align: middle; margin-right: 4px;" onerror="this.remove()">` : '🏢 '}
        ${b.name.length > 18 ? b.name.substring(0, 16) + '...' : b.name}
      </button>
    `;
  });

  container.innerHTML = html;
}

function switchPosBusinessFilter(bizId) {
  state.selectedPosBusinessId = bizId;
  renderPosBusinessSwitcherPills();
  
  const analyticsSelect = document.getElementById('biz-analytics-store-select');
  if (analyticsSelect) {
    analyticsSelect.value = bizId;
  }

  loadPosProducts();
  loadBusinessCatalog();
  loadBusinessAnalytics(bizId);
}

function handleLiveBusinessSwitch(bizId) {
  if (bizId === '__NEW__' || !bizId) {
    openCreateBusinessModal();
    return;
  }

  state.activeBusinessId = bizId;
  console.log(`[MADN] Active business switched to: ${bizId}`);
  
  const currentBiz = state.businesses.find(b => b.id === bizId);
  const nameEl = document.getElementById('admin-current-biz-name');
  if (nameEl && currentBiz) {
    nameEl.innerText = currentBiz.name;
  }

  loadPosProducts();
  loadBusinessCatalog();
  loadMarketplaceCatalog();
  loadPlantings();
  loadHarvests();
  loadBusinessOperators(bizId);
  loadBusinessBankingAccounts();
  loadBusinessAnalytics(bizId);
  updateUIPermissions();
}

async function quickStartPresetStore() {
  showSuccessToast("Launching Green Valley Farm & Market preset... 🏪🌱", 3000);
  try {
    const payload = {
      name: "Green Valley Farm & Market",
      category: "agriculture",
      settlement_currency: "USD",
      physical_address: "Plot 12, Umguza Valley, Bulawayo",
      phone: "+263 77 234 5678",
      tax_id: "ZW-8841-HORT",
      return_policy: "Fresh produce guaranteed. Returns accepted within 24 hours.",
      receipt_footer: "Sustainably grown with organic compost. Siyabonga!"
    };
    
    const res = await secureFetch("/api/businesses", {
      method: "POST",
      body: JSON.stringify(payload)
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Failed to create store preset");
    }
    
    const newBiz = await res.json();
    
    // Add sample fresh produce items to populate POS immediately!
    const sampleProducts = [
      { name: "Organic Roma Tomatoes", category: "Vegetables", price: 1.50, unit: "kg", stock_qty: 45, allow_decay: 1, decay_half_life_hours: 48, min_decay_price: 0.75, business_id: newBiz.id },
      { name: "Sweet White Maize (SC719)", category: "Grains", price: 0.80, unit: "kg", stock_qty: 120, allow_decay: 0, min_decay_price: 0.80, business_id: newBiz.id },
      { name: "Fresh Crisp Spinach", category: "Leafy Greens", price: 1.00, unit: "bundle", stock_qty: 30, allow_decay: 1, decay_half_life_hours: 24, min_decay_price: 0.50, business_id: newBiz.id }
    ];
    
    for (const prod of sampleProducts) {
      await secureFetch("/api/pos/products", {
        method: "POST",
        body: JSON.stringify(prod)
      }).catch(() => {});
    }
    
    state.isStoreSetupWorkspaceOpen = false;
    const workspace = document.getElementById('business-setup-workspace-container');
    const launchpad = document.getElementById('business-no-store-container');
    if (workspace) workspace.style.display = 'none';
    if (launchpad) launchpad.style.display = 'none';
    await loadBusinesses();
    switchBusiness(newBiz.id);
    showSuccessToast("Green Valley Farm Store is Live! POS register and fresh crops active 🏪🎉", 5000);
  } catch (err) {
    showErrorToast(err.message || "Failed to launch quick store preset");
  }
}
window.quickStartPresetStore = quickStartPresetStore;

const BIZ_INSPIRATION_PRESETS = [
  {
    sector: "⚡ Electronics, Hardware & Solar",
    category: "Hardware & Technology",
    name: "Apex Cybernetics & Solar Depot",
    tagline: "Off-grid solar inverters, smart sensors, and sovereign computing nodes",
    desc: "Decentralized computing hardware, high-efficiency solar battery packs, and electronics repair.",
    phone: "+263 77 456 7890",
    email: "orders@apexcyber.co.zw",
    address: "Shop 12, Cyber Hub Arcade, Bulawayo CBD",
    taxId: "ZW-2026-TECH-08",
    website: "https://apexcyber.co.zw",
    hours: "Mon - Fri: 08:30 - 17:30 | Sat: 09:00 - 14:00",
    policy: "1-year direct manufacturer warranty on all electronics.",
    header: "Apex Cybernetics & Solar",
    footer: "Powering sovereign communities with decentralized tech!"
  },
  {
    sector: "🥐 Bakery, Coffee & Specialty Food",
    category: "Bakery & Specialty Food",
    name: "Matopos Hearth Artisan Bakery & Deli",
    tagline: "Wood-fired stone-ground sourdough, pastries, and roasted local coffee",
    desc: "Organic sourdough breads, handcrafted pastries, and farm-to-table breakfast delicacies.",
    phone: "+263 71 888 2345",
    email: "hello@matoposhearth.co.zw",
    address: "45 Hillside Road, Bulawayo",
    taxId: "ZW-2026-BAKE-14",
    website: "https://matoposhearth.co.zw",
    hours: "Tue - Sun: 06:30 - 16:00 (Fresh batches daily)",
    policy: "100% freshly baked daily freshness replacement guarantee.",
    header: "Matopos Hearth Artisan Bakery",
    footer: "Siyabonga kakhulu! Taste the warmth of authentic tradition."
  },
  {
    sector: "🛒 Supermarket, Grocery & Wholesale",
    category: "Community Wholesale & Retail",
    name: "Sunrise Community Supermarket & Goods",
    tagline: "Wholesale grains, household goods, dairy, and essential family provisions",
    desc: "Affordable community supermarket offering groceries, fresh produce, and household supplies.",
    phone: "+263 77 654 3210",
    email: "sales@sunrisemart.co.zw",
    address: "Stand 102, Luveve Shopping Complex, Bulawayo",
    taxId: "ZW-2026-RET-31",
    website: "https://sunrisemart.co.zw",
    hours: "Mon - Sun: 07:00 - 20:00 (Open 7 Days)",
    policy: "Same-day replacement on unopened sealed goods with receipt.",
    header: "Sunrise Community Market",
    footer: "Thank you for shopping local with your community market!"
  },
  {
    sector: "👗 Apparel, Modern Fashion & Tailoring",
    category: "Fashion & Apparel",
    name: "Ubuntu Heritage Tailors & Urban Apparel",
    tagline: "Bespoke African modern textiles, tailored suits, and handcrafted streetwear",
    desc: "Handcrafted contemporary African fashion, custom tailored garments, and ethical cotton apparel.",
    phone: "+263 78 555 9012",
    email: "style@ubuntuheritage.zw",
    address: "Studio 4, Artisan Quarter, Jason Moyo St",
    taxId: "ZW-2026-FASH-22",
    website: "https://ubuntuheritage.zw",
    hours: "Mon - Sat: 09:00 - 18:00",
    policy: "7-day complimentary alteration and fitting exchange.",
    header: "Ubuntu Heritage Studio",
    footer: "Wear your sovereign heritage with pride!"
  },
  {
    sector: "🚗 Automotive, Solar Mobility & Fleet Care",
    category: "Automotive & Mobility",
    name: "Velocity EV & Mechanical Fleet Care",
    tagline: "Electric vehicle conversions, precision diagnostics, and fleet maintenance",
    desc: "Comprehensive diagnostics, solar mobility charging, and advanced hybrid vehicle repairs.",
    phone: "+263 77 333 4455",
    email: "service@velocityfleet.co.zw",
    address: "Stand 88, Belmont Industrial Zone, Bulawayo",
    taxId: "ZW-2026-AUTO-05",
    website: "https://velocityfleet.co.zw",
    hours: "Mon - Fri: 07:30 - 17:00 | Sat: 08:00 - 13:00",
    policy: "6-month or 10,000km mechanical workmanship guarantee.",
    header: "Velocity Fleet & EV Care",
    footer: "Driving sovereign zero-emission mobility into the future!"
  },
  {
    sector: "🎨 Creative Design, 3D & Spatial Media",
    category: "Creative & Digital Services",
    name: "Nexus Spatial Media & Design Agency",
    tagline: "3D architectural rendering, digital branding, and spatial media production",
    desc: "Full-service digital brand design, high-resolution rendering, and media production.",
    phone: "+263 71 999 1122",
    email: "contact@nexusspatial.io",
    address: "Level 3, Sovereign Tower, 8th Avenue",
    taxId: "ZW-2026-DES-19",
    website: "https://nexusspatial.io",
    hours: "Mon - Fri: 08:00 - 18:00",
    policy: "Milestone-based iterative satisfaction sign-off guarantee.",
    header: "Nexus Spatial Media Studio",
    footer: "Transforming visionary ideas into sovereign digital reality."
  },
  {
    sector: "🌾 Agriculture, Horticulture & Farm Direct",
    category: "Horticulture & Fresh Produce",
    name: "Umguza Valley Agro-Ecological Farm Depot",
    tagline: "Pure organic heirloom crops, honey, and cold-pressed sunflower oils",
    desc: "Regenerative farm produce, heirloom seeds, and fresh chemical-free horticulture.",
    phone: "+263 77 123 4567",
    email: "orders@umguzafarm.co.zw",
    address: "Plot 14, Umguza Valley, Matabeleland North",
    taxId: "ZW-2026-AGRI-01",
    website: "https://umguzafarm.co.zw",
    hours: "Mon - Sat: 07:00 - 17:30",
    policy: "24-hour freshness replacement guarantee.",
    header: "Umguza Farm Fresh Direct",
    footer: "Siyabonga! Supporting local regenerative farming."
  },
  {
    sector: "🌿 Health, Wellness & Herbal Apothecary",
    category: "Health & Natural Wellness",
    name: "Zenith Botanical Wellness & Apothecary",
    tagline: "Indigenous herbal remedies, organic wellness teas, and holistic consultations",
    desc: "Scientific and traditional botanical wellness products, herbal tinctures, and consultations.",
    phone: "+263 73 222 8899",
    email: "wellness@zenithbotanical.co.zw",
    address: "Suite 9, Ascot Wellness Centre, Bulawayo",
    taxId: "ZW-2026-HLTH-07",
    website: "https://zenithbotanical.co.zw",
    hours: "Mon - Fri: 08:30 - 17:00 | Sat: 09:00 - 13:00",
    policy: "14-day exchange on tamper-evident sealed botanical products.",
    header: "Zenith Botanical Wellness",
    footer: "Living in sovereign balance and vitality with nature."
  }
];

let _bizInspirationTimer = null;
let _bizInspirationIdx = 0;
let _isBizFormFocused = false;

function initStoreSetupInspirationTicker() {
  if (_bizInspirationTimer) {
    clearInterval(_bizInspirationTimer);
    _bizInspirationTimer = null;
  }
  
  const form = document.getElementById('form-create-business');
  if (!form) return;

  // Bind focus listeners to freeze when operator clicks into any field
  if (!form.dataset.inspireBound) {
    form.dataset.inspireBound = 'true';

    form.addEventListener('focusin', () => {
      _isBizFormFocused = true;
      const hint = document.getElementById('biz-inspiration-action-hint');
      if (hint) hint.innerText = 'Examples paused while editing';
    });

    form.addEventListener('focusout', () => {
      setTimeout(() => {
        const active = document.activeElement;
        if (!form.contains(active)) {
          _isBizFormFocused = false;
          const hint = document.getElementById('biz-inspiration-action-hint');
          if (hint) hint.innerText = 'Examples cycle live • Focus any field to freeze';
        }
      }, 250);
    });
  }

  function cycle() {
    if (_isBizFormFocused) return;
    const formEl = document.getElementById('form-create-business');
    if (!formEl || formEl.offsetParent === null) return;

    const preset = BIZ_INSPIRATION_PRESETS[_bizInspirationIdx % BIZ_INSPIRATION_PRESETS.length];
    _bizInspirationIdx++;

    const badge = document.getElementById('biz-inspiration-sector-badge');
    if (badge) {
      badge.style.opacity = '0.3';
      setTimeout(() => {
        badge.innerText = preset.sector;
        badge.style.opacity = '1';
      }, 150);
    }

    const fieldMap = {
      'new-biz-name': preset.name,
      'new-biz-tagline': preset.tagline,
      'new-biz-desc': preset.desc,
      'new-biz-phone': preset.phone,
      'new-biz-email': preset.email,
      'new-biz-address': preset.address,
      'new-biz-tax-id': preset.taxId,
      'new-biz-website': preset.website,
      'new-biz-hours': preset.hours,
      'new-biz-policy': preset.policy,
      'new-biz-header': preset.header,
      'new-biz-footer': preset.footer
    };

    Object.entries(fieldMap).forEach(([id, val]) => {
      const input = document.getElementById(id);
      if (input && document.activeElement !== input && (!input.value || input.value.trim() === '')) {
        input.placeholder = `e.g. ${val}`;
      }
    });
  }

  // Run initial cycle immediately and start interval
  cycle();
  _bizInspirationTimer = setInterval(cycle, 3500);
}
window.initStoreSetupInspirationTicker = initStoreSetupInspirationTicker;

function openCreateBusinessModal() {
  openCreateBusinessWorkspace();
}

async function openCreateBusinessWorkspace() {
  state.isStoreSetupWorkspaceOpen = true;

  if (state.activeView !== 'business') {
    if (typeof switchView === 'function') {
      await switchView('business');
    }
  }

  const gate = document.getElementById('business-no-store-container');
  const launchpadMode = document.getElementById('business-launchpad-mode');
  const workspace = document.getElementById('business-setup-workspace-container');
  const titleText = document.getElementById('business-setup-title-text');

  if (gate) {
    gate.style.display = 'block';
    gate.classList.remove('is-collapsed');
  }

  if (launchpadMode) {
    launchpadMode.style.display = 'none';
  }

  if (workspace) {
    workspace.style.display = 'block';
  }

  if (titleText) {
    titleText.innerText = 'Set Up Sovereign Business / Store';
  }

  // Reset modular fields
  state.activeBizFields = {
    branding: false,
    contact: false,
    tax: false,
    currency: false,
    web: false,
    hours: false,
    policy: false,
    receipt: false
  };
  Object.keys(state.activeBizFields).forEach(k => toggleBizField(k, false));

  state.pendingBizLogo = '';
  state.pendingBizBanner = '';
  clearBizLogo();
  clearBizBanner();

  // Trigger dynamic live inspiration ticker
  setTimeout(() => {
    initStoreSetupInspirationTicker();
  }, 50);
}

function cancelBusinessSetupWorkspace() {
  state.isStoreSetupWorkspaceOpen = false;
  if (_bizInspirationTimer) {
    clearInterval(_bizInspirationTimer);
    _bizInspirationTimer = null;
  }
  const launchpadMode = document.getElementById('business-launchpad-mode');
  const workspace = document.getElementById('business-setup-workspace-container');
  const titleText = document.getElementById('business-setup-title-text');
  const gate = document.getElementById('business-no-store-container');

  if (workspace) {
    workspace.style.display = 'none';
  }

  const numBusinesses = (state.businesses && state.businesses.length) || 0;
  if (numBusinesses === 0) {
    if (gate) {
      gate.style.display = 'block';
      gate.classList.remove('is-collapsed');
    }
    if (launchpadMode) {
      launchpadMode.style.display = 'block';
    }
    if (titleText) {
      titleText.innerText = 'Store Setup Launchpad';
    }
  } else {
    if (gate) gate.style.display = 'none';
    // Show active subview
    const currentSub = document.querySelector('.subnav-pill.active')?.dataset.subtarget || 'pos-terminal-box';
    if (typeof switchSubView === 'function') {
      switchSubView('business', currentSub);
    }
  }
}

window.openCreateBusinessModal = openCreateBusinessModal;
window.openCreateBusinessWorkspace = openCreateBusinessWorkspace;
window.cancelBusinessSetupWorkspace = cancelBusinessSetupWorkspace;

function toggleBizField(fieldKey, forceState) {
  const el = document.getElementById(`biz-field-${fieldKey}`);
  const pill = document.getElementById(`pill-biz-${fieldKey}`);
  if (!el) return;

  const willShow = forceState !== undefined ? forceState : el.style.display === 'none';
  el.style.display = willShow ? 'block' : 'none';
  state.activeBizFields[fieldKey] = willShow;

  if (pill) {
    if (willShow) {
      pill.style.background = 'rgba(16, 185, 129, 0.25)';
      pill.style.color = '#34d399';
      pill.style.borderColor = '#10b981';
    } else {
      pill.style.background = 'rgba(255, 255, 255, 0.06)';
      pill.style.color = '#fff';
      pill.style.borderColor = 'transparent';
    }
  }
}

function compressClientImage(file, maxWidth, maxHeight, quality, callback) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    const img = new Image();
    img.onload = function() {
      const canvas = document.createElement('canvas');
      let width = img.width;
      let height = img.height;

      if (width > maxWidth || height > maxHeight) {
        if (width / maxWidth > height / maxHeight) {
          height = Math.round((height * maxWidth) / width);
          width = maxWidth;
        } else {
          width = Math.round((width * maxHeight) / height);
          height = maxHeight;
        }
      }

      canvas.width = Math.max(1, width);
      canvas.height = Math.max(1, height);
      const ctx = canvas.getContext('2d');
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(img, 0, 0, width, height);
      const mime = file.type === 'image/png' ? 'image/png' : 'image/jpeg';
      const compressedDataUrl = canvas.toDataURL(mime, quality || 0.88);
      callback(compressedDataUrl);
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

function handleBizLogoUpload(inputEl) {
  if (!inputEl || !inputEl.files || !inputEl.files[0]) return;
  const file = inputEl.files[0];
  const reader = new FileReader();
  reader.onload = function(e) {
    const rawDataUrl = e.target.result;
    state.pendingBizLogo = rawDataUrl;
    const urlInput = document.getElementById('new-biz-logo-url');
    if (urlInput) urlInput.value = rawDataUrl;
    const previewImg = document.getElementById('new-biz-logo-img');
    const placeholder = document.getElementById('new-biz-logo-placeholder');
    const clearBtn = document.getElementById('btn-clear-logo');
    if (previewImg) {
      previewImg.src = rawDataUrl;
      previewImg.style.display = 'block';
    }
    if (placeholder) placeholder.style.display = 'none';
    if (clearBtn) clearBtn.style.display = 'inline-block';

    // Compress in background for lightweight database payload
    compressClientImage(file, 256, 256, 0.88, function(compressedUrl) {
      if (compressedUrl) {
        state.pendingBizLogo = compressedUrl;
        if (urlInput) urlInput.value = compressedUrl;
      }
    });
  };
  reader.readAsDataURL(file);
}
window.handleBizLogoUpload = handleBizLogoUpload;

function clearBizLogo() {
  state.pendingBizLogo = '';
  const fileInput = document.getElementById('new-biz-logo-file');
  if (fileInput) fileInput.value = '';
  const urlInput = document.getElementById('new-biz-logo-url');
  if (urlInput) urlInput.value = '';
  const previewImg = document.getElementById('new-biz-logo-img');
  const placeholder = document.getElementById('new-biz-logo-placeholder');
  const clearBtn = document.getElementById('btn-clear-logo');
  if (previewImg) {
    previewImg.src = '';
    previewImg.style.display = 'none';
  }
  if (placeholder) placeholder.style.display = 'flex';
  if (clearBtn) clearBtn.style.display = 'none';
}
window.clearBizLogo = clearBizLogo;

function handleBizLogoUrlInput(url) {
  const clean = (url || '').trim();
  state.pendingBizLogo = clean;
  const previewImg = document.getElementById('new-biz-logo-img');
  const placeholder = document.getElementById('new-biz-logo-placeholder');
  const clearBtn = document.getElementById('btn-clear-logo');
  if (clean) {
    if (previewImg) {
      previewImg.src = clean;
      previewImg.style.display = 'block';
    }
    if (placeholder) placeholder.style.display = 'none';
    if (clearBtn) clearBtn.style.display = 'inline-block';
  } else {
    clearBizLogo();
  }
}
window.handleBizLogoUrlInput = handleBizLogoUrlInput;

function handleBizBannerUpload(inputEl) {
  if (!inputEl || !inputEl.files || !inputEl.files[0]) return;
  const file = inputEl.files[0];
  const reader = new FileReader();
  reader.onload = function(e) {
    const rawDataUrl = e.target.result;
    state.pendingBizBanner = rawDataUrl;
    const urlInput = document.getElementById('new-biz-banner-url');
    if (urlInput) urlInput.value = rawDataUrl;
    const pillFrame = document.getElementById('new-biz-banner-pill-frame');
    const previewImg = document.getElementById('new-biz-banner-img');
    const placeholder = document.getElementById('new-biz-banner-placeholder');
    const clearBtn = document.getElementById('btn-clear-banner');
    if (pillFrame) pillFrame.style.display = 'block';
    if (previewImg) {
      previewImg.src = rawDataUrl;
      previewImg.style.display = 'block';
    }
    if (placeholder) placeholder.style.display = 'none';
    if (clearBtn) clearBtn.style.display = 'inline-block';

    // Compress in background for lightweight database payload with flexible aspect ratio (up to 1600x900)
    compressClientImage(file, 1600, 900, 0.88, function(compressedUrl) {
      if (compressedUrl) {
        state.pendingBizBanner = compressedUrl;
        if (urlInput) urlInput.value = compressedUrl;
      }
    });
  };
  reader.readAsDataURL(file);
}
window.handleBizBannerUpload = handleBizBannerUpload;

function clearBizBanner() {
  state.pendingBizBanner = '';
  const fileInput = document.getElementById('new-biz-banner-file');
  if (fileInput) fileInput.value = '';
  const urlInput = document.getElementById('new-biz-banner-url');
  if (urlInput) urlInput.value = '';
  const pillFrame = document.getElementById('new-biz-banner-pill-frame');
  const previewImg = document.getElementById('new-biz-banner-img');
  const placeholder = document.getElementById('new-biz-banner-placeholder');
  const clearBtn = document.getElementById('btn-clear-banner');
  if (pillFrame) pillFrame.style.display = 'none';
  if (previewImg) {
    previewImg.src = '';
    previewImg.style.display = 'none';
  }
  if (placeholder) placeholder.style.display = 'flex';
  if (clearBtn) clearBtn.style.display = 'none';
}
window.clearBizBanner = clearBizBanner;

function handleBizBannerUrlInput(url) {
  const clean = (url || '').trim();
  state.pendingBizBanner = clean;
  const pillFrame = document.getElementById('new-biz-banner-pill-frame');
  const previewImg = document.getElementById('new-biz-banner-img');
  const placeholder = document.getElementById('new-biz-banner-placeholder');
  const clearBtn = document.getElementById('btn-clear-banner');
  if (clean) {
    if (pillFrame) pillFrame.style.display = 'block';
    if (previewImg) {
      previewImg.src = clean;
      previewImg.style.display = 'block';
    }
    if (placeholder) placeholder.style.display = 'none';
    if (clearBtn) clearBtn.style.display = 'inline-block';
  } else {
    clearBizBanner();
  }
}
window.handleBizBannerUrlInput = handleBizBannerUrlInput;

async function submitCreateBusiness() {
  const name = (document.getElementById('new-biz-name')?.value || '').trim();
  const tagline = (document.getElementById('new-biz-tagline')?.value || '').trim();
  const desc = (document.getElementById('new-biz-desc')?.value || '').trim();

  if (!name) {
    showErrorToast("Please enter a Business / Store Name.");
    return;
  }
  if (!tagline) {
    showErrorToast("Please enter a Brief Tagline for your store.");
    return;
  }

  // Gather optional modular fields
  const category = document.getElementById('new-biz-category')?.value || 'General Retail & Wholesale';
  const currency = document.getElementById('new-biz-currency')?.value || 'USD';
  const phone = (document.getElementById('new-biz-phone')?.value || '').trim();
  const email = (document.getElementById('new-biz-email')?.value || '').trim();
  const taxId = (document.getElementById('new-biz-tax-id')?.value || '').trim();
  const address = (document.getElementById('new-biz-address')?.value || '').trim();
  const website = (document.getElementById('new-biz-website')?.value || '').trim();
  const hours = (document.getElementById('new-biz-hours')?.value || '').trim();
  const policy = (document.getElementById('new-biz-policy')?.value || '').trim();
  const header = (document.getElementById('new-biz-header')?.value || '').trim();
  const footer = (document.getElementById('new-biz-footer')?.value || '').trim();

  const logoUrl = state.pendingBizLogo || (document.getElementById('new-biz-logo-url')?.value || '').trim();
  const bannerUrl = state.pendingBizBanner || (document.getElementById('new-biz-banner-url')?.value || '').trim();

  const payload = {
    name: name,
    tagline: tagline,
    description: desc,
    category: category,
    currency_preference: currency,
    logo_url: logoUrl,
    banner_url: bannerUrl,
    contact_phone: phone,
    contact_email: email,
    location_address: address,
    tax_id: taxId,
    website_url: website,
    operating_hours: hours,
    return_policy: policy,
    receipt_header: header,
    receipt_footer_note: footer
  };

  try {
    const res = await secureFetch("/api/businesses", {
      method: "POST",
      body: JSON.stringify(payload)
    });

    const text = await res.text();
    let data = {};
    try {
      data = JSON.parse(text);
    } catch (parseErr) {
      data = { detail: text || `HTTP ${res.status} ${res.statusText}` };
    }

    if (res.ok) {
      state.isStoreSetupWorkspaceOpen = false;
      hideModals();
      const workspace = document.getElementById('business-setup-workspace-container');
      const launchpad = document.getElementById('business-no-store-container');
      if (workspace) workspace.style.display = 'none';
      if (launchpad) launchpad.style.display = 'none';
      document.getElementById('form-inline-create-business')?.reset();
      document.getElementById('form-create-business')?.reset();
      await loadBusinesses();
      if (data.business && data.business.id) {
        handleLiveBusinessSwitch(data.business.id);
      }
      showSuccessToast(`Store "${name}" created with dedicated Banking Settlement Account! 🏪🎉`, 5000);
    } else {
      showErrorToast("Failed to create store: " + (data.detail || "Unknown error"));
    }
  } catch (e) {
    showErrorToast("Network error creating store: " + (e.message || "Connection failed"));
  }
}

// --- MULTI-STORE ANALYTICS HANDLERS ---
async function loadBusinessAnalytics(bizId = 'all') {
  try {
    const res = await secureFetch(`/api/businesses/analytics?business_id=${bizId}&time_range=30d`);
    if (!res.ok) return;
    const data = await res.json();
    const a = data.analytics || {};

    const revEl = document.getElementById('biz-kpi-revenue');
    const cogsEl = document.getElementById('biz-kpi-cogs');
    const marginEl = document.getElementById('biz-kpi-margin');
    const ordersEl = document.getElementById('biz-kpi-orders');
    const unitsEl = document.getElementById('biz-kpi-units');

    if (revEl) revEl.innerText = `$${(a.gross_revenue_usd || 0).toFixed(2)}`;
    if (cogsEl) cogsEl.innerText = `$${(a.total_cogs_usd || 0).toFixed(2)}`;
    if (marginEl) {
      const margin = a.gross_margin_pct || 0;
      marginEl.innerText = `${margin.toFixed(1)}%`;
      marginEl.style.color = margin >= 0 ? '#34d399' : '#f87171';
    }
    if (ordersEl) ordersEl.innerText = `${a.transactions_count || 0} orders`;
    if (unitsEl) unitsEl.innerText = `${a.units_sold_total || 0} units sold (${a.top_selling_items?.length || 0} unique items)`;

    // Render hourly sales chart onto canvas
    drawHourlySalesChart(a.hourly_sales_distribution || []);
  } catch (e) {
    console.error("Failed to load business analytics:", e);
  }
}

function drawHourlySalesChart(hourlyData) {
  const canvas = document.getElementById('sales-chart-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  // Background
  ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
  ctx.fillRect(0, 0, w, h);

  // Grid lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  for (let y = 20; y < h; y += 35) {
    ctx.beginPath();
    ctx.moveTo(30, y);
    ctx.lineTo(w - 10, y);
    ctx.stroke();
  }

  // Draw 24h bar graph
  const barWidth = (w - 50) / 24;
  const maxVal = Math.max(...hourlyData.map(d => d.amount_usd || 0), 10);

  hourlyData.forEach((d, i) => {
    const val = d.amount_usd || 0;
    const barHeight = (val / maxVal) * (h - 50);
    const x = 35 + i * barWidth;
    const y = h - 25 - barHeight;

    // Gradient bar
    const grad = ctx.createLinearGradient(0, y, 0, h - 25);
    grad.addColorStop(0, '#00e5ff');
    grad.addColorStop(1, 'rgba(0, 229, 255, 0.1)');
    ctx.fillStyle = grad;
    ctx.fillRect(x + 2, y, barWidth - 4, barHeight);

    // X Axis hour label every 4 hours
    if (i % 4 === 0) {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.font = '9px monospace';
      ctx.fillText(`${i}:00`, x, h - 8);
    }
  });
}

// --- ENTERPRISE BUSINESS BANKING ACCOUNTS ---
async function loadBusinessBankingAccounts() {
  const grid = document.getElementById('business-accounts-grid');
  if (!grid) return;

  try {
    const res = await secureFetch("/api/banking/business-accounts");
    if (!res.ok) return;
    const data = await res.json();
    state.businessAccounts = data.accounts || [];

    if (state.businessAccounts.length === 0) {
      grid.innerHTML = `
        <div class="glass-panel" style="grid-column: 1 / -1; padding: 28px; text-align: center; background: rgba(255,255,255,0.02);">
          <div style="font-size: 2.2rem; margin-bottom: 8px;">🏢</div>
          <h4 style="color: #fff; margin-bottom: 4px;">No Business Settlement Accounts</h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 14px;">Establish a store to automatically generate its dedicated multi-currency settlement wallet.</p>
          <button class="btn-pill-primary" onclick="openCreateBusinessModal()">+ Register Store Profile</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = state.businessAccounts.map(acc => {
      const balances = acc.balances || {};
      const currencies = Object.keys(balances);

      return `
        <div class="glass-panel" style="padding: 20px; border-radius: 18px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
              <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(0,229,255,0.1); border: 1px solid rgba(0,229,255,0.3); overflow: hidden; display: flex; align-items: center; justify-content: center; font-size: 1.4rem;">
                ${acc.business_logo ? `<img src="${acc.business_logo}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.parentElement.innerHTML='🏢'">` : '🏢'}
              </div>
              <div>
                <h4 style="margin: 0; font-size: 1.05rem; color: #fff;">${acc.business_name}</h4>
                <div style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">Account: <span style="color: var(--accent-cyan); font-weight: 700;">${acc.account_number}</span></div>
              </div>
            </div>

            ${acc.business_tagline ? `<p style="font-size: 0.8rem; color: var(--text-muted); margin: 0 0 14px 0; font-style: italic;">"${acc.business_tagline}"</p>` : ''}

            <div style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; font-weight: 700; margin-bottom: 8px;">Settlement Balances</div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; margin-bottom: 16px;">
              ${currencies.map(c => `
                <div style="background: rgba(0,0,0,0.25); padding: 8px 10px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);">
                  <div style="font-size: 0.68rem; color: var(--text-muted);">${c}</div>
                  <div style="font-size: 0.95rem; font-weight: 700; color: #fff; font-family: var(--font-display);">${(balances[c] || 0).toFixed(2)}</div>
                </div>
              `).join('')}
            </div>
          </div>

          <div style="display: flex; gap: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px;">
            <button class="btn-pill-small" style="flex-grow: 1; background: rgba(16,185,129,0.15); color: #34d399;" onclick="openTopupModal()">➕ Deposit Funds</button>
            <button class="btn-pill-small" style="flex-grow: 1; background: rgba(56,189,248,0.15); color: #38bdf8;" onclick="switchPosBusinessFilter('${acc.business_id}')">View Analytics 📊</button>
          </div>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error("Failed to load business banking accounts:", e);
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
    showErrorToast("Please select an operator username.");
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
      showSuccessToast(`Operator @${username} granted ${role} access with permissions: ${perms.join(', ')}`);
      hideModals();
      loadBusinessOperators();
    } else {
      showErrorToast("Failed to assign operator: " + (data.detail || "Error occurred"));
    }
  } catch (e) {
    showErrorToast("Assignment error: " + e.message);
  }
}

async function revokeOperator(username) {
  try {
    const res = await secureFetch(`/api/businesses/${state.activeBusinessId}/operators/${username}`, {
      method: "DELETE"
    });

    if (res.ok) {
      showSuccessToast(`Access revoked for @${username}`);
      loadBusinessOperators();
    } else {
      const data = await res.json();
      showErrorToast("Revocation failed: " + (data.detail || "Error"));
    }
  } catch (e) {
    showErrorToast("Revocation error: " + e.message);
  }
}

// --- ADMIN USER & GLOBAL PRIVILEGE MANAGEMENT ---
let currentAdminUsersTab = 'active';

function switchAdminUsersTab(tab) {
  currentAdminUsersTab = tab;
  const activeView = document.getElementById('admin-users-active-view');
  const recycleView = document.getElementById('admin-users-recycle-view');
  const tabBtnActive = document.getElementById('tab-btn-users-active');
  const tabBtnRecycle = document.getElementById('tab-btn-users-recycle');

  if (tab === 'active') {
    if (activeView) activeView.style.display = 'grid';
    if (recycleView) recycleView.style.display = 'none';
    if (tabBtnActive) {
      tabBtnActive.style.background = 'linear-gradient(135deg, var(--accent-cyan), #0284c7)';
      tabBtnActive.style.color = '#000';
    }
    if (tabBtnRecycle) {
      tabBtnRecycle.style.background = 'rgba(255,255,255,0.06)';
      tabBtnRecycle.style.color = 'var(--text-muted)';
    }
    loadAdminUsers();
  } else {
    if (activeView) activeView.style.display = 'none';
    if (recycleView) recycleView.style.display = 'block';
    if (tabBtnRecycle) {
      tabBtnRecycle.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
      tabBtnRecycle.style.color = '#fff';
    }
    if (tabBtnActive) {
      tabBtnActive.style.background = 'rgba(255,255,255,0.06)';
      tabBtnActive.style.color = 'var(--text-muted)';
    }
    loadAdminRecycleBin();
  }
}

async function loadAdminUsers() {
  const tbody = document.getElementById('admin-users-table-body');
  const countBadge = document.getElementById('count-active-users');
  if (!tbody) return;

  try {
    const res = await secureFetch("/api/admin/users");
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 16px;">User directory restricted to Administrators.</td></tr>`;
      return;
    }

    const users = await res.json();
    const userList = Array.isArray(users) ? users : [];
    if (countBadge) countBadge.innerText = userList.length;

    if (userList.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 16px;">No active operators found.</td></tr>`;
      return;
    }

    tbody.innerHTML = userList.map(u => {
      const isSelf = (state.user && state.user.username === u.username);
      const isStatusActive = (u.status === 'active');
      const hasAvatar = u.avatar_url && u.avatar_url.trim();
      const displayName = u.full_name ? u.full_name : u.username;

      return `
        <tr>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="width: 28px; height: 28px; border-radius: 50%; ${hasAvatar ? `background-image: url('${u.avatar_url}'); background-size: cover; background-position: center; border: 1.5px solid var(--accent-cyan);` : 'background: rgba(255,255,255,0.08); font-size: 0.75rem; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fff;'} flex-shrink: 0;">
                ${hasAvatar ? '' : displayName.charAt(0).toUpperCase()}
              </div>
              <div>
                <strong style="color: #fff; display: block; font-size: 0.88rem;">${escapeHtml(displayName)}</strong>
                <span style="color: var(--accent-cyan); font-size: 0.74rem;">@${escapeHtml(u.username)}</span>
                ${isSelf ? '<span style="color: #10b981; font-size: 0.7rem; font-weight: 700; margin-left: 4px;">(You)</span>' : ''}
              </div>
            </div>
          </td>
          <td><span class="role-pill-badge">${u.role.toUpperCase()}</span></td>
          <td>
            <span style="display: inline-block; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700; background: ${isStatusActive ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}; color: ${isStatusActive ? '#10b981' : '#f87171'};">
              ${u.status.toUpperCase()}
            </span>
          </td>
          <td style="text-align: center;">
            <button class="btn-pill-small" onclick='openConfigureUserModal(${JSON.stringify(u)})'>⚙️ Configure</button>
          </td>
        </tr>
      `;
    }).join('');

    loadAdminRecycleBinCount();
  } catch (e) {
    console.error("Error loading admin users:", e);
  }
}

async function loadAdminRecycleBinCount() {
  try {
    const res = await secureFetch("/api/admin/users/recycle-bin");
    if (res.ok) {
      const items = await res.json();
      const countEl = document.getElementById('count-recycle-users');
      if (countEl) countEl.innerText = Array.isArray(items) ? items.length : 0;
    }
  } catch (e) {}
}

async function loadAdminRecycleBin() {
  const tbody = document.getElementById('admin-recycle-table-body');
  const countBadge = document.getElementById('count-recycle-users');
  if (!tbody) return;

  try {
    const res = await secureFetch("/api/admin/users/recycle-bin");
    if (!res.ok) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 16px;">Restricted to Administrators.</td></tr>`;
      return;
    }

    const items = await res.json();
    const list = Array.isArray(items) ? items : [];
    if (countBadge) countBadge.innerText = list.length;

    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">Recycle Bin is empty 🗑️ (No deleted accounts).</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(u => {
      const deletedDateStr = u.deleted_at ? new Date(u.deleted_at * 1000).toLocaleString() : 'Recently';
      const hasAvatar = u.avatar_url && u.avatar_url.trim();
      const displayName = u.full_name ? u.full_name : u.username;

      return `
        <tr>
          <td>
            <div style="display: flex; align-items: center; gap: 8px;">
              <div style="width: 28px; height: 28px; border-radius: 50%; ${hasAvatar ? `background-image: url('${u.avatar_url}'); background-size: cover; background-position: center; border: 1.5px solid #ef4444;` : 'background: rgba(239,68,68,0.15); font-size: 0.75rem; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #fca5a5;'} flex-shrink: 0;">
                ${hasAvatar ? '' : displayName.charAt(0).toUpperCase()}
              </div>
              <div>
                <strong style="color: #fca5a5; display: block; font-size: 0.88rem; text-decoration: line-through;">${escapeHtml(displayName)}</strong>
                <span style="color: var(--text-muted); font-size: 0.74rem;">@${escapeHtml(u.username)}</span>
              </div>
            </div>
          </td>
          <td><span class="role-pill-badge" style="border-color: rgba(239,68,68,0.4); color: #fca5a5;">${u.role.toUpperCase()}</span></td>
          <td><small style="color: var(--text-muted);">${deletedDateStr}</small></td>
          <td><span style="color: var(--accent-cyan); font-size: 0.8rem;">${escapeHtml(u.deleted_by || 'Admin')}</span></td>
          <td style="text-align: center;">
            <div style="display: inline-flex; gap: 6px;">
              <button class="btn-pill-small" style="background: rgba(16, 185, 129, 0.2); border: 1px solid #10b981; color: #6ee7b7;" onclick="restoreUserFromRecycleBin(${u.id}, '${escapeHtml(u.username)}')">♻️ Restore</button>
              <button class="btn-pill-small btn-pill-danger" onclick="permanentlyDeleteUser(${u.id}, '${escapeHtml(u.username)}')">❌ Purge</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    console.error("Error loading recycle bin:", e);
  }
}

function openConfigureUserModal(user) {
  const modal = document.getElementById('modal-configure-user');
  const overlay = document.getElementById('modal-overlay');
  if (!modal || !overlay) return;

  hideModals();

  document.getElementById('config-user-id').value = user.id;
  document.getElementById('config-user-role').value = user.role || 'guest';
  document.getElementById('config-user-status').value = user.status || 'active';
  document.getElementById('config-user-title').innerText = `Configure @${user.username}`;
  document.getElementById('config-user-sub').innerText = user.full_name ? `${user.full_name} (#${user.id})` : `Operator ID #${user.id}`;

  const badgeEl = document.getElementById('config-user-avatar-badge');
  if (badgeEl) {
    if (user.avatar_url && user.avatar_url.trim()) {
      badgeEl.style.backgroundImage = `url('${user.avatar_url}')`;
      badgeEl.style.backgroundSize = 'cover';
      badgeEl.style.backgroundPosition = 'center';
      badgeEl.innerText = '';
    } else {
      badgeEl.style.backgroundImage = 'none';
      badgeEl.innerText = (user.full_name || user.username || 'U').charAt(0).toUpperCase();
    }
  }

  overlay.style.display = 'flex';
  modal.style.display = 'block';
}

async function submitSaveUserConfig() {
  const userId = document.getElementById('config-user-id').value;
  const role = document.getElementById('config-user-role').value;
  const status = document.getElementById('config-user-status').value;

  try {
    const roleRes = await secureFetch(`/api/admin/users/${userId}/role`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role })
    });
    if (!roleRes.ok) {
      const d = await roleRes.json().catch(() => ({}));
      showErrorToast(d.detail || "Failed to update role.");
      return;
    }

    const statusRes = await secureFetch(`/api/admin/users/${userId}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    if (!statusRes.ok) {
      const d = await statusRes.json().catch(() => ({}));
      showErrorToast(d.detail || "Failed to update status.");
      return;
    }

    showSuccessToast("Operator configuration updated successfully! 💾");
    hideModals();
    loadAdminUsers();
  } catch (e) {
    showErrorToast(e.message);
  }
}

async function submitMoveUserToRecycleBin() {
  const userId = document.getElementById('config-user-id').value;
  if (!confirm("Are you sure you want to move this operator to the Recycle Bin? Their active sessions will be revoked, but you can restore the account at any time.")) {
    return;
  }

  try {
    const res = await secureFetch(`/api/admin/users/${userId}`, {
      method: "DELETE"
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      showErrorToast(d.detail || "Failed to delete user.");
      return;
    }

    showSuccessToast("Account moved to Recycle Bin 🗑️ (Soft Deleted)");
    hideModals();
    loadAdminUsers();
    loadAdminRecycleBinCount();
  } catch (e) {
    showErrorToast(e.message);
  }
}

async function restoreUserFromRecycleBin(userId, username) {
  try {
    const res = await secureFetch(`/api/admin/users/${userId}/restore`, {
      method: "POST"
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      showErrorToast(d.detail || "Failed to restore user.");
      return;
    }

    showSuccessToast(`Operator @${username} restored to Active Roster! ♻️`);
    loadAdminRecycleBin();
    loadAdminUsers();
  } catch (e) {
    showErrorToast(e.message);
  }
}

async function permanentlyDeleteUser(userId, username) {
  if (!confirm(`⚠️ PERMANENT DESTRUCTION WARNING: Are you sure you want to permanently erase operator @${username}? All cascaded wallets and history will be purged. This action CANNOT be undone.`)) {
    return;
  }

  try {
    const res = await secureFetch(`/api/admin/users/${userId}/permanent`, {
      method: "DELETE"
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      showErrorToast(d.detail || "Failed to permanently purge user.");
      return;
    }

    showSuccessToast(`Operator @${username} permanently purged from system. ❌`);
    loadAdminRecycleBin();
    loadAdminUsers();
  } catch (e) {
    showErrorToast(e.message);
  }
}

async function submitResetUserPassword() {
  const userId = document.getElementById('config-user-id').value;
  try {
    const res = await secureFetch(`/api/admin/users/${userId}/reset-password`, {
      method: "PUT"
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      showErrorToast(d.detail || "Failed to reset password.");
      return;
    }

    alert(`🔑 Temporary Password Generated:\n\n${d.temp_password}\n\nPlease share this one-time passphrase securely with the operator. They will be required to change it on next login.`);
  } catch (e) {
    showErrorToast(e.message);
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

// --- COMPONENT TEMPLATE CACHE & DYNAMIC MOUNTING ENGINE ---
const templateCache = {};

async function preloadAllViewTemplates() {
  const views = ['dashboard', 'business', 'banking', 'agriculture', 'security', 'social', 'cluster', 'admin', 'tutorials'];
  for (const v of views) {
    if (!templateCache[v]) {
      fetch(`./components/${v}.html?v=20260831_0953`)
        .then(r => r.ok ? r.text() : '')
        .then(html => { if (html) templateCache[v] = html; })
        .catch(() => {});
    }
  }
}

async function loadComponentView(target) {
  const viewport = document.getElementById('app-viewport');
  if (!viewport) return;

  // 1. Fetch template if not in cache
  if (!templateCache[target]) {
    try {
      const res = await fetch(`./components/${target}.html?v=20260831_0953`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      templateCache[target] = await res.text();
    } catch (err) {
      console.error(`Failed to load component ${target}:`, err);
      viewport.innerHTML = `<div class="glass-panel" style="padding: 28px; text-align: center;">
        <p style="color: var(--danger); margin-bottom: 12px;">Failed to load view component.</p>
        <button class="btn-pill-primary" onclick="switchView('${target}')">Retry</button>
      </div>`;
      return;
    }
  }

  // 2. Mount template directly into viewport
  viewport.innerHTML = templateCache[target];

  // 3. Make sure the mounted section is visible
  const sec = viewport.querySelector('.view-section');
  if (sec) {
    sec.classList.add('active');
    sec.style.display = 'block';
  }

  // 4. Update contextual subnav pills
  if (typeof updateSubNav === 'function') {
    updateSubNav(target);
  }

  // 5. Trigger view-specific data loading asynchronously in parallel
  if (target === 'agriculture') {
    Promise.all([loadAgriFields(), loadPlantings(), loadHarvests(), loadDispositions()]).catch(() => {});
  } else if (target === 'business') {
    Promise.all([loadBusinesses(), loadPosProducts(), loadMarketplaceCatalog()]).catch(() => {});
    setTimeout(() => {
      initStoreSetupInspirationTicker();
    }, 100);
  } else if (target === 'admin') {
    Promise.all([loadCurrencies(), loadAdminUsers(), loadBusinessOperators()]).catch(() => {});
  } else if (target === 'banking') {
    Promise.all([loadCurrencies(), loadCustomerWallet(), loadCustomerReceipts(), loadWalletLedger()]).catch(() => {});
  } else if (target === 'cluster') {
    Promise.all([loadDiscoveredClusterNodes(), loadExportedNodePackages()]).catch(() => {});
  } else if (target === 'security') {
    loadActiveVisitors();
  } else if (target === 'social') {
    Promise.all([loadSocialStories(), loadSocialPosts()]).catch(() => {});
  }

  // 6. Non-blocking LaTeX math rendering
  setTimeout(() => {
    renderLatexInUI();
  }, 40);
}

function switchView(target, subtarget) {
  state.activeView = target;

  // Highlight active nav buttons
  document.querySelectorAll('.nav-item-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.target === target);
  });
  document.querySelectorAll('.mobile-nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.target === target);
  });

  // Mount component view dynamically
  loadComponentView(target).then(() => {
    if (subtarget && typeof switchSubView === 'function') {
      switchSubView(target, subtarget);
    }
  });
}
window.switchView = switchView;
window.switchViewInternal = switchView;
window.loadComponentView = loadComponentView;
window.preloadAllViewTemplates = preloadAllViewTemplates;

function initNavigation() {
  preloadAllViewTemplates();

  // Bind sidebar nav clicks
  document.querySelectorAll('.nav-item-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.target;
      if (target) switchView(target);
    });
  });
  // Bind mobile bottom nav clicks
  document.querySelectorAll('.mobile-nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const target = item.dataset.target;
      if (target) switchView(target);
    });
  });
}

function handleQuickCTA() {
  if (state.currentRole === 'agronomist') {
    switchView('agriculture');
    togglePlantingForm();
  } else if (state.currentRole === 'guard') {
    switchView('security');
  } else if (state.currentRole === 'merchant') {
    switchView('business');
  } else if (state.currentRole === 'customer') {
    switchView('banking');
    openTopupModal();
  } else {
    openCreatePostModal('thread');
  }
}

async function loadAllSubsystemData() {
  await Promise.all([
    loadBusinesses(),
    loadCustomerWallet(),
    loadCurrencies()
  ]).catch(() => {});

  updateDashboardLiveFeeds();

  // On-demand load strictly for current active view
  const currentView = state.activeView || 'dashboard';
  if (currentView === 'business') {
    loadPosProducts();
    loadMarketplaceCatalog();
  } else if (currentView === 'agriculture') {
    loadAgriFields();
    loadPlantings();
  } else if (currentView === 'banking') {
    loadCustomerReceipts();
    loadWalletLedger();
  } else if (currentView === 'security') {
    loadActiveVisitors();
  } else if (currentView === 'social') {
    loadSocialStories();
    loadSocialPosts();
  } else if (currentView === 'cluster') {
    loadDiscoveredClusterNodes();
    loadExportedNodePackages();
  } else if (currentView === 'admin' && state.currentRole === 'admin') {
    loadAdminUsers();
    loadAdminDevices();
  }
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
// STAGE 1 CORE: AGRICULTURE MODULE & FIELD MANAGEMENT
// =====================================================================
function initAgriModule() {
  const btnAgriCalc = document.getElementById('btn-calculate-agri');
  if (btnAgriCalc) {
    btnAgriCalc.addEventListener('click', calculateBulawayoSchedule);
  }
}

function toggleFieldForm() {
  const form = document.getElementById('new-field-form-container');
  if (form) {
    form.style.display = (form.style.display === 'none' || !form.style.display) ? 'block' : 'none';
  }
}

async function loadAgriFields() {
  try {
    const res = await secureFetch("/api/agri/fields");
    if (!res.ok) return;
    const data = await res.json();
    state.agriFields = data.fields || [];
    state.fields = state.agriFields;

    if (typeof updateSubNav === 'function' && state.activeView === 'agriculture') {
      const activeBtn = document.getElementById('subnav-pill-bar')?.querySelector('.tab-pill-btn.active');
      const preferredSubId = activeBtn ? activeBtn.getAttribute('onclick')?.match(/'([^']+)'\s*,\s*this/)?.[1] : null;
      updateSubNav('agriculture', preferredSubId);
    }

    const tbody = document.getElementById('agri-fields-table-body');
    const fieldSelect = document.getElementById('planting-field-select');
    const warningBox = document.getElementById('planting-no-fields-warning');

    if (warningBox) {
      warningBox.style.display = state.agriFields.length === 0 ? 'block' : 'none';
    }

    if (tbody) {
      if (state.agriFields.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No farm fields registered yet. Click <strong style="color: #00e5ff;">"+ Add Farm Field"</strong> above to define your first plot.</td></tr>`;
      } else {
        tbody.innerHTML = state.agriFields.map(f => `
          <tr>
            <td><code style="color: var(--accent-cyan); font-weight: 700;">${f.id}</code></td>
            <td><strong>${f.name}</strong></td>
            <td><span style="font-family: monospace; color: var(--text-muted);">${f.code || 'N/A'}</span></td>
            <td><strong>${f.area_size} ${f.area_unit}</strong></td>
            <td>${f.soil_type || 'Loamy'}</td>
            <td>${f.irrigation_type || 'Drip'}</td>
            <td><span style="padding: 2px 8px; border-radius: 9999px; background: rgba(16, 185, 129, 0.2); color: #10b981; font-size: 0.75rem; font-weight: 700;">${(f.status || 'active').toUpperCase()}</span></td>
            <td>
              <button class="btn-pill-small" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3);" onclick="deleteField('${f.id}')">Delete 🗑️</button>
            </td>
          </tr>
        `).join('');
      }
    }

    if (fieldSelect) {
      if (state.agriFields.length === 0) {
        fieldSelect.innerHTML = `<option value="">-- No fields available. Click "+ New Field" first --</option>`;
      } else {
        fieldSelect.innerHTML = `
          <option value="">-- Select a registered farm field --</option>
          ${state.agriFields.map(f => `
            <option value="${f.id}" data-name="${f.name}" data-area="${f.area_size}" data-unit="${f.area_unit}">
              ${f.name} (${f.area_size} ${f.area_unit} • ${f.soil_type})
            </option>
          `).join('')}
        `;
      }
    }
  } catch (e) {
    console.error("Failed to load agricultural fields:", e);
  }
}

async function submitNewField() {
  const name = document.getElementById('field-name-input').value.trim();
  const code = document.getElementById('field-code-input').value.trim();
  const size = parseFloat(document.getElementById('field-area-size-input').value || "1.0");
  const unit = document.getElementById('field-area-unit-input').value;
  const soil = document.getElementById('field-soil-type-input').value;
  const irrig = document.getElementById('field-irrigation-input').value;
  const notes = document.getElementById('field-notes-input').value.trim();

  if (!name) {
    alert("Field name is required.");
    return;
  }

  try {
    const res = await secureFetch("/api/agri/fields", {
      method: "POST",
      body: JSON.stringify({
        name: name,
        code: code,
        area_size: size,
        area_unit: unit,
        soil_type: soil,
        irrigation_type: irrig,
        notes: notes
      })
    });

    if (res.ok) {
      toggleFieldForm();
      document.getElementById('field-name-input').value = "";
      document.getElementById('field-code-input').value = "";
      document.getElementById('field-notes-input').value = "";
      await loadAgriFields();
      alert(`Farm field "${name}" registered and synchronized to Data Node storage!`);
    } else {
      const err = await res.json();
      alert("Failed to save field: " + (err.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Error registering field: " + e.message);
  }
}

async function deleteField(fieldId) {
  if (!confirm("Are you sure you want to delete this farm field?")) return;
  try {
    const res = await secureFetch(`/api/agri/fields/${fieldId}`, { method: "DELETE" });
    if (res.ok) {
      loadAgriFields();
    }
  } catch (e) {
    alert("Failed to delete field: " + e.message);
  }
}

function onPlantingFieldSelected() {
  const select = document.getElementById('planting-field-select');
  if (!select) return;
  const opt = select.selectedOptions[0];
  if (opt && opt.dataset.area) {
    const areaInput = document.getElementById('planting-area-utilized');
    const unitInput = document.getElementById('planting-area-unit');
    if (areaInput) areaInput.value = opt.dataset.area;
    if (unitInput && opt.dataset.unit) unitInput.value = opt.dataset.unit;
  }
}

function togglePlantingForm() {
  const form = document.getElementById('new-planting-form-container');
  if (form) {
    const isShowing = form.style.display === 'block';
    form.style.display = isShowing ? 'none' : 'block';
    if (!isShowing) {
      const dInput = document.getElementById('planting-date-input');
      if (dInput && !dInput.value) {
        dInput.value = new Date().toISOString().substring(0, 10);
      }
    }
  }
}

async function loadPlantings() {
  try {
    const res = await secureFetch("/api/agri/plantings");
    if (!res.ok) return;
    const data = await res.json();
    state.plantings = data.plantings || [];
    updateDashboardLiveFeeds();

    if (typeof updateSubNav === 'function' && state.activeView === 'agriculture') {
      const activeBtn = document.getElementById('subnav-pill-bar')?.querySelector('.tab-pill-btn.active');
      const preferredSubId = activeBtn ? activeBtn.getAttribute('onclick')?.match(/'([^']+)'\s*,\s*this/)?.[1] : null;
      updateSubNav('agriculture', preferredSubId);
    }

    const dashPlantings = document.getElementById('dash-plantings-count');
    if (dashPlantings) {
      dashPlantings.innerText = `● ${state.plantings.length} Active Plantings`;
    }

    const tbody = document.getElementById('agri-plantings-table-body');
    const harvestSelect = document.getElementById('harvest-planting-select');
    const costSelect = document.getElementById('calc-planting-select');

    if (tbody) {
      if (state.plantings.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted); padding: 24px;">No active crop plantings found. Select a field and click <strong style="color: #10b981;">"+ New Planting Plan"</strong> above.</td></tr>`;
      } else {
        tbody.innerHTML = state.plantings.map(p => `
          <tr>
            <td><strong style="font-family: monospace; color: var(--accent-cyan);">${p.id}</strong></td>
            <td><strong style="color: #fff;">${p.field_name || p.plot_bed_id || 'Main Field'}</strong></td>
            <td><strong>${p.crop_variety}</strong></td>
            <td>${p.planting_date_utc ? p.planting_date_utc.substring(0, 10) : 'N/A'}</td>
            <td>${p.target_maturity_date_utc ? p.target_maturity_date_utc.substring(0, 10) : 'Approx. 90d'}</td>
            <td>${p.area_utilized || 1.0} ${p.area_unit || 'ha'}</td>
            <td><span style="padding: 2px 8px; border-radius: 9999px; background: rgba(16, 185, 129, 0.2); color: #10b981; font-size: 0.75rem; font-weight: 700;">${(p.status || 'growing').toUpperCase()}</span></td>
            <td>
              <div style="display: flex; gap: 6px;">
                <button class="btn-pill-small" onclick="selectPlantingForCostCalc('${p.id}', '${p.crop_variety}', '${p.field_name || p.plot_bed_id}')">Costs 💰</button>
                <button class="btn-pill-small" onclick="selectPlantingForHarvest('${p.id}', '${p.crop_variety}')">Harvest 🚜</button>
              </div>
            </td>
          </tr>
        `).join('');
      }
    }

    const plantingOptions = state.plantings.length === 0 
      ? `<option value="">-- No active plantings available --</option>`
      : `
        <option value="">-- Select an active crop planting --</option>
        ${state.plantings.map(p => `
          <option value="${p.id}" data-crop="${p.crop_variety}" data-field="${p.field_name || p.plot_bed_id}">
            ${p.crop_variety} in ${p.field_name || p.plot_bed_id} (${p.planting_date_utc ? p.planting_date_utc.substring(0, 10) : 'Active'})
          </option>
        `).join('')}
      `;

    if (harvestSelect) harvestSelect.innerHTML = plantingOptions;
    if (costSelect) costSelect.innerHTML = plantingOptions;
  } catch (e) {
    console.error("Failed to load plantings:", e);
  }
}

async function submitNewPlanting() {
  const fieldSelect = document.getElementById('planting-field-select');
  const fieldId = fieldSelect ? fieldSelect.value : "";
  const opt = fieldSelect ? fieldSelect.selectedOptions[0] : null;
  const fieldName = opt ? (opt.dataset.name || opt.text) : "";
  const crop = document.getElementById('planting-crop-variety').value.trim();
  const area = parseFloat(document.getElementById('planting-area-utilized').value || "1.0");
  const unit = document.getElementById('planting-area-unit').value;
  const date = document.getElementById('planting-date-input').value;
  const maturityDate = document.getElementById('planting-maturity-date-input').value;
  const density = parseFloat(document.getElementById('planting-seeding-density').value || "0");
  const hydration = parseFloat(document.getElementById('planting-soil-hydration').value || "0");
  const notes = document.getElementById('planting-notes').value.trim();

  if (!fieldId) {
    alert("Please select a registered Farm Field / Plot for this planting.");
    return;
  }

  if (!crop) {
    alert("Please enter the Crop Variety (e.g. White Maize SC719, Roma Tomatoes).");
    return;
  }

  try {
    const res = await secureFetch("/api/agri/plantings", {
      method: "POST",
      body: JSON.stringify({
        field_id: fieldId,
        field_name: fieldName,
        plot_bed_id: fieldName,
        crop_variety: crop,
        area_utilized: area,
        area_unit: unit,
        planting_date_utc: date,
        target_maturity_date_utc: maturityDate,
        seeding_density: density,
        initial_soil_hydration_pct: hydration,
        notes: notes
      })
    });

    if (res.ok) {
      togglePlantingForm();
      document.getElementById('planting-crop-variety').value = "";
      document.getElementById('planting-notes').value = "";
      loadPlantings();
      alert(`Crop planting for "${crop}" in field "${fieldName}" registered and synced to Data Node!`);
    } else {
      const err = await res.json();
      alert("Failed to create planting: " + (err.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Failed to create planting: " + e.message);
  }
}

function selectPlantingForCostCalc(plantingId, cropName, fieldName) {
  switchView('agriculture');
  const costBox = document.getElementById('agri-cost-calc-box');
  if (costBox) costBox.scrollIntoView({ behavior: 'smooth' });
  const select = document.getElementById('calc-planting-select');
  if (select) select.value = plantingId;
  onSelectPlantingForCosts();
}

function onSelectPlantingForCosts() {
  const select = document.getElementById('calc-planting-select');
  if (!select) return;
  const opt = select.selectedOptions[0];
  if (opt && opt.dataset.crop) {
    recalculateCosts();
  }
}

async function submitProductionCosts() {
  const select = document.getElementById('calc-planting-select');
  const plantingId = select ? select.value : "";
  if (!plantingId) {
    alert("Please select a Field Crop Planting before saving expenses.");
    return;
  }

  const cSeeds = parseFloat(document.getElementById('calc-cost-seeds').value || "0");
  const cFert = parseFloat(document.getElementById('calc-cost-fert').value || "0");
  const cWater = parseFloat(document.getElementById('calc-cost-water').value || "0");
  const cLabor = parseFloat(document.getElementById('calc-cost-labor').value || "0");
  const cPest = parseFloat(document.getElementById('calc-cost-pest').value || "0");
  const cPack = parseFloat(document.getElementById('calc-cost-pack').value || "0");
  const cLog = parseFloat(document.getElementById('calc-cost-log').value || "0");
  const cOver = parseFloat(document.getElementById('calc-cost-over').value || "0");

  try {
    const res = await secureFetch("/api/agri/costs", {
      method: "POST",
      body: JSON.stringify({
        planting_id: plantingId,
        costs: {
          seeds: cSeeds,
          fertilizer: cFert,
          water: cWater,
          labor: cLabor,
          pest: cPest,
          packaging: cPack,
          logistics: cLog,
          overhead: cOver
        }
      })
    });

    if (res.ok) {
      alert("Production expenses saved and synchronized with Data Node!");
    } else {
      const err = await res.json();
      alert("Failed to save costs: " + (err.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Error logging production costs: " + e.message);
  }
}

function selectPlantingForHarvest(plantingId, cropName) {
  switchView('agriculture');
  const harvestBox = document.getElementById('agri-harvest-box');
  if (harvestBox) harvestBox.scrollIntoView({ behavior: 'smooth' });
  const select = document.getElementById('harvest-planting-select');
  if (select) select.value = plantingId;
  const nameInput = document.getElementById('harvest-crop-name');
  if (nameInput) nameInput.value = cropName;
}

function onSelectPlantingForHarvest() {
  const select = document.getElementById('harvest-planting-select');
  if (!select) return;
  const opt = select.selectedOptions[0];
  if (opt && opt.dataset.crop) {
    const nameInput = document.getElementById('harvest-crop-name');
    if (nameInput) nameInput.value = opt.dataset.crop;
  }
}

async function submitHarvest() {
  const pId = document.getElementById('harvest-planting-select').value;
  const crop = document.getElementById('harvest-crop-name').value.trim();
  const mHarvest = parseFloat(document.getElementById('harvest-total-mass').value || "0");
  const mSelf = parseFloat(document.getElementById('harvest-self-mass').value || "0");
  const grade = document.getElementById('harvest-quality-grade').value;
  const halfLife = parseFloat(document.getElementById('harvest-half-life').value || "2.5");

  if (!pId || !crop || mHarvest <= 0) {
    alert("Please select a crop planting and enter valid harvest yield weight.");
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
      alert(`Harvest logged successfully! Commercial batch synchronized to POS store catalog and Data Node storage.`);
      loadPlantings();
      loadHarvests();
      loadDispositions();
      loadPosProducts();
      loadMarketplaceCatalog();
    } else {
      const err = await res.json();
      alert("Harvest logging failed: " + (err.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Harvest logging failed: " + e.message);
  }
}

function openAddStoreProductModal() {
  if (!state.businesses || state.businesses.length === 0) {
    alert("Store setup required. Please establish a business store first before adding products.");
    openCreateBusinessModal();
    return;
  }

  const overlay = document.getElementById('modal-overlay');
  const modal = document.getElementById('modal-add-store-product');
  if (overlay && modal) {
    document.querySelectorAll('.auth-card').forEach(m => m.style.display = 'none');
    overlay.style.display = 'flex';
    modal.style.display = 'block';

    // Populate business store select
    const bizSelect = document.getElementById('store-product-business-select');
    if (bizSelect) {
      bizSelect.innerHTML = state.businesses.map(b => `
        <option value="${b.id}" ${b.id === state.selectedPosBusinessId || b.id === state.activeBusinessId ? 'selected' : ''}>${b.name}</option>
      `).join('');
    }

    updateSystemSkuPreview();
  }
}

function updateSystemSkuPreview() {
  const nameInput = document.getElementById('store-product-name-input');
  const catInput = document.getElementById('store-product-category-input');
  const badge = document.getElementById('product-sku-badge');
  if (!nameInput || !badge) return;

  const rawName = nameInput.value.trim().replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
  const rawCat = catInput ? catInput.value.trim().replace(/[^a-zA-Z0-9]/g, '').toUpperCase() : '';
  
  if (!rawName) {
    badge.innerText = 'SKU: AUTO-ASSIGNED';
    return;
  }
  
  const prefix = rawName.substring(0, 4);
  const catTag = rawCat ? `-${rawCat.substring(0, 3)}` : '';
  badge.innerText = `SKU: ${prefix}${catTag}-AUTO`;
}

function toggleProductField(fieldKey, forceState) {
  const el = document.getElementById(`mod-field-${fieldKey}`);
  const pill = document.getElementById(`pill-field-${fieldKey}`);
  if (!el) return;

  const willShow = forceState !== undefined ? forceState : el.style.display === 'none';
  el.style.display = willShow ? 'block' : 'none';

  if (pill) {
    if (willShow) {
      pill.style.background = 'rgba(0, 229, 255, 0.2)';
      pill.style.color = 'var(--accent-cyan)';
      pill.style.borderColor = 'var(--accent-cyan)';
    } else {
      pill.style.background = 'rgba(255, 255, 255, 0.06)';
      pill.style.color = '#fff';
      pill.style.borderColor = 'transparent';
    }
  }
}

function handleProductImageUpload(inputEl) {
  if (!inputEl || !inputEl.files || !inputEl.files[0]) return;
  const file = inputEl.files[0];
  const reader = new FileReader();
  reader.onload = function(e) {
    const dataUrl = e.target.result;
    state.pendingProductImage = dataUrl;
    const previewWrap = document.getElementById('store-product-image-preview-wrap');
    if (previewWrap) {
      previewWrap.innerHTML = `<img src="${dataUrl}" style="width: 100%; height: 100%; object-fit: cover;" alt="Product preview">`;
    }
  };
  reader.readAsDataURL(file);
}

function handleProductImageUrlInput(url) {
  const cleanUrl = (url || '').trim();
  state.pendingProductImage = cleanUrl;
  const previewWrap = document.getElementById('store-product-image-preview-wrap');
  if (previewWrap) {
    if (cleanUrl) {
      previewWrap.innerHTML = `<img src="${cleanUrl}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.parentElement.innerHTML='⚠️'" alt="Product preview">`;
    } else {
      previewWrap.innerHTML = `<span style="font-size: 1.2rem; color: var(--text-muted);">📷</span>`;
    }
  }
}

function generateRandomBarcode() {
  const prefix = "600"; // Southern African EAN prefix standard
  const randomDigits = Math.floor(1000000000 + Math.random() * 9000000000).toString();
  const barcode = prefix + randomDigits;
  const input = document.getElementById('store-product-barcode-input');
  if (input) {
    input.value = barcode;
    toggleProductField('barcode', true);
  }
}

function applyCategoryPreset(category, subcategory) {
  const catInput = document.getElementById('store-product-category-input');
  const subInput = document.getElementById('store-product-subcategory-input');
  if (catInput) catInput.value = category;
  if (subInput) subInput.value = subcategory;
  toggleProductField('category', true);
  updateCatBreadcrumb();
  updateSystemSkuPreview();
}

function updateCatBreadcrumb() {
  const cat = (document.getElementById('store-product-category-input')?.value || '').trim();
  const sub = (document.getElementById('store-product-subcategory-input')?.value || '').trim();
  const breadcrumb = document.getElementById('store-product-cat-breadcrumb');
  if (!breadcrumb) return;

  if (cat && sub) {
    breadcrumb.innerHTML = `Hierarchy: <span style="color:#fff;">${cat}</span> &gt; <span style="color:var(--accent-cyan); font-weight:700;">${sub}</span>`;
  } else if (cat) {
    breadcrumb.innerHTML = `Hierarchy: <span style="color:var(--accent-cyan); font-weight:700;">${cat}</span>`;
  } else {
    breadcrumb.innerHTML = '';
  }
}

function addProductSpecRow(key = '', val = '') {
  const container = document.getElementById('store-product-specs-rows');
  if (!container) return;
  const rowId = `spec-row-${Date.now()}-${Math.floor(Math.random()*1000)}`;
  const row = document.createElement('div');
  row.id = rowId;
  row.style.display = 'flex';
  row.style.gap = '8px';
  row.style.alignItems = 'center';
  row.innerHTML = `
    <input type="text" class="search-input spec-key-input" style="flex: 1; padding: 6px 10px; font-size: 0.75rem; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 9999px;" placeholder="Spec (e.g. Dimensions, Expiry, Voltage)" value="${key}">
    <input type="text" class="search-input spec-val-input" style="flex: 1; padding: 6px 10px; font-size: 0.75rem; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 9999px;" placeholder="Value (e.g. 500ml, 220V, 100m)" value="${val}">
    <button type="button" style="background: none; border: none; color: #ff5252; cursor: pointer; font-size: 0.8rem; padding: 4px 6px;" onclick="this.parentElement.remove()">✕</button>
  `;
  container.appendChild(row);
  toggleProductField('specs', true);
}

async function submitAddStoreProduct() {
  const bizId = document.getElementById('store-product-business-select')?.value || state.activeBusinessId || (state.businesses[0] ? state.businesses[0].id : '');
  const name = document.getElementById('store-product-name-input').value.trim();
  const cost = parseFloat(document.getElementById('store-product-cost-input').value || "0");
  const price = parseFloat(document.getElementById('store-product-price-input').value || "0");
  const qty = parseFloat(document.getElementById('store-product-qty-input').value || "0");
  const unit = document.getElementById('store-product-unit-input').value;
  
  // Optional modular fields
  const barcode = (document.getElementById('store-product-barcode-input')?.value || '').trim();
  const category = (document.getElementById('store-product-category-input')?.value || '').trim();
  const subcategory = (document.getElementById('store-product-subcategory-input')?.value || '').trim();
  const brand = (document.getElementById('store-product-brand-input')?.value || '').trim();
  const desc = (document.getElementById('store-product-desc-input')?.value || '').trim();
  const threshold = parseFloat(document.getElementById('store-product-threshold-input')?.value || "5");
  const wholesalePrice = parseFloat(document.getElementById('store-product-wholesale-price')?.value || "0");
  const wholesaleQty = parseFloat(document.getElementById('store-product-wholesale-qty')?.value || "0");
  const imageUrl = state.pendingProductImage || (document.getElementById('store-product-image-url')?.value || '').trim();

  // Collect specs key-values
  const specifications = {};
  document.querySelectorAll('#store-product-specs-rows > div').forEach(row => {
    const k = row.querySelector('.spec-key-input')?.value.trim();
    const v = row.querySelector('.spec-val-input')?.value.trim();
    if (k && v) specifications[k] = v;
  });

  if (!name) {
    alert("Product Item Name / Title is required.");
    return;
  }

  if (isNaN(cost) || cost < 0) {
    alert("Please provide a valid Cost Price (Purchase Cost) for COGS calculation.");
    return;
  }

  if (isNaN(price) || price <= 0) {
    alert("Selling price (Retail Price) must be greater than 0.");
    return;
  }

  try {
    const res = await secureFetch("/api/inventory", {
      method: "POST",
      body: JSON.stringify({
        business_id: bizId,
        name: name,
        sku: "", // Automatically assigned by system
        cost_price_usd: cost,
        price_usd: price,
        quantity: qty,
        unit: unit,
        low_stock_threshold: threshold,
        barcode: barcode,
        category: category,
        subcategory: subcategory,
        brand: brand,
        description: desc,
        specifications: specifications,
        image_url: imageUrl,
        wholesale_price_usd: wholesalePrice,
        wholesale_min_qty: wholesaleQty
      })
    });

    if (res.ok) {
      const data = await res.json();
      hideModals();
      state.pendingProductImage = "";
      
      // Reset form
      document.getElementById('form-add-store-product').reset();
      const previewWrap = document.getElementById('store-product-image-preview-wrap');
      if (previewWrap) previewWrap.innerHTML = `<span style="font-size: 1.2rem; color: var(--text-muted);">📷</span>`;
      const specRows = document.getElementById('store-product-specs-rows');
      if (specRows) specRows.innerHTML = '';
      const breadcrumb = document.getElementById('store-product-cat-breadcrumb');
      if (breadcrumb) breadcrumb.innerHTML = '';

      alert(`Product "${name}" (SKU: ${data.sku}) successfully added to store catalog and synced to Data Node storage!`);
      loadPosProducts();
      loadBusinessCatalog();
      loadMarketplaceCatalog();
    } else {
      const err = await res.json();
      alert("Failed to add product: " + (err.detail || "Unknown error"));
    }
  } catch (e) {
    alert("Error adding product: " + e.message);
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
  const totalCostElem = document.getElementById('calc-total-cost-usd');
  if (totalCostElem) totalCostElem.innerText = `$${totalCost.toFixed(2)}`;

  const mHarvest = parseFloat(document.getElementById('calc-mass-harvest').value || "0");
  const mSelf = parseFloat(document.getElementById('calc-mass-self').value || "0");
  const mComm = Math.max(0, mHarvest - mSelf);
  const commMassElem = document.getElementById('calc-comm-mass-val');
  if (commMassElem) commMassElem.innerText = `${mComm.toFixed(0)} kg`;

  const markup = parseFloat(document.getElementById('calc-markup-slider').value || "1.0");
  const markupLabelElem = document.getElementById('calc-markup-label');
  if (markupLabelElem) markupLabelElem.innerText = `${(markup * 100).toFixed(0)}% (${(1 + markup).toFixed(1)}x)`;

  const costFloor = mComm > 0 ? (totalCost / mComm) : 0.50;
  const basePrice = costFloor * (1.0 + markup);

  const costFloorElem = document.getElementById('calc-cost-floor-val');
  const basePriceElem = document.getElementById('calc-base-price-val');
  if (costFloorElem) costFloorElem.innerText = `$${costFloor.toFixed(2)} / kg`;
  if (basePriceElem) basePriceElem.innerText = `$${basePrice.toFixed(2)} / kg`;
}

async function loadHarvests() {
  try {
    const res = await secureFetch("/api/agri/harvests");
    if (!res.ok) return;
    const data = await res.json();
    state.harvests = data.harvests || [];

    if (typeof updateSubNav === 'function' && state.activeView === 'agriculture') {
      const activeBtn = document.getElementById('subnav-pill-bar')?.querySelector('.tab-pill-btn.active');
      const preferredSubId = activeBtn ? activeBtn.getAttribute('onclick')?.match(/'([^']+)'\s*,\s*this/)?.[1] : null;
      updateSubNav('agriculture', preferredSubId);
    }
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
      container.innerHTML = state.socialStories.map(s => {
        const authorName = s.author_full_name ? s.author_full_name : `@${s.author}`;
        const hasAvatar = s.author_avatar && s.author_avatar.trim();
        return `
          <div class="story-bubble" onclick="alert('Story from ${authorName}: ${escapeHtml(s.content_text)}')">
            <div class="story-ring">
              <div class="story-avatar" style="${hasAvatar ? `background-image: url('${s.author_avatar}'); background-size: cover; background-position: center; font-size: 0;` : ''}">
                ${hasAvatar ? '' : s.author.charAt(0).toUpperCase()}
              </div>
            </div>
            <span class="story-author-label" title="${authorName}">${authorName}</span>
          </div>
        `;
      }).join('');
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
      const authorDisplay = p.author_full_name ? p.author_full_name : `@${p.author}`;
      const hasAvatar = p.author_avatar && p.author_avatar.trim();

      return `
        <div class="social-card" id="card-${p.id}">
          <div class="social-card-header">
            <div class="social-card-author-group">
              <div class="user-avatar-badge" style="width: 38px; height: 38px; ${hasAvatar ? `background-image: url('${p.author_avatar}'); background-size: cover; background-position: center; border: 1.5px solid var(--accent-cyan);` : 'font-size: 0.9rem;'}">
                ${hasAvatar ? '' : p.author.charAt(0).toUpperCase()}
              </div>
              <div>
                <strong style="color: #fff; font-size: 0.95rem;">${escapeHtml(authorDisplay)}</strong>
                ${p.author_full_name ? `<span style="font-size: 0.75rem; color: var(--accent-cyan); margin-left: 6px;">@${escapeHtml(p.author)}</span>` : ''}
                <span style="font-size: 0.75rem; color: var(--text-muted); margin-left: 8px;">${p.created_at_utc ? p.created_at_utc.substring(0, 16).replace('T', ' ') : ''}</span>
              </div>
            </div>
            <span class="role-pill-badge" style="background: rgba(255,255,255,0.06);">${typeIcons[p.post_type] || '💬'} ${p.post_type.toUpperCase()}</span>
          </div>

          <p style="font-size: 0.92rem; line-height: 1.5; color: var(--text-main); margin-bottom: 8px;">${escapeHtml(p.content_text)}</p>
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
          list.innerHTML = (data.comments || []).map(c => {
            const authorDisplay = c.author_full_name ? c.author_full_name : `@${c.author}`;
            const hasAvatar = c.author_avatar && c.author_avatar.trim();
            return `
              <div style="background: rgba(255,255,255,0.03); padding: 8px 12px; border-radius: 12px; font-size: 0.82rem; display: flex; align-items: center; gap: 8px;">
                <div style="width: 22px; height: 22px; border-radius: 50%; ${hasAvatar ? `background-image: url('${c.author_avatar}'); background-size: cover; background-position: center; border: 1px solid var(--accent-cyan);` : 'background: rgba(255,255,255,0.1); font-size: 0.68rem; display: flex; align-items: center; justify-content: center; font-weight: 700;'} flex-shrink: 0;">
                  ${hasAvatar ? '' : c.author.charAt(0).toUpperCase()}
                </div>
                <div>
                  <strong style="color: var(--accent-cyan);">${escapeHtml(authorDisplay)}:</strong>
                  <span style="color: var(--text-main); margin-left: 4px;">${escapeHtml(c.comment_text)}</span>
                </div>
              </div>
            `;
          }).join('') || `<span style="font-size: 0.75rem; color: var(--text-muted);">No comments yet.</span>`;
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
    state.allPosProducts = items || [];

    // Filter by selected business store if not 'all'
    if (state.selectedPosBusinessId && state.selectedPosBusinessId !== 'all') {
      state.posProducts = state.allPosProducts.filter(p => p.business_id === state.selectedPosBusinessId);
    } else {
      state.posProducts = state.allPosProducts;
    }

    updateDashboardLiveFeeds();

    const dashCatalog = document.getElementById('dash-catalog-count');
    if (dashCatalog) {
      dashCatalog.innerText = `● ${state.allPosProducts.length} Catalog Items`;
    }

    if (typeof updateSubNav === 'function' && state.activeView === 'business') {
      const activeBtn = document.getElementById('subnav-pill-bar')?.querySelector('.tab-pill-btn.active');
      const preferredSubId = activeBtn ? activeBtn.getAttribute('onclick')?.match(/'([^']+)'\s*,\s*this/)?.[1] : null;
      updateSubNav('business', preferredSubId);
    }

    const emptyBox = document.getElementById('pos-empty-store-container');
    const activeTerm = document.getElementById('pos-active-terminal-container');

    if (state.businesses.length === 0) {
      if (emptyBox) emptyBox.style.display = 'none';
      if (activeTerm) activeTerm.style.display = 'none';
    } else if (state.posProducts.length === 0) {
      if (emptyBox) emptyBox.style.display = 'block';
      if (activeTerm) activeTerm.style.display = 'none';
    } else {
      if (emptyBox) emptyBox.style.display = 'none';
      if (activeTerm) activeTerm.style.display = 'block';
    }

    const select = document.getElementById('pos-product-select');
    const saSelect = document.getElementById('sa-item-select');

    if (select) {
      if (state.posProducts.length === 0) {
        select.innerHTML = `<option value="">-- No items in store. Click "+ New Product" --</option>`;
      } else {
        select.innerHTML = state.posProducts.map(p => {
          const b = state.businesses.find(biz => biz.id === p.business_id);
          const bName = b ? ` [${b.name}]` : '';
          return `<option value="${p.id}">${p.name}${bName} ($${p.current_price_usd.toFixed(2)} / ${p.unit}) - Qty: ${p.quantity}</option>`;
        }).join('');
      }
    }

    if (saSelect) {
      if (state.posProducts.length === 0) {
        saSelect.innerHTML = `<option value="">-- No items available --</option>`;
      } else {
        saSelect.innerHTML = state.posProducts.map(p => `
          <option value="${p.id}">${p.name} (Current Qty: ${p.quantity} ${p.unit})</option>
        `).join('');
      }
    }
  } catch (e) {
    console.error("Failed to load POS products:", e);
  }
}

async function loadBusinessCatalog() {
  try {
    const res = await secureFetch("/api/inventory");
    if (!res.ok) return;
    const data = await res.json();
    state.allBusinessProducts = Array.isArray(data) ? data : (data.items || []);

    // Filter by selected business store if not 'all'
    if (state.selectedPosBusinessId && state.selectedPosBusinessId !== 'all') {
      state.businessProducts = state.allBusinessProducts.filter(p => p.business_id === state.selectedPosBusinessId);
    } else {
      state.businessProducts = state.allBusinessProducts;
    }

    // Populate category filter dropdown
    const catSelect = document.getElementById('catalog-category-filter');
    if (catSelect) {
      const uniqueCats = Array.from(new Set(state.businessProducts.map(p => p.category).filter(Boolean)));
      catSelect.innerHTML = `<option value="">All Categories</option>` + uniqueCats.map(c => `<option value="${c}">${c}</option>`).join('');
    }

    renderBusinessProductsTable(state.businessProducts);
  } catch (e) {
    console.error("Failed to load business inventory catalog:", e);
  }
}

function filterBusinessCatalog() {
  const query = (document.getElementById('catalog-search-input')?.value || '').toLowerCase().trim();
  const selectedCat = (document.getElementById('catalog-category-filter')?.value || '').trim();

  let filtered = state.businessProducts || [];
  if (selectedCat) {
    filtered = filtered.filter(p => p.category === selectedCat);
  }
  if (query) {
    filtered = filtered.filter(p => {
      const matchName = (p.name || '').toLowerCase().includes(query);
      const matchSku = (p.sku || '').toLowerCase().includes(query);
      const matchBarcode = (p.barcode || '').toLowerCase().includes(query);
      const matchBrand = (p.brand || '').toLowerCase().includes(query);
      const matchCat = (p.category || '').toLowerCase().includes(query);
      const matchSub = (p.subcategory || '').toLowerCase().includes(query);
      return matchName || matchSku || matchBarcode || matchBrand || matchCat || matchSub;
    });
  }

  renderBusinessProductsTable(filtered);
}

function renderBusinessProductsTable(products) {
  const container = document.getElementById('business-products-table-container');
  if (!container) return;

  if (!products || products.length === 0) {
    container.innerHTML = `
      <div style="padding: 32px; text-align: center; background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.1); border-radius: 16px;">
        <div style="font-size: 2.2rem; margin-bottom: 8px;">📦</div>
        <h4 style="color: #fff; margin-bottom: 6px;">No Store Products Found</h4>
        <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 14px;">Use the product form to register items, prices, barcodes, and details.</p>
        <button class="btn-pill-primary" onclick="openAddStoreProductModal()">+ Add Store Product</button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="table-responsive-wrapper">
      <table class="visitor-table">
        <thead>
          <tr>
            <th style="width: 50px;">Image</th>
            <th>Item & Brand</th>
            <th>Store</th>
            <th>SKU / Barcode</th>
            <th>Category</th>
            <th>Cost (COGS)</th>
            <th>Selling Price</th>
            <th>Stock Qty</th>
            <th style="text-align: center;">Action</th>
          </tr>
        </thead>
        <tbody>
          ${products.map(p => {
            const cost = p.cost_price_usd || 0;
            const price = p.price_usd || 0;
            const margin = price > 0 ? (((price - cost) / price) * 100).toFixed(0) : 0;
            const isLowStock = p.quantity <= (p.low_stock_threshold || 5);
            const b = state.businesses.find(biz => biz.id === p.business_id);
            const storeName = b ? b.name : 'Store';
            return `
              <tr>
                <td>
                  <div style="width: 42px; height: 42px; border-radius: 8px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.08); overflow: hidden; display: flex; align-items: center; justify-content: center;">
                    ${p.image_url ? `<img src="${p.image_url}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.parentElement.innerHTML='📦'">` : `<span style="font-size: 1.2rem;">📦</span>`}
                  </div>
                </td>
                <td>
                  <div style="font-weight: 700; color: #fff;">${p.name}</div>
                  ${p.brand ? `<div style="font-size: 0.72rem; color: var(--accent-cyan);">🏢 ${p.brand}</div>` : ''}
                </td>
                <td>
                  <span style="padding: 2px 8px; border-radius: 6px; background: rgba(16,185,129,0.15); color: #34d399; font-size: 0.72rem; font-weight: 600;">
                    ${storeName}
                  </span>
                </td>
                <td>
                  <div style="font-family: monospace; font-size: 0.8rem; color: #38bdf8;">${p.sku || 'N/A'}</div>
                  ${p.barcode ? `<div style="font-family: monospace; font-size: 0.7rem; color: var(--text-muted);">🏷️ ${p.barcode}</div>` : ''}
                </td>
                <td>
                  ${p.category ? `<span style="padding: 2px 8px; border-radius: 6px; background: rgba(255,255,255,0.05); font-size: 0.72rem; color: #e2e8f0;">${p.category}${p.subcategory ? ` &gt; ${p.subcategory}` : ''}</span>` : '<span style="color: var(--text-muted); font-size: 0.75rem;">General</span>'}
                </td>
                <td>
                  <span style="font-family: var(--font-display); color: #cbd5e1;">$${cost.toFixed(2)}</span>
                </td>
                <td>
                  <div style="font-family: var(--font-display); font-weight: 700; color: var(--accent-cyan);">$${price.toFixed(2)}</div>
                  <div style="font-size: 0.7rem; color: #10b981;">+${margin}% margin</div>
                </td>
                <td>
                  <span style="padding: 3px 8px; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; background: ${isLowStock ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)'}; color: ${isLowStock ? '#ef4444' : '#10b981'};">
                    ${p.quantity} ${p.unit || 'pcs'} ${isLowStock ? '⚠️ Low' : ''}
                  </span>
                </td>
                <td style="text-align: center;">
                  <button class="btn-pill-small" style="font-size: 0.72rem; background: rgba(0, 229, 255, 0.1); color: var(--accent-cyan);" onclick="quickAddToCart('${p.id}')">+ POS Cart</button>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;
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
      grid.innerHTML = `
        <div class="glass-panel" style="grid-column: 1 / -1; padding: 32px; text-align: center; background: rgba(255,255,255,0.02);">
          <div style="font-size: 2.2rem; margin-bottom: 8px;">🏪</div>
          <h4 style="color: #fff; margin-bottom: 6px;">No Store Products Listed Yet</h4>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 16px;">Operators can input inventory directly or record farm crop harvests to stock the catalog.</p>
          <button class="btn-pill-primary" onclick="openAddStoreProductModal()">+ Add Store Product</button>
        </div>
      `;
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
  const prod = state.allPosProducts ? state.allPosProducts.find(p => p.id === itemId) : state.posProducts.find(p => p.id === itemId);
  if (!prod) return;
  const existing = state.cart.find(c => c.id === itemId);
  if (existing) existing.qty += 1;
  else state.cart.push({ ...prod, qty: 1 });
  renderCart();
  switchView('business');
}

function renderCart() {
  const tbody = document.getElementById('pos-cart-table-body');
  const totalDisplay = document.getElementById('pos-cart-total-usd');

  let total = 0.0;
  if (state.cart.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:16px; color: var(--text-muted);">Cart is empty.</td></tr>`;
  } else {
    tbody.innerHTML = state.cart.map((c, idx) => {
      const subtotal = c.current_price_usd * c.qty;
      total += subtotal;
      const b = state.businesses.find(biz => biz.id === c.business_id);
      const storeName = b ? b.name : 'Store';
      return `
        <tr>
          <td><strong>${c.name}</strong></td>
          <td><span style="padding: 2px 6px; border-radius: 4px; background: rgba(16,185,129,0.15); color: #34d399; font-size: 0.72rem;">${storeName}</span></td>
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
    populateCurrencyDropdowns();
    if (state.wallet) {
      renderBankingBalances();
    }
    if (state.activeView === 'admin') {
      renderAdminCurrencies();
      searchGlobalCatalog("");
    }
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

function toggleWidgetCollapse(widgetId) {
  const el = document.getElementById(widgetId);
  if (!el) return;
  const isCollapsed = el.classList.toggle('is-collapsed');
  const btn = el.querySelector('.btn-collapse-toggle') || el.querySelector(`[onclick*="toggleWidgetCollapse('${widgetId}')"]`);
  if (btn) {
    btn.innerHTML = isCollapsed ? '▲' : '▼';
    btn.title = isCollapsed ? 'Expand to standard view' : 'Minimize to compact pill';
  }
}
window.toggleWidgetCollapse = toggleWidgetCollapse;

function closeAllFullscreenPanels() {
  const fsPanels = document.querySelectorAll('.panel-fullscreen');
  fsPanels.forEach(panel => {
    panel.classList.remove('panel-fullscreen');
    const btns = panel.querySelectorAll('.btn-panel-expand');
    btns.forEach(btn => {
      if (btn.classList.contains('btn-card-ctrl')) {
        btn.innerHTML = '⛶';
        btn.title = 'Expand to Fullscreen';
      } else {
        btn.innerHTML = '⛶ Expand';
        btn.title = 'Expand to Fullscreen';
      }
    });
  });
  document.getElementById('panel-fullscreen-backdrop')?.classList.remove('is-active');
  document.body.style.overflow = '';
}
window.closeAllFullscreenPanels = closeAllFullscreenPanels;

function togglePanelFullscreen(panelId) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const isFs = panel.classList.toggle('panel-fullscreen');
  const btns = panel.querySelectorAll('.btn-panel-expand');
  btns.forEach(btn => {
    if (btn.classList.contains('btn-card-ctrl')) {
      btn.innerHTML = isFs ? '🗗' : '⛶';
      btn.title = isFs ? 'Exit Fullscreen Mode (or press Esc)' : 'Expand to Fullscreen';
    } else {
      btn.innerHTML = isFs ? '🗗 Restore (Esc)' : '⛶ Expand';
      btn.title = isFs ? 'Exit Fullscreen Mode (or press Esc)' : 'Expand to Fullscreen';
    }
  });

  const backdrop = document.getElementById('panel-fullscreen-backdrop');
  if (isFs) {
    if (backdrop) backdrop.classList.add('is-active');
    document.body.style.overflow = 'hidden';
    panel.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    const anyRemaining = document.querySelector('.panel-fullscreen');
    if (!anyRemaining) {
      if (backdrop) backdrop.classList.remove('is-active');
      document.body.style.overflow = '';
    }
  }
}
window.togglePanelFullscreen = togglePanelFullscreen;

// Global escape key listener to close any expanded panel
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' || e.key === 'Esc') {
    closeAllFullscreenPanels();
  }
});

const LOGIN_POSSIBILITIES = [
  "🌐 <strong>Decentralized Mesh:</strong> Sovereign peer-to-peer data nodes with zero single points of failure.",
  "🪙 <strong>Dynamic Value Systems:</strong> Continuous pricing models, decay curves, and multi-currency ledgers.",
  "🛡️ <strong>Offline First:</strong> Full transactional autonomy, cryptographic vaults, and local consensus.",
  "⚡ <strong>Adaptive Scalability:</strong> Modular micro-services dynamically tailored to local community needs.",
  "🔒 <strong>Cryptographic Vaults:</strong> Scrypt key derivation, HMAC-SHA256 signatures, and zero-knowledge audits.",
  "🌍 <strong>Global Interoperability:</strong> Sovereign local economies seamlessly interfacing with global currencies."
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

// --- PASSWORD VISIBILITY TOGGLE & REAL-TIME STRENGTH CHECKER ---
function togglePasswordVisibility(inputId, btnElement) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isHidden = (input.type === 'password');
  input.type = isHidden ? 'text' : 'password';
  if (btnElement) {
    btnElement.innerHTML = isHidden ? '🙈' : '👁️';
    btnElement.title = isHidden ? 'Hide what you are typing' : 'View what you are typing';
    btnElement.setAttribute('aria-label', btnElement.title);
  }
}

function checkPasswordStrength(password, prefix) {
  const pwd = password || '';
  const lenEl = document.getElementById(`chk-${prefix}-len`);
  const upperEl = document.getElementById(`chk-${prefix}-upper`);
  const lowerEl = document.getElementById(`chk-${prefix}-lower`);
  const numEl = document.getElementById(`chk-${prefix}-num`);
  const symEl = document.getElementById(`chk-${prefix}-sym`);
  const meterBar = document.getElementById(`${prefix}-meter-bar`);
  const strengthLabel = document.getElementById(`${prefix}-strength-label`);

  const hasLen = pwd.length >= 12;
  const hasUpper = /[A-Z]/.test(pwd);
  const hasLower = /[a-z]/.test(pwd);
  const hasNum = /[0-9]/.test(pwd);
  const hasSym = /[^A-Za-z0-9]/.test(pwd);

  const updateItem = (el, valid, text) => {
    if (!el) return;
    if (valid) {
      el.style.color = '#10b981';
      el.innerHTML = `✅ <span style="color:#10b981; font-weight:600;">${text}</span>`;
    } else {
      el.style.color = 'var(--text-muted)';
      el.innerHTML = `⚪ <span style="color:var(--text-muted);">${text}</span>`;
    }
  };

  updateItem(lenEl, hasLen, '12+ characters');
  updateItem(upperEl, hasUpper, 'Uppercase (A-Z)');
  updateItem(lowerEl, hasLower, 'Lowercase (a-z)');
  updateItem(numEl, hasNum, 'Number (0-9)');
  updateItem(symEl, hasSym, 'Special Symbol (!@#$...)');

  // Calculate score (0 to 5)
  let score = 0;
  if (pwd.length >= 8) score++;
  if (hasLen) score++;
  if (hasUpper && hasLower) score++;
  if (hasNum) score++;
  if (hasSym) score++;

  let percent = 0;
  let color = 'var(--text-muted)';
  let labelText = 'Min 12 Chars';

  if (!pwd) {
    percent = 0;
    labelText = 'Min 12 Chars';
    color = 'var(--text-muted)';
  } else if (score <= 1) {
    percent = 20;
    color = '#ef4444';
    labelText = 'Weak ⚠️';
  } else if (score === 2) {
    percent = 40;
    color = '#f59e0b';
    labelText = 'Fair 🟡';
  } else if (score === 3) {
    percent = 65;
    color = '#3b82f6';
    labelText = 'Good 🔵';
  } else if (score === 4) {
    percent = 85;
    color = '#10b981';
    labelText = 'Strong 🟢';
  } else {
    percent = 100;
    color = 'var(--accent-cyan)';
    labelText = 'Vault-Grade 🔒✨';
  }

  if (meterBar) {
    meterBar.style.width = `${percent}%`;
    meterBar.style.background = color;
  }
  if (strengthLabel) {
    strengthLabel.innerText = labelText;
    strengthLabel.style.color = color;
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

