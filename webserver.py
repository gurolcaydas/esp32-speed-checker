import usocket as socket
import ujson as json
import gc

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Server Sentinel - caydas.cloud Health & Latency Monitor</title>
<style>
:root {
  --bg: #070a13;
  --card: rgba(18, 26, 44, 0.78);
  --border: rgba(255, 255, 255, 0.08);
  --cyan: #00f2fe;
  --blue: #38bdf8;
  --purple: #a855f7;
  --green: #10b981;
  --amber: #f59e0b;
  --red: #ef4444;
  --text: #f8fafc;
  --muted: #94a3b8;
}
* { margin:0; padding:0; box-sizing:border-box; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }
body { background:linear-gradient(135deg, #070a12 0%, #0f172a 100%); color:var(--text); min-height:100vh; padding:20px; display:flex; justify-content:center; }
.container { width:100%; max-width:880px; }
header { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:20px; padding-bottom:16px; border-bottom:1px solid var(--border); }
.logo-box { display:flex; align-items:center; gap:12px; }
.badge { background:linear-gradient(135deg, var(--cyan), var(--blue)); color:#04101e; padding:6px 12px; border-radius:10px; font-size:12px; font-weight:800; letter-spacing:0.5px; }
h1 { font-size:21px; font-weight:800; letter-spacing:-0.5px; }
.header-pills { display:flex; gap:8px; align-items:center; }
.pill { padding:5px 12px; border-radius:99px; font-size:12px; font-weight:700; display:flex; align-items:center; gap:6px; }
.pill.up { background:rgba(16,185,129,0.18); color:var(--green); border:1px solid rgba(16,185,129,0.35); }
.pill.down { background:rgba(239,68,68,0.18); color:var(--red); border:1px solid rgba(239,68,68,0.35); }
.pill.busy { background:rgba(245,158,11,0.15); color:var(--amber); border:1px solid rgba(245,158,11,0.3); }
.pill.sched { background:rgba(56,189,248,0.12); color:var(--blue); border:1px solid rgba(56,189,248,0.25); }
.dot { width:8px; height:8px; border-radius:50%; background:currentColor; animation:pulse 1.8s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:16px; margin-bottom:20px; }
.card { background:var(--card); backdrop-filter:blur(14px); border:1px solid var(--border); border-radius:18px; padding:20px; box-shadow:0 12px 30px rgba(0,0,0,0.35); position:relative; overflow:hidden; }
.card::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, var(--cyan), var(--blue)); }
.card.danger::before { background:linear-gradient(90deg, var(--amber), var(--red)); }
.card-label { font-size:12px; color:var(--muted); text-transform:uppercase; font-weight:700; letter-spacing:0.6px; margin-bottom:8px; }
.val-row { display:flex; align-items:baseline; gap:6px; }
.huge { font-size:36px; font-weight:900; letter-spacing:-1px; line-height:1; }
.unit { color:var(--muted); font-size:14px; font-weight:600; }
.subtext { margin-top:8px; font-size:12px; color:var(--muted); }

.action-card { background:var(--card); backdrop-filter:blur(14px); border:1px solid var(--border); border-radius:18px; padding:22px; display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:16px; margin-bottom:20px; }
.sched-box { display:flex; align-items:center; gap:10px; background:rgba(255,255,255,0.04); padding:8px 14px; border-radius:12px; border:1px solid var(--border); }
.sched-lbl { font-size:12px; color:var(--muted); font-weight:600; text-transform:uppercase; }
select { background:transparent; border:none; color:#fff; font-size:13px; font-weight:600; cursor:pointer; outline:none; }
select option { background:#0f172a; color:#fff; }
.btn { background:linear-gradient(135deg, var(--cyan), var(--blue)); color:#04101e; border:none; padding:12px 24px; border-radius:12px; font-weight:800; font-size:14px; cursor:pointer; transition:transform 0.15s, box-shadow 0.15s; display:inline-flex; align-items:center; gap:8px; }
.btn:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,242,254,0.35); }
.btn:disabled { opacity:0.5; cursor:not-allowed; transform:none; box-shadow:none; }

.chart-card { margin-bottom:20px; }
.chart-header { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:14px; }
.chart-controls { display:flex; gap:6px; }
.tab-btn { background:rgba(255,255,255,0.06); border:1px solid var(--border); color:var(--muted); padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600; cursor:pointer; transition:all 0.15s; }
.tab-btn.active { background:rgba(0,242,254,0.15); color:var(--cyan); border-color:var(--cyan); }
.legend-row { display:flex; gap:14px; align-items:center; font-size:12px; color:var(--muted); }
.legend-item { display:flex; align-items:center; gap:6px; }
.legend-dot { width:8px; height:8px; border-radius:50%; }
.chart-container { position:relative; width:100%; height:220px; }
canvas { width:100%; height:100%; display:block; }

.stats-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(360px, 1fr)); gap:16px; margin-bottom:20px; }
.stat-card { padding:20px; }
.card-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }
.tag-pill { background:rgba(255,255,255,0.06); border:1px solid var(--border); color:var(--muted); font-size:11px; padding:3px 8px; border-radius:6px; font-weight:600; }
.stat-metrics { display:flex; flex-direction:column; gap:12px; }
.metric-row { display:flex; justify-content:space-between; align-items:center; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.04); }
.m-name { font-size:13px; color:var(--muted); font-weight:600; }
.m-vals { display:flex; align-items:baseline; gap:5px; font-family:monospace; }
.m-best { color:var(--green); font-weight:800; font-size:15px; }
.m-worst { color:var(--amber); font-weight:800; font-size:15px; }
.m-div { color:var(--muted); font-size:12px; }
.m-unit { color:var(--muted); font-size:11px; }
.stat-footer { margin-top:12px; font-size:12px; color:var(--muted); text-align:right; }

