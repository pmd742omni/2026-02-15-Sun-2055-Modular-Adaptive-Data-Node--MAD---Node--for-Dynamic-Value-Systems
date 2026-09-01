/**
 * MADN Sovereign System Telemetry & Performance Engine
 * Tracks live FPS, Main-Thread Long Tasks (>50ms), JS Heap, Network Profiling,
 * and Host Computer Hardware health (CPU, RAM, Threads, SQLite WAL).
 */

(function () {
  'use strict';

  const telemetryState = {
    fps: 60,
    frameCount: 0,
    lastFrameTime: performance.now(),
    droppedFrames: 0,
    longTasks: [],
    networkLogs: [],
    jsHeapMb: 0,
    hostTelemetry: null,
    isConsoleOpen: false,
    activeTab: 'host',
    pollTimer: null
  };

  // 1. Frame Rate (FPS) and Frame Drop Observer
  function startFpsObserver() {
    let lastTime = performance.now();
    let frames = 0;

    function frameLoop(now) {
      frames++;
      const delta = now - lastTime;

      if (delta >= 1000) {
        telemetryState.fps = Math.round((frames * 1000) / delta);
        if (telemetryState.fps < 45) {
          telemetryState.droppedFrames++;
        }
        frames = 0;
        lastTime = now;

        // Sample JS Heap
        if (window.performance && window.performance.memory) {
          telemetryState.jsHeapMb = Math.round(window.performance.memory.usedJSHeapSize / (1024 * 1024));
        }

        updateHudBadge();
        if (telemetryState.isConsoleOpen) {
          updateConsoleView();
        }
      }

      requestAnimationFrame(frameLoop);
    }

    requestAnimationFrame(frameLoop);
  }

  // 2. Main-Thread Long Task Observer (>50ms freeze detector)
  function startLongTaskObserver() {
    if ('PerformanceObserver' in window) {
      try {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const task = {
              timestamp: new Date().toLocaleTimeString(),
              durationMs: Math.round(entry.duration),
              startTime: Math.round(entry.startTime),
              name: entry.name,
              attribution: entry.attribution ? entry.attribution.map(a => a.name || a.containerType).join(', ') : 'main-script'
            };

            telemetryState.longTasks.unshift(task);
            if (telemetryState.longTasks.length > 50) telemetryState.longTasks.pop();

            // Send critical freeze event to backend diagnostics log
            logClientEvent('long_task_freeze', task);

            updateHudBadge();
          }
        });

        observer.observe({ entryTypes: ['longtask'] });
      } catch (e) {
        console.debug("PerformanceObserver for longtask not supported or restricted.");
      }
    }
  }

  // 3. Network & Fetch Profiler (Intercepts fetch requests)
  function initNetworkProfiler() {
    const originalFetch = window.fetch;
    window.fetch = async function (...args) {
      const start = performance.now();
      const url = typeof args[0] === 'string' ? args[0] : (args[0] && args[0].url) || '';
      const method = (args[1] && args[1].method) || 'GET';

      try {
        const response = await originalFetch.apply(this, args);
        const duration = Math.round(performance.now() - start);

        if (url.includes('/api/') && !url.includes('/api/system/telemetry')) {
          const logEntry = {
            timestamp: new Date().toLocaleTimeString(),
            url: url.replace(window.location.origin, ''),
            method: method.toUpperCase(),
            status: response.status,
            durationMs: duration
          };

          telemetryState.networkLogs.unshift(logEntry);
          if (telemetryState.networkLogs.length > 40) telemetryState.networkLogs.pop();

          if (duration > 150) {
            logClientEvent('slow_network_fetch', logEntry);
          }
        }
        return response;
      } catch (err) {
        const duration = Math.round(performance.now() - start);
        if (url.includes('/api/')) {
          telemetryState.networkLogs.unshift({
            timestamp: new Date().toLocaleTimeString(),
            url: url.replace(window.location.origin, ''),
            method: method.toUpperCase(),
            status: 'ERR',
            durationMs: duration,
            error: err.message
          });
        }
        throw err;
      }
    };
  }

  // 4. Send Client Telemetry Event to Backend
  function logClientEvent(type, data) {
    try {
      const payload = JSON.stringify({ type, data });
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/system/telemetry/log', payload);
      } else {
        fetch('/api/system/telemetry/log', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payload
        }).catch(() => {});
      }
    } catch (e) {}
  }

  // 5. Host Telemetry Poller
  async function fetchHostTelemetry() {
    if (document.hidden) return; // Save resources when tab is idle
    try {
      const res = await fetch('/api/system/telemetry');
      if (res.ok) {
        const data = await res.json();
        telemetryState.hostTelemetry = data.telemetry;
        updateHudBadge();
        if (telemetryState.isConsoleOpen) {
          updateConsoleView();
        }
      }
    } catch (e) {}
  }

  // 6. UI HUD Badge & Modal Creation
  function mountTelemetryUi() {
    if (document.getElementById('madn-telemetry-hud-badge')) return;

    // A. Floating HUD Badge
    const badge = document.createElement('div');
    badge.id = 'madn-telemetry-hud-badge';
    badge.title = 'Click to open Sovereign System Telemetry & Performance Diagnostic Center';
    badge.innerHTML = `
      <div class="hud-pill" onclick="window.toggleTelemetryConsole()">
        <span class="hud-indicator" id="hud-status-dot"></span>
        <span class="hud-metric" id="hud-fps-val">60 FPS</span>
        <span class="hud-divider">|</span>
        <span class="hud-metric" id="hud-cpu-val">CPU: --%</span>
        <span class="hud-divider">|</span>
        <span class="hud-metric" id="hud-ram-val">RAM: --MB</span>
        <span class="hud-divider">|</span>
        <span class="hud-metric" id="hud-lat-val">--ms</span>
      </div>
    `;

    // B. Modal Console
    const modal = document.createElement('div');
    modal.id = 'madn-telemetry-modal';
    modal.className = 'telemetry-modal-backdrop hidden';
    modal.innerHTML = `
      <div class="telemetry-modal-container glass-panel">
        <div class="telemetry-modal-header">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.4rem;">⚡</span>
            <div>
              <h3 style="margin: 0; font-size: 1.1rem; color: #fff; font-weight: 800; letter-spacing: 0.5px;">Sovereign System Telemetry & Diagnostics</h3>
              <p style="margin: 0; font-size: 0.75rem; color: var(--text-muted);">Real-Time Host Hardware, Backend Engine & Main-Thread Profiler</p>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <button class="btn-pill-small" onclick="window.refreshTelemetrySnapshot()" style="padding: 4px 10px; font-size: 0.72rem;">🔄 Refresh</button>
            <button class="btn-pill-small" onclick="window.toggleTelemetryConsole()" style="padding: 4px 10px; font-size: 0.72rem; background: rgba(239,68,68,0.2); color: #f87171;">✕ Close</button>
          </div>
        </div>

        <!-- Tab Navigation -->
        <div class="telemetry-tabs">
          <button class="telemetry-tab active" id="tab-btn-host" onclick="window.switchTelemetryTab('host')">💻 Host & Hardware</button>
          <button class="telemetry-tab" id="tab-btn-network" onclick="window.switchTelemetryTab('network')">🌐 API & Network Profiler</button>
          <button class="telemetry-tab" id="tab-btn-client" onclick="window.switchTelemetryTab('client')">⚡ UI & Main-Thread</button>
          <button class="telemetry-tab" id="tab-btn-logs" onclick="window.switchTelemetryTab('logs')">📜 Diagnostics Log</button>
        </div>

        <!-- Tab Content Viewport -->
        <div class="telemetry-tab-viewport" id="telemetry-viewport">
          <!-- Dynamic Content Injected Here -->
        </div>
      </div>
    `;

    // Inject Styles
    const style = document.createElement('style');
    style.textContent = `
      #madn-telemetry-hud-badge {
        position: fixed;
        bottom: 14px;
        right: 14px;
        z-index: 9990;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, monospace;
        user-select: none;
      }
      .hud-pill {
        display: flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: rgba(10, 14, 22, 0.88);
        border: 1px solid rgba(0, 229, 255, 0.3);
        border-radius: 999px;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5), 0 0 10px rgba(0, 229, 255, 0.15);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        color: #e2e8f0;
        font-size: 0.72rem;
        font-weight: 700;
        cursor: pointer;
        transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
      }
      .hud-pill:hover {
        transform: translateY(-2px);
        border-color: var(--accent-cyan);
        box-shadow: 0 6px 22px rgba(0, 229, 255, 0.3);
      }
      .hud-indicator {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #10b981;
        box-shadow: 0 0 6px #10b981;
        transition: background 0.3s;
      }
      .hud-indicator.warn {
        background: #f59e0b;
        box-shadow: 0 0 6px #f59e0b;
      }
      .hud-indicator.danger {
        background: #ef4444;
        box-shadow: 0 0 8px #ef4444;
      }
      .hud-divider {
        color: rgba(255, 255, 255, 0.2);
        font-weight: 300;
      }
      .telemetry-modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(4, 6, 12, 0.82);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
      }
      .telemetry-modal-backdrop.hidden {
        display: none !important;
      }
      .telemetry-modal-container {
        width: 100%;
        max-width: 880px;
        max-height: 85vh;
        background: rgba(14, 20, 32, 0.95);
        border: 1px solid rgba(0, 229, 255, 0.35);
        border-radius: 18px;
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.8), 0 0 24px rgba(0, 229, 255, 0.15);
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      .telemetry-modal-header {
        padding: 16px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .telemetry-tabs {
        display: flex;
        gap: 6px;
        padding: 10px 20px;
        background: rgba(0, 0, 0, 0.3);
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        overflow-x: auto;
      }
      .telemetry-tab {
        padding: 6px 14px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: var(--text-muted);
        font-size: 0.78rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.2s;
      }
      .telemetry-tab.active {
        background: rgba(0, 229, 255, 0.18);
        border-color: var(--accent-cyan);
        color: var(--accent-cyan);
      }
      .telemetry-tab-viewport {
        padding: 20px;
        overflow-y: auto;
        flex-grow: 1;
      }
      .metric-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
        margin-bottom: 18px;
      }
      .metric-card {
        background: rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 12px 14px;
      }
      .metric-card-title {
        font-size: 0.72rem;
        color: var(--text-muted);
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .metric-card-value {
        font-size: 1.3rem;
        font-weight: 800;
        color: #fff;
      }
      .metric-card-sub {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 2px;
      }
      .telemetry-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.75rem;
        font-family: monospace;
      }
      .telemetry-table th {
        text-align: left;
        padding: 8px 10px;
        background: rgba(0, 0, 0, 0.4);
        color: var(--accent-cyan);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      }
      .telemetry-table td {
        padding: 6px 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        color: #cbd5e1;
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(badge);
    document.body.appendChild(modal);
  }

  // 7. Update Floating HUD Badge View
  function updateHudBadge() {
    const dot = document.getElementById('hud-status-dot');
    const fpsEl = document.getElementById('hud-fps-val');
    const cpuEl = document.getElementById('hud-cpu-val');
    const ramEl = document.getElementById('hud-ram-val');
    const latEl = document.getElementById('hud-lat-val');

    if (!fpsEl) return;

    fpsEl.innerText = `${telemetryState.fps} FPS`;

    const host = telemetryState.hostTelemetry?.host;
    const backend = telemetryState.hostTelemetry?.backend;

    if (host && cpuEl) {
      cpuEl.innerText = `CPU: ${Math.round(host.cpu_percent)}%`;
    }

    if (backend && ramEl) {
      ramEl.innerText = `RAM: ${Math.round(backend.process_ram_mb)}MB`;
    }

    if (backend && latEl) {
      latEl.innerText = `${Math.round(backend.avg_api_latency_ms)}ms`;
    }

    if (dot) {
      if (telemetryState.fps < 35 || (host && host.cpu_percent > 65)) {
        dot.className = 'hud-indicator danger';
      } else if (telemetryState.fps < 50 || (host && host.cpu_percent > 25)) {
        dot.className = 'hud-indicator warn';
      } else {
        dot.className = 'hud-indicator';
      }
    }
  }

  // 8. Update Modal Console View
  function updateConsoleView() {
    const vp = document.getElementById('telemetry-viewport');
    if (!vp) return;

    const t = telemetryState.hostTelemetry;
    const host = t?.host;
    const backend = t?.backend;
    const db = t?.database;

    if (telemetryState.activeTab === 'host') {
      vp.innerHTML = `
        <div class="metric-card-grid">
          <div class="metric-card">
            <div class="metric-card-title">Host CPU Usage</div>
            <div class="metric-card-value" style="color: ${host && host.cpu_percent > 30 ? '#f59e0b' : '#10b981'};">${host ? host.cpu_percent : '--'}%</div>
            <div class="metric-card-sub">${host ? `${host.cpu_cores} Logical Cores (${host.os})` : 'Sampling...'}</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">Host RAM Usage</div>
            <div class="metric-card-value" style="color: #38bdf8;">${host ? `${host.ram_used_gb} / ${host.ram_total_gb} GB` : '--'}</div>
            <div class="metric-card-sub">${host ? `${host.ram_percent}% Allocated (${host.ram_free_gb} GB Free)` : 'Sampling...'}</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">Python Process RAM</div>
            <div class="metric-card-value" style="color: var(--accent-cyan);">${backend ? `${backend.process_ram_mb} MB` : '--'}</div>
            <div class="metric-card-sub">${backend ? `${backend.threads} Active Threads (WorkingSet64)` : 'Sampling...'}</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">SQLite Database & WAL</div>
            <div class="metric-card-value" style="color: #c084fc;">${db ? `${db.db_size_kb} KB` : '--'}</div>
            <div class="metric-card-sub">${db ? `WAL: ${db.wal_size_kb} KB (Active: ${db.wal_active ? 'Yes' : 'No'})` : 'Sampling...'}</div>
          </div>
        </div>

        <h4 style="font-size: 0.85rem; color: #fff; margin: 16px 0 8px 0;">⚡ Backend Engine Latency Distribution</h4>
        <div class="metric-card-grid">
          <div class="metric-card">
            <div class="metric-card-title">Average Latency</div>
            <div class="metric-card-value" style="color: #10b981;">${backend ? `${backend.avg_api_latency_ms} ms` : '--'}</div>
            <div class="metric-card-sub">Rolling 100 Requests</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">P50 Median Latency</div>
            <div class="metric-card-value" style="color: #38bdf8;">${backend ? `${backend.p50_api_latency_ms} ms` : '--'}</div>
            <div class="metric-card-sub">50% of requests faster than</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">P95 Worst-Case Latency</div>
            <div class="metric-card-value" style="color: ${backend && backend.p95_api_latency_ms > 100 ? '#f59e0b' : '#10b981'};">${backend ? `${backend.p95_api_latency_ms} ms` : '--'}</div>
            <div class="metric-card-sub">95% of requests faster than</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">Total Requests Profiled</div>
            <div class="metric-card-value" style="color: #e2e8f0;">${backend ? backend.total_requests_profiled : '0'}</div>
            <div class="metric-card-sub">Uptime: ${t ? `${Math.round(t.uptime_seconds / 60)}m` : '--'}</div>
          </div>
        </div>
      `;
    } else if (telemetryState.activeTab === 'network') {
      const rows = telemetryState.networkLogs.map(r => `
        <tr>
          <td><span style="color: var(--text-muted);">${r.timestamp}</span></td>
          <td><strong style="color: ${r.method === 'POST' ? '#38bdf8' : '#10b981'};">${r.method}</strong></td>
          <td><code>${r.url}</code></td>
          <td><span style="color: ${r.status >= 400 ? '#ef4444' : '#10b981'};">${r.status}</span></td>
          <td><strong style="color: ${r.durationMs > 100 ? '#f59e0b' : '#10b981'};">${r.durationMs} ms</strong></td>
        </tr>
      `).join('');

      vp.innerHTML = `
        <h4 style="font-size: 0.85rem; color: #fff; margin: 0 0 10px 0;">🌐 Recent Client-Side Network Requests (${telemetryState.networkLogs.length})</h4>
        ${telemetryState.networkLogs.length === 0 ? '<p style="color: var(--text-muted); font-size: 0.8rem;">No recent network requests recorded yet.</p>' : `
          <div style="overflow-x: auto; background: rgba(0,0,0,0.3); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);">
            <table class="telemetry-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Method</th>
                  <th>API Endpoint</th>
                  <th>Status</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                ${rows}
              </tbody>
            </table>
          </div>
        `}
      `;
    } else if (telemetryState.activeTab === 'client') {
      const taskRows = telemetryState.longTasks.map(task => `
        <tr>
          <td><span style="color: var(--text-muted);">${task.timestamp}</span></td>
          <td><strong style="color: #ef4444;">${task.durationMs} ms</strong></td>
          <td><code>${task.attribution}</code></td>
        </tr>
      `).join('');

      vp.innerHTML = `
        <div class="metric-card-grid">
          <div class="metric-card">
            <div class="metric-card-title">Live Rendering FPS</div>
            <div class="metric-card-value" style="color: ${telemetryState.fps >= 50 ? '#10b981' : '#ef4444'};">${telemetryState.fps} FPS</div>
            <div class="metric-card-sub">${telemetryState.droppedFrames} Dropped Frame Ticks (<45 FPS)</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">Browser JS Heap Memory</div>
            <div class="metric-card-value" style="color: var(--accent-cyan);">${telemetryState.jsHeapMb || '--'} MB</div>
            <div class="metric-card-sub">Chromium V8 Engine Allocated</div>
          </div>
          <div class="metric-card">
            <div class="metric-card-title">Main-Thread Freezes (>50ms)</div>
            <div class="metric-card-value" style="color: ${telemetryState.longTasks.length > 0 ? '#f59e0b' : '#10b981'};">${telemetryState.longTasks.length}</div>
            <div class="metric-card-sub">Observed Long Tasks</div>
          </div>
        </div>

        <h4 style="font-size: 0.85rem; color: #fff; margin: 16px 0 8px 0;">🚨 Main-Thread Freeze Event History</h4>
        ${telemetryState.longTasks.length === 0 ? '<p style="color: #10b981; font-size: 0.8rem;">✅ Zero main-thread freezes detected. Rendering is completely smooth.</p>' : `
          <div style="overflow-x: auto; background: rgba(0,0,0,0.3); border-radius: 10px; border: 1px solid rgba(255,255,255,0.06);">
            <table class="telemetry-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Freeze Duration</th>
                  <th>Attribution</th>
                </tr>
              </thead>
              <tbody>
                ${taskRows}
              </tbody>
            </table>
          </div>
        `}
      `;
    } else if (telemetryState.activeTab === 'logs') {
      fetch('/api/system/telemetry/diagnostics-log?lines=80')
        .then(r => r.json())
        .then(data => {
          const logs = data.logs || [];
          const logContent = logs.join('\n');
          vp.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
              <h4 style="font-size: 0.85rem; color: #fff; margin: 0;">📜 Unified Diagnostics Log Tail (system_diagnostics.log)</h4>
              <div style="display: flex; gap: 8px;">
                <button class="btn-pill-small" onclick="window.clearDiagnosticsLog()" style="padding: 4px 10px; font-size: 0.72rem; background: rgba(239,68,68,0.2); color: #f87171;">🗑️ Clear Log</button>
              </div>
            </div>
            <pre style="background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 14px; color: #a5f3fc; font-family: monospace; font-size: 0.72rem; line-height: 1.5; max-height: 380px; overflow-y: auto; white-space: pre-wrap;">${logContent || 'Log is currently empty.'}</pre>
          `;
        })
        .catch(() => {
          vp.innerHTML = '<p style="color: var(--danger);">Failed to load diagnostics log.</p>';
        });
    }
  }

  // 9. Window Global Handlers
  window.toggleTelemetryConsole = function () {
    const modal = document.getElementById('madn-telemetry-modal');
    if (!modal) return;

    telemetryState.isConsoleOpen = !telemetryState.isConsoleOpen;
    if (telemetryState.isConsoleOpen) {
      modal.classList.remove('hidden');
      updateConsoleView();
      fetchHostTelemetry();
    } else {
      modal.classList.add('hidden');
    }
  };

  window.switchTelemetryTab = function (tabName) {
    telemetryState.activeTab = tabName;
    ['host', 'network', 'client', 'logs'].forEach(t => {
      const btn = document.getElementById(`tab-btn-${t}`);
      if (btn) {
        if (t === tabName) btn.classList.add('active');
        else btn.classList.remove('active');
      }
    });
    updateConsoleView();
  };

  window.refreshTelemetrySnapshot = function () {
    fetchHostTelemetry();
  };

  window.clearDiagnosticsLog = async function () {
    if (!confirm("Are you sure you want to reset the system diagnostics log?")) return;
    try {
      await fetch('/api/system/telemetry/diagnostics-log', { method: 'DELETE' });
      window.switchTelemetryTab('logs');
    } catch (e) {}
  };

  // 10. Bootstrap Engine
  function init() {
    mountTelemetryUi();
    startFpsObserver();
    startLongTaskObserver();
    initNetworkProfiler();
    fetchHostTelemetry();

    // Poll host telemetry every 2.5 seconds
    telemetryState.pollTimer = setInterval(fetchHostTelemetry, 2500);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