table { width:100%; border-collapse:collapse; margin-top:10px; font-size:13px; }
th { text-align:left; color:var(--muted); font-weight:600; padding:10px 8px; border-bottom:1px solid var(--border); }
td { padding:10px 8px; border-bottom:1px solid rgba(255,255,255,0.03); }

.config-section { margin-top:20px; background:var(--card); border:1px solid var(--border); border-radius:18px; padding:20px; }
.form-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:10px; }
input { background:rgba(255,255,255,0.05); border:1px solid var(--border); padding:10px 14px; border-radius:10px; color:#fff; font-size:14px; flex:1; min-width:180px; }
input:focus { outline:none; border-color:var(--cyan); }
.toast { font-size:12px; color:var(--cyan); margin-top:6px; min-height:16px; }
</style>
</head>
<body>
<div class="container">
<header>
  <div class="logo-box">
    <span class="badge">ESP32</span>
    <h1>caydas.cloud Sentinel & Latency Monitor</h1>
  </div>
  <div class="header-pills">
    <div class="pill sched" id="schedPill">Auto: 5m</div>
    <div class="pill up" id="serverPill"><span class="dot"></span><span id="serverTxt">caydas.cloud: ONLINE</span></div>
  </div>
</header>

<div class="grid">
  <!-- Card 1: Server Up Flag -->
  <div class="card" id="flagCard">
    <div class="card-label">Server Status Flag</div>
    <div class="val-row"><span class="huge" id="flagVal" style="color:var(--green)">ONLINE</span></div>
    <div class="subtext" id="flagSub">HTTP 200 OK &bull; caydas.cloud</div>
  </div>

  <!-- Card 2: Server Latency -->
  <div class="card">
    <div class="card-label">caydas.cloud Latency</div>
    <div class="val-row"><span class="huge" id="pingVal" style="color:var(--cyan)">--</span><span class="unit">ms</span></div>
    <div class="subtext" id="ttfbSub">TTFB Response: -- ms</div>
  </div>

  <!-- Card 3: Gateway Latency -->
  <div class="card">
    <div class="card-label">Internet Gateway (1.1.1.1)</div>
    <div class="val-row"><span class="huge" id="gateVal" style="color:var(--blue)">--</span><span class="unit">ms</span></div>
    <div class="subtext" id="jitterSub">Jitter: -- ms</div>
  </div>

  <!-- Card 4: Wi-Fi Signal -->
  <div class="card">
    <div class="card-label">Local Wi-Fi Signal</div>
    <div class="val-row"><span class="huge" id="rssiVal" style="color:var(--green)">--</span><span class="unit">dBm</span></div>
    <div class="subtext" id="rssiQuality">Quality: --</div>
  </div>
</div>

<div class="action-card">
  <div style="flex:1;min-width:220px">
    <h3 style="margin-bottom:4px;font-size:16px">Continuous Uptime & Latency Check</h3>
    <p style="color:var(--muted);font-size:13px" id="lastTested">Last check: Not checked yet</p>
  </div>
  <div class="sched-box">
    <span class="sched-lbl">Check Every:</span>
    <select id="intervalSel" onchange="updateInterval()">
      <option value="0">Disabled (Manual only)</option>
      <option value="1">Every 1 Minute</option>
      <option value="2">Every 2 Minutes</option>
      <option value="5" selected>Every 5 Minutes (Recommended)</option>
      <option value="15">Every 15 Minutes</option>
      <option value="30">Every 30 Minutes</option>
      <option value="60">Every 1 Hour</option>
    </select>
  </div>
  <button class="btn" id="runBtn" onclick="triggerTest()">
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
    <span>Check Server Now</span>
  </button>
</div>

<!-- LATENCY TIMELINE CHART -->
<div class="card chart-card">
  <div class="chart-header">
    <div>
      <div class="card-label" style="margin-bottom:2px">Response Time & Latency Trend (ms)</div>
      <div class="legend-row">
        <div class="legend-item"><span class="legend-dot" style="background:var(--cyan)"></span> caydas.cloud Ping (ms)</div>
        <div class="legend-item"><span class="legend-dot" style="background:var(--blue)"></span> Gateway Ping (ms)</div>
      </div>
    </div>
    <div class="chart-controls">
      <button class="tab-btn active" id="btnModeAll" onclick="setChartMode('all')">All Latencies</button>
      <button class="tab-btn" id="btnModeServer" onclick="setChartMode('server')">Server Only</button>
      <button class="tab-btn" id="btnModeGate" onclick="setChartMode('gate')">Gateway Only</button>
    </div>
  </div>
  <div class="chart-container">
    <canvas id="perfChart"></canvas>
  </div>
</div>

<!-- TODAY & MONTH PEAK / LOW LATENCIES & UPTIME -->
<div class="stats-grid">
  <!-- Today's Stats Card -->
  <div class="card stat-card">
    <div class="card-head">
      <div class="card-label">Today's Server Performance</div>
      <span class="tag-pill" id="tdTag">Today</span>
    </div>
    <div class="stat-metrics">
      <div class="metric-row">
        <span class="m-name">Uptime Availability</span>
        <div class="m-vals">
          <span class="m-best" id="tdUptime" style="font-size:18px">100.0%</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Latency (Lowest / Highest)</span>
        <div class="m-vals">
          <span class="m-best" id="tdPingMin">--</span>
          <span class="m-div">/</span>
          <span class="m-worst" id="tdPingMax">--</span>
          <span class="m-unit">ms</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Average Latency</span>
        <div class="m-vals">
          <span class="m-best" id="tdPingAvg">--</span>
          <span class="m-unit">ms</span>
        </div>
      </div>
    </div>
    <div class="stat-footer" id="tdSummary">Total Checks: 0 (0 Up / 0 Down)</div>
  </div>

  <!-- Month's Stats Card -->
  <div class="card stat-card">
    <div class="card-head">
      <div class="card-label">This Month's Server Performance</div>
      <span class="tag-pill" id="moTag">This Month</span>
    </div>
    <div class="stat-metrics">
      <div class="metric-row">
        <span class="m-name">Monthly Uptime</span>
        <div class="m-vals">
          <span class="m-best" id="moUptime" style="font-size:18px">100.0%</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Latency (Lowest / Highest)</span>
        <div class="m-vals">
          <span class="m-best" id="moPingMin">--</span>
          <span class="m-div">/</span>
          <span class="m-worst" id="moPingMax">--</span>
          <span class="m-unit">ms</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Monthly Average Latency</span>
        <div class="m-vals">
          <span class="m-best" id="moPingAvg">--</span>
          <span class="m-unit">ms</span>
        </div>
      </div>
    </div>
    <div class="stat-footer" id="moSummary">Total Checks: 0 (0 Up / 0 Down)</div>
  </div>
</div>

<div class="card" style="margin-bottom:20px">
  <div class="card-label">Recent Uptime & Health Log</div>
  <table>
    <thead><tr><th>Time</th><th>Target Server</th><th>Status Flag</th><th>HTTP Code</th><th>Server Ping</th><th>Gateway</th></tr></thead>
    <tbody id="histBody"><tr><td colspan="6" style="color:var(--muted)">No checks recorded yet.</td></tr></tbody>
  </table>
</div>

<div class="config-section">
  <div class="card-label">Target Server & Wi-Fi Settings</div>
  <div class="form-row">
    <input type="text" id="targetHost" placeholder="Target Host (e.g., caydas.cloud)" value="caydas.cloud">
    <input type="number" id="targetPort" placeholder="Port" value="80" style="max-width:100px">
    <button class="btn" style="padding:10px 18px" onclick="saveTarget()">Save Server Target</button>
  </div>
  <div class="form-row" style="margin-top:14px">
    <input type="text" id="ssid" placeholder="Wi-Fi SSID">
    <input type="password" id="pw" placeholder="Wi-Fi Password">
    <button class="btn" style="padding:10px 18px" onclick="saveWifi()">Save & Reconnect Wi-Fi</button>
  </div>
  <div class="toast" id="cfgMsg"></div>
</div>

</div>

<script>
let polling = false;
let chartMode = 'all';
let historyData = [];
let hoverIdx = -1;

function setChartMode(mode){
  chartMode = mode;
  document.getElementById('btnModeAll').className = 'tab-btn' + (mode === 'all' ? ' active' : '');
  document.getElementById('btnModeServer').className = 'tab-btn' + (mode === 'server' ? ' active' : '');
  document.getElementById('btnModeGate').className = 'tab-btn' + (mode === 'gate' ? ' active' : '');
  drawChart();
}

function drawChart(){
  const canvas = document.getElementById('perfChart');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  
  canvas.width = rect.width * dpr;
  canvas.height = 220 * dpr;
  ctx.scale(dpr, dpr);
  
  const w = rect.width;
  const h = 220;
  ctx.clearRect(0, 0, w, h);
  
  if(!historyData || historyData.length === 0){
    ctx.fillStyle = '#64748b';
    ctx.font = '13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No health checks recorded yet. Click "Check Server Now" to probe caydas.cloud.', w/2, h/2);
    return;
  }
  
  const padL = 46, padR = 24, padT = 20, padB = 30;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const pts = historyData;
  const n = pts.length;
  
  let maxMs = 50;
  pts.forEach(p => {
    if(p.server && p.server.ping_ms > maxMs) maxMs = p.server.ping_ms;
    if(p.internet && p.internet.avg > maxMs) maxMs = p.internet.avg;
  });
  maxMs = Math.ceil(maxMs * 1.2);
  
  // Gridlines
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.fillStyle = '#64748b';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'right';
  ctx.lineWidth = 1;
  
  const gridSteps = 4;
  for(let i=0; i<=gridSteps; i++){
    const y = padT + (plotH / gridSteps) * i;
    ctx.beginPath();
    ctx.moveTo(padL, y);
    ctx.lineTo(w - padR, y);
    ctx.stroke();
    const v = Math.round(maxMs - (maxMs / gridSteps) * i);
    ctx.fillText(v + 'ms', padL - 8, y + 4);
  }
  
  function getX(i){
    if(n === 1) return padL + plotW / 2;
    return padL + (i / (n - 1)) * plotW;
  }
  function getY(v){
    return padT + plotH - (v / maxMs) * plotH;
  }
  
  // X-axis timestamps
  ctx.textAlign = 'center';
  ctx.fillStyle = '#64748b';
  for(let i=0; i<n; i++){
    if(n > 8 && i % Math.ceil(n / 6) !== 0 && i !== n - 1) continue;
    const x = getX(i);
    const lbl = pts[i].short_time || pts[i].timestamp || ('#' + (i+1));
    ctx.fillText(lbl, x, h - 8);
  }
  
  function drawLine(getter, color, fillGrad){
    ctx.beginPath();
    for(let i=0; i<n; i++){
      const val = getter(pts[i]);
      const x = getX(i);
      const y = getY(val);
      if(i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.stroke();
    
    if(fillGrad && n > 1){
      const lastX = getX(n - 1);
      const firstX = getX(0);
      const bY = padT + plotH;
      ctx.lineTo(lastX, bY);
      ctx.lineTo(firstX, bY);
      ctx.closePath();
      ctx.fillStyle = fillGrad;
      ctx.fill();
    }
    
    // Data points
    for(let i=0; i<n; i++){
      const val = getter(pts[i]);
      const x = getX(i);
      const y = getY(val);
      ctx.beginPath();
      ctx.arc(x, y, (hoverIdx === i) ? 5 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#070a13';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }
  
  const sGrad = ctx.createLinearGradient(0, padT, 0, padT + plotH);
  sGrad.addColorStop(0, 'rgba(0, 242, 254, 0.25)');
  sGrad.addColorStop(1, 'rgba(0, 242, 254, 0.0)');
  
  if(chartMode === 'all' || chartMode === 'server'){
    drawLine(p => (p.server ? p.server.ping_ms : 0), '#00f2fe', sGrad);
  }
  if(chartMode === 'all' || chartMode === 'gate'){
    drawLine(p => (p.internet ? p.internet.avg : 0), '#38bdf8', null);
  }
  
  // Hover crosshair and tip
  if(hoverIdx >= 0 && hoverIdx < n){
    const p = pts[hoverIdx];
    const x = getX(hoverIdx);
    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(x, padT);
    ctx.lineTo(x, padT + plotH);
    ctx.stroke();
    ctx.setLineDash([]);
    
    const sPing = p.server ? p.server.ping_ms : 0;
    const gPing = p.internet ? p.internet.avg : 0;
    const stCode = (p.server && p.server.status_code) ? p.server.status_code : 'ERR';
    const tip = `${p.timestamp || ''} | Server: ${sPing}ms [${stCode}] | Gateway: ${gPing}ms`;
    ctx.font = '11px sans-serif';
    const tw = ctx.measureText(tip).width;
    let tx = x - tw / 2 - 8;
    if(tx < padL) tx = padL;
    if(tx + tw + 16 > w - padR) tx = w - padR - tw - 16;
    
    ctx.fillStyle = 'rgba(15, 23, 42, 0.95)';
    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.rect(tx, 4, tw + 16, 20);
    ctx.fill();
    ctx.stroke();
    
    ctx.fillStyle = '#f8fafc';
    ctx.textAlign = 'left';
    ctx.fillText(tip, tx + 8, 18);
  }
}

const canvasEl = document.getElementById('perfChart');
if(canvasEl){
  canvasEl.addEventListener('mousemove', e => {
    if(!historyData || historyData.length === 0) return;
    const r = canvasEl.getBoundingClientRect();
    const x = e.clientX - r.left;
    const padL = 46, padR = 24;
    const plotW = r.width - padL - padR;
    const n = historyData.length;
    if(n === 1){ hoverIdx = 0; }
    else{
      const ratio = Math.max(0, Math.min(1, (x - padL) / plotW));
      hoverIdx = Math.round(ratio * (n - 1));
    }
    drawChart();
  });
  canvasEl.addEventListener('mouseleave', () => { hoverIdx = -1; drawChart(); });
}
window.addEventListener('resize', drawChart);

async function fetchStatus(){
  try{
    const r = await fetch('/api/status');
    const d = await r.json();

    // 1. Target server & flag
    const isUp = d.is_server_up;
    const flagVal = document.getElementById('flagVal');
    const flagSub = document.getElementById('flagSub');
    const sPill = document.getElementById('serverPill');
    const sTxt = document.getElementById('serverTxt');
    const flagCard = document.getElementById('flagCard');

    if(isUp){
      flagVal.innerText = 'ONLINE';
      flagVal.style.color = 'var(--green)';
      flagCard.className = 'card';
      sPill.className = 'pill up';
      sTxt.innerText = `${d.target || 'Server'}: ONLINE`;
      flagSub.innerText = `HTTP ${d.server ? d.server.status_code : 200} OK \u2022 ${d.target || 'caydas.cloud'}`;
    }else{
      flagVal.innerText = d.flag || 'OFFLINE';
      flagVal.style.color = 'var(--red)';
      flagCard.className = 'card danger';
      sPill.className = 'pill down';
      sTxt.innerText = `${d.target || 'Server'}: OFFLINE`;
      flagSub.innerText = `${d.server && d.server.error ? d.server.error : 'Connection Failed'}`;
    }

    if(d.server){
      document.getElementById('pingVal').innerText = d.server.ping_ms || '--';
      document.getElementById('ttfbSub').innerText = 'TTFB Response: ' + (d.server.response_time_ms || '--') + ' ms';
    }
    if(d.internet){
      document.getElementById('gateVal').innerText = d.internet.avg || '--';
      document.getElementById('jitterSub').innerText = 'Jitter: ' + (d.internet.jitter || 0) + ' ms';
    }
    if(d.wifi){
      document.getElementById('rssiVal').innerText = d.wifi.rssi || '--';
      document.getElementById('rssiQuality').innerText = (d.wifi.quality || '--') + ' (' + (d.wifi.percent || 0) + '%)';
    }
    if(d.last){
      document.getElementById('lastTested').innerText = 'Last check: ' + d.last.timestamp + ' (' + d.last.flag + ')';
    }

    if(d.history){
      historyData = d.history;
      drawChart();
      if(d.history.length > 0){
        let h = '';
        for(let i=d.history.length-1; i>=0; i--){
          const x = d.history[i];
          const stColor = x.is_server_up ? 'var(--green)' : 'var(--red)';
          const codeTxt = (x.server && x.server.status_code) ? x.server.status_code : 'ERR';
          h += `<tr><td>${x.date ? (x.date.slice(5) + ' ') : ''}${x.timestamp}</td><td><strong>${x.target}</strong></td><td><span style="color:${stColor};font-weight:700">${x.flag}</span></td><td>HTTP ${codeTxt}</td><td style="color:var(--cyan);font-weight:700">${x.server ? x.server.ping_ms : 0} ms</td><td>${x.internet ? x.internet.avg : 0} ms</td></tr>`;
        }
        document.getElementById('histBody').innerHTML = h;
      }
    }

    if(d.stats){
      renderExtremes(d.stats);
    }

    if(d.interval_min !== undefined){
      const sel = document.getElementById('intervalSel');
      if(document.activeElement !== sel) sel.value = d.interval_min;
      const sched = document.getElementById('schedPill');
      if(d.interval_min === 0){
        sched.innerText = 'Auto: Off';
      }else if(d.next_test_in_s !== null && d.next_test_in_s !== undefined){
        const m = Math.floor(d.next_test_in_s / 60);
        const s = d.next_test_in_s % 60;
        sched.innerText = `Next: ${m}m ${s}s`;
      }else{
        sched.innerText = `Auto: ${d.interval_min}m`;
      }
    }

    if(d.target){
      const tIn = document.getElementById('targetHost');
      if(document.activeElement !== tIn && !tIn.value) tIn.value = d.target;
    }

    const btn = document.getElementById('runBtn');
    if(d.is_running){
      btn.disabled = true;
      btn.querySelector('span').innerText = 'Checking server...';
      if(!polling){ polling = setInterval(fetchStatus, 2000); }
    }else{
      btn.disabled = false;
      btn.querySelector('span').innerText = 'Check Server Now';
      if(polling){ clearInterval(polling); polling = false; }
    }
  }catch(e){ console.error(e); }
}

function renderExtremes(s){
  const td = s.today || {};
  if(td.date) document.getElementById('tdTag').innerText = td.date;
  if(td.total > 0){
    document.getElementById('tdUptime').innerText = (td.uptime_pct !== undefined ? td.uptime_pct : 100.0) + '%';
    document.getElementById('tdPingMin').innerText = td.ping_min || 0;
    document.getElementById('tdPingMax').innerText = td.ping_max || 0;
    const avg = td.up > 0 ? (td.ping_sum / td.up).toFixed(1) : 0;
    document.getElementById('tdPingAvg').innerText = avg;
    document.getElementById('tdSummary').innerText = `Total Checks: ${td.total} (${td.up} Up / ${td.total - td.up} Down)`;
  }

  const mo = s.month || {};
  if(mo.month) document.getElementById('moTag').innerText = mo.month;
  if(mo.total > 0){
    document.getElementById('moUptime').innerText = (mo.uptime_pct !== undefined ? mo.uptime_pct : 100.0) + '%';
    document.getElementById('moPingMin').innerText = mo.ping_min || 0;
    document.getElementById('moPingMax').innerText = mo.ping_max || 0;
    const avg = mo.up > 0 ? (mo.ping_sum / mo.up).toFixed(1) : 0;
    document.getElementById('moPingAvg').innerText = avg;
    document.getElementById('moSummary').innerText = `Total Checks: ${mo.total} (${mo.up} Up / ${mo.total - mo.up} Down)`;
  }
}

async function triggerTest(){
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  btn.querySelector('span').innerText = 'Probing caydas.cloud...';
  try{ await fetch('/api/run', {method:'POST'}); }catch(e){}
  
  let attempts = 0;
  const pollInterval = setInterval(async ()=>{
    attempts++;
    try{
      const r = await fetch('/api/status');
      if(r.ok){
        await fetchStatus();
        if(attempts >= 3) clearInterval(pollInterval);
      }
    }catch(err){}
    if(attempts > 10){
      clearInterval(pollInterval);
      fetchStatus();
    }
  }, 2000);
}

async function updateInterval(){
  const v = parseInt(document.getElementById('intervalSel').value);
  try{
    await fetch('/api/config', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({interval_min: v})
    });
    fetchStatus();
  }catch(e){ console.error(e); }
}

async function saveTarget(){
  const host = document.getElementById('targetHost').value.trim();
  const port = parseInt(document.getElementById('targetPort').value) || 80;
  if(!host){ alert('Please enter target server hostname'); return; }
  const msg = document.getElementById('cfgMsg');
  msg.innerText = 'Updating target server to ' + host + '...';
  await fetch('/api/config', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({target_server: host, target_port: port})
  });
  setTimeout(()=>{ msg.innerText = 'Target server updated!'; fetchStatus(); }, 1000);
}

async function saveWifi(){
  const s = document.getElementById('ssid').value;
  const p = document.getElementById('pw').value;
  if(!s){ alert('Please enter SSID'); return; }
  const msg = document.getElementById('cfgMsg');
  msg.innerText = 'Saving credentials and restarting Wi-Fi...';
  await fetch('/api/config', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ssid:s, password:p})
  });
}

fetchStatus();
setInterval(fetchStatus, 6000);
</script>
</body>
</html>
"""

class WebServer:
    def __init__(self, tester, config_manager):
        self.tester = tester
        self.config_manager = config_manager
        self.server_socket = None

    def start(self, port=80):
        gc.collect()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(3)
        self.server_socket.settimeout(0.2)
        print(f"Server Sentinel Web Dashboard started on port {port}")

    def handle_client(self):
        if not self.server_socket:
            return

        try:
            cl, addr = self.server_socket.accept()
        except OSError:
            return

        try:
            cl.settimeout(3.0)
            req_line = cl.readline().decode('utf-8', 'ignore')
            if not req_line:
                cl.close()
                return

            parts = req_line.split()
            if len(parts) < 2:
                cl.close()
                return

            method, path = parts[0], parts[1]

            content_length = 0
            while True:
                line = cl.readline().decode('utf-8', 'ignore')
                if line == '\r\n' or line == '\n' or not line:
                    break
                if line.lower().startswith('content-length:'):
                    try:
                        content_length = int(line.split(':')[1].strip())
                    except:
                        pass

            body = b""
            if content_length > 0:
                body = cl.read(content_length)

            if path == '/' or path == '/index.html':
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\n\r\n")
                cl.sendall(DASHBOARD_HTML.encode('utf-8'))
            elif path == '/api/status':
                last_res = self.tester.last_result or {}
                data = {
                    "target": self.tester.target_server,
                    "is_server_up": last_res.get("is_server_up", True),
                    "flag": last_res.get("flag", "ONLINE"),
                    "server": last_res.get("server", {"ping_ms": 0, "status_code": 200, "response_time_ms": 0}),
                    "internet": last_res.get("internet", {"avg": 0, "jitter": 0}),
                    "wifi": self.tester.get_wifi_info(),
                    "is_running": self.tester.is_running,
                    "last": self.tester.last_result,
                    "history": self.tester.history,
                    "stats": getattr(self.tester, "stats", {}),
                    "interval_min": self.config_manager.config.get("auto_test_interval_min", 5),
                    "next_test_in_s": getattr(self.tester, "next_test_in_s", None)
                }
                body_bytes = json.dumps(data).encode('utf-8')
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n")
                cl.sendall(body_bytes)
            elif path == '/api/run' and method == 'POST':
                if not self.tester.is_running:
                    self.tester.pending_test = True
                cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{\"status\":\"started\"}")
            elif path == '/api/config' and method == 'POST':
                try:
                    cfg = json.loads(body.decode('utf-8'))
                    if 'interval_min' in cfg:
                        self.config_manager.update_interval(cfg.get('interval_min'))
                    if 'target_server' in cfg:
                        srv = cfg.get('target_server')
                        prt = cfg.get('target_port', 80)
                        self.config_manager.update_target(srv, prt)
                        self.tester.set_target(srv, prt)
                    if 'ssid' in cfg:
                        self.config_manager.update_wifi(cfg.get('ssid', ''), cfg.get('password', ''))
                    cl.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nConnection: close\r\n\r\n{\"status\":\"saved\"}")
                except Exception as e:
                    cl.send(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
            else:
                cl.send(b"HTTP/1.1 404 Not Found\r\nConnection: close\r\n\r\n")
        except Exception as e:
            pass
        finally:
            try:
                cl.close()
            except:
                pass
            gc.collect()
