import usocket as socket
import ujson as json
import gc

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ESP32 Speed Checker & Network Diagnostics</title>
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
header { display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:24px; padding-bottom:16px; border-bottom:1px solid var(--border); }
.logo-box { display:flex; align-items:center; gap:12px; }
.badge { background:linear-gradient(135deg, var(--cyan), var(--purple)); color:#04101e; padding:6px 12px; border-radius:10px; font-size:12px; font-weight:800; letter-spacing:0.5px; }
h1 { font-size:22px; font-weight:800; letter-spacing:-0.5px; }
.header-pills { display:flex; gap:8px; align-items:center; }
.pill { background:rgba(16,185,129,0.15); color:var(--green); border:1px solid rgba(16,185,129,0.3); padding:5px 12px; border-radius:99px; font-size:12px; font-weight:600; display:flex; align-items:center; gap:6px; }
.pill.busy { background:rgba(245,158,11,0.15); color:var(--amber); border-color:rgba(245,158,11,0.3); }
.pill.sched { background:rgba(56,189,248,0.12); color:var(--blue); border-color:rgba(56,189,248,0.25); }
.dot { width:8px; height:8px; border-radius:50%; background:currentColor; animation:pulse 1.8s infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

.grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(190px, 1fr)); gap:16px; margin-bottom:20px; }
.card { background:var(--card); backdrop-filter:blur(14px); border:1px solid var(--border); border-radius:18px; padding:20px; box-shadow:0 12px 30px rgba(0,0,0,0.35); position:relative; overflow:hidden; }
.card::before { content:""; position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, var(--cyan), var(--purple)); }
.card-label { font-size:12px; color:var(--muted); text-transform:uppercase; font-weight:700; letter-spacing:0.6px; margin-bottom:8px; }
.val-row { display:flex; align-items:baseline; gap:6px; }
.huge { font-size:38px; font-weight:900; letter-spacing:-1px; line-height:1; }
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
.m-peak { color:var(--cyan); font-weight:800; font-size:15px; }
.m-low { color:var(--amber); font-weight:800; font-size:15px; }
.m-best { color:var(--green); font-weight:800; font-size:15px; }
.m-worst { color:var(--red); font-weight:800; font-size:15px; }
.m-div { color:var(--muted); font-size:12px; }
.m-unit { color:var(--muted); font-size:11px; }
.stat-footer { margin-top:12px; font-size:12px; color:var(--muted); text-align:right; }

table { width:100%; border-collapse:collapse; margin-top:10px; font-size:13px; }
th { text-align:left; color:var(--muted); font-weight:600; padding:10px 8px; border-bottom:1px solid var(--border); }
td { padding:10px 8px; border-bottom:1px solid rgba(255,255,255,0.03); }

.wifi-section { margin-top:20px; background:var(--card); border:1px solid var(--border); border-radius:18px; padding:20px; }
.form-row { display:flex; flex-wrap:wrap; gap:10px; margin-top:10px; }
input { background:rgba(255,255,255,0.05); border:1px solid var(--border); padding:10px 14px; border-radius:10px; color:#fff; font-size:14px; flex:1; min-width:180px; }
input:focus { outline:none; border-color:var(--cyan); }
.toast { font-size:12px; color:var(--cyan); margin-top:6px; min-height:16px; transition:opacity 0.3s; }
</style>
</head>
<body>
<div class="container">
<header>
  <div class="logo-box">
    <span class="badge">ESP32</span>
    <h1>Network Speed Diagnostics</h1>
  </div>
  <div class="header-pills">
    <div class="pill sched" id="schedPill">Auto-test: 30m</div>
    <div class="pill" id="statusPill"><span class="dot"></span><span id="statusTxt">Connected</span></div>
  </div>
</header>

<div class="grid">
  <div class="card">
    <div class="card-label">Download Speed</div>
    <div class="val-row"><span class="huge" id="downVal" style="color:var(--cyan)">--</span><span class="unit">Mbps</span></div>
    <div class="subtext" id="downSub">Cloudflare CDN</div>
  </div>
  <div class="card">
    <div class="card-label">Upload Speed</div>
    <div class="val-row"><span class="huge" id="upVal" style="color:var(--purple)">--</span><span class="unit">Mbps</span></div>
    <div class="subtext" id="upSub">Direct Stream</div>
  </div>
  <div class="card">
    <div class="card-label">Latency (Ping)</div>
    <div class="val-row"><span class="huge" id="pingVal" style="color:var(--blue)">--</span><span class="unit">ms</span></div>
    <div class="subtext" id="jitterSub">Jitter: -- ms</div>
  </div>
  <div class="card">
    <div class="card-label">Wi-Fi Signal</div>
    <div class="val-row"><span class="huge" id="rssiVal" style="color:var(--green)">--</span><span class="unit">dBm</span></div>
    <div class="subtext" id="rssiQuality">Quality: --</div>
  </div>
</div>

<div class="action-card">
  <div style="flex:1;min-width:220px">
    <h3 style="margin-bottom:4px;font-size:16px">Automated Testing & Diagnostics</h3>
    <p style="color:var(--muted);font-size:13px" id="lastTested">Last test: Not tested yet</p>
  </div>
  <div class="sched-box">
    <span class="sched-lbl">Interval:</span>
    <select id="intervalSel" onchange="updateInterval()">
      <option value="0">Disabled (Manual only)</option>
      <option value="5">Every 5 Minutes</option>
      <option value="15">Every 15 Minutes</option>
      <option value="30">Every 30 Minutes</option>
      <option value="60">Every 1 Hour</option>
      <option value="120">Every 2 Hours</option>
      <option value="360">Every 6 Hours</option>
      <option value="720">Every 12 Hours</option>
      <option value="1440">Every 24 Hours</option>
    </select>
  </div>
  <button class="btn" id="runBtn" onclick="triggerTest()">
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
    <span>Start Speed Test</span>
  </button>
</div>

<!-- PERFORMANCE TIMELINE CHART -->
<div class="card chart-card">
  <div class="chart-header">
    <div>
      <div class="card-label" style="margin-bottom:2px">Performance Trend Chart</div>
      <div class="legend-row">
        <div class="legend-item"><span class="legend-dot" style="background:var(--cyan)"></span> Download (Mbps)</div>
        <div class="legend-item"><span class="legend-dot" style="background:var(--purple)"></span> Upload (Mbps)</div>
        <div class="legend-item"><span class="legend-dot" style="background:var(--blue)"></span> Latency (ms)</div>
      </div>
    </div>
    <div class="chart-controls">
      <button class="tab-btn active" id="btnModeAll" onclick="setChartMode('all')">All Metrics</button>
      <button class="tab-btn" id="btnModeSpeed" onclick="setChartMode('speed')">Speed Only</button>
      <button class="tab-btn" id="btnModePing" onclick="setChartMode('ping')">Latency Only</button>
    </div>
  </div>
  <div class="chart-container">
    <canvas id="perfChart"></canvas>
  </div>
</div>

<!-- DAY & MONTH EXTREMES (HIGHEST & LOWEST) -->
<div class="stats-grid">
  <!-- Today's Extremes Card -->
  <div class="card stat-card">
    <div class="card-head">
      <div class="card-label">Today's Extremes (Peak / Low)</div>
      <span class="tag-pill" id="tdTag">Today</span>
    </div>
    <div class="stat-metrics">
      <div class="metric-row">
        <span class="m-name">Download (Peak / Low)</span>
        <div class="m-vals">
          <span class="m-peak" id="tdDownMax">--</span>
          <span class="m-div">/</span>
          <span class="m-low" id="tdDownMin">--</span>
          <span class="m-unit">Mbps</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Upload (Peak / Low)</span>
        <div class="m-vals">
          <span class="m-peak" id="tdUpMax">--</span>
          <span class="m-div">/</span>
          <span class="m-low" id="tdUpMin">--</span>
          <span class="m-unit">Mbps</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Latency (Best / Worst)</span>
        <div class="m-vals">
          <span class="m-best" id="tdPingMin">--</span>
          <span class="m-div">/</span>
          <span class="m-worst" id="tdPingMax">--</span>
          <span class="m-unit">ms</span>
        </div>
      </div>
    </div>
    <div class="stat-footer" id="tdSummary">Average: -- Mbps | Total: 0 tests</div>
  </div>

  <!-- Month's Extremes Card -->
  <div class="card stat-card">
    <div class="card-head">
      <div class="card-label">This Month's Extremes (Peak / Low)</div>
      <span class="tag-pill" id="moTag">This Month</span>
    </div>
    <div class="stat-metrics">
      <div class="metric-row">
        <span class="m-name">Download (Peak / Low)</span>
        <div class="m-vals">
          <span class="m-peak" id="moDownMax">--</span>
          <span class="m-div">/</span>
          <span class="m-low" id="moDownMin">--</span>
          <span class="m-unit">Mbps</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Upload (Peak / Low)</span>
        <div class="m-vals">
          <span class="m-peak" id="moUpMax">--</span>
          <span class="m-div">/</span>
          <span class="m-low" id="moUpMin">--</span>
          <span class="m-unit">Mbps</span>
        </div>
      </div>
      <div class="metric-row">
        <span class="m-name">Latency (Best / Worst)</span>
        <div class="m-vals">
          <span class="m-best" id="moPingMin">--</span>
          <span class="m-div">/</span>
          <span class="m-worst" id="moPingMax">--</span>
          <span class="m-unit">ms</span>
        </div>
      </div>
    </div>
    <div class="stat-footer" id="moSummary">Average: -- Mbps | Total: 0 tests</div>
  </div>
</div>

<div class="card" style="margin-bottom:20px">
  <div class="card-label">Recent Test Log</div>
  <table>
    <thead><tr><th>Time</th><th>Download</th><th>Upload</th><th>Latency</th><th>Rating</th></tr></thead>
    <tbody id="histBody"><tr><td colspan="5" style="color:var(--muted)">No tests recorded yet.</td></tr></tbody>
  </table>
</div>

<div class="wifi-section">
  <div class="card-label">Wi-Fi Settings</div>
  <div class="form-row">
    <input type="text" id="ssid" placeholder="Wi-Fi SSID (Network Name)">
    <input type="password" id="pw" placeholder="Wi-Fi Password">
    <button class="btn" style="padding:10px 20px" onclick="saveWifi()">Save & Reconnect</button>
  </div>
  <div class="toast" id="saveMsg"></div>
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
  document.getElementById('btnModeSpeed').className = 'tab-btn' + (mode === 'speed' ? ' active' : '');
  document.getElementById('btnModePing').className = 'tab-btn' + (mode === 'ping' ? ' active' : '');
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
    ctx.fillText('No speed test data recorded yet. Run a speed test to display trends.', w/2, h/2);
    return;
  }
  
  const padL = 46, padR = 24, padT = 20, padB = 30;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const pts = historyData;
  const n = pts.length;
  
  let maxSpeed = 10;
  let maxPing = 50;
  pts.forEach(p => {
    if(p.download && p.download.mbps > maxSpeed) maxSpeed = p.download.mbps;
    if(p.upload && p.upload.mbps > maxSpeed) maxSpeed = p.upload.mbps;
    if(p.ping && p.ping.avg > maxPing) maxPing = p.ping.avg;
  });
  maxSpeed = Math.ceil(maxSpeed * 1.15);
  maxPing = Math.ceil(maxPing * 1.15);
  
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
    
    let label = '';
    if(chartMode === 'ping'){
      label = Math.round(maxPing - (maxPing / gridSteps) * i) + 'ms';
    }else{
      label = Math.round(maxSpeed - (maxSpeed / gridSteps) * i) + 'M';
    }
    ctx.fillText(label, padL - 8, y + 4);
  }
  
  function getX(i){
    if(n === 1) return padL + plotW / 2;
    return padL + (i / (n - 1)) * plotW;
  }
  function getY(v, maxV){
    return padT + plotH - (v / maxV) * plotH;
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
  
  function drawLine(getter, color, fillGrad, isPing){
    const maxV = isPing ? maxPing : maxSpeed;
    ctx.beginPath();
    for(let i=0; i<n; i++){
      const val = getter(pts[i]);
      const x = getX(i);
      const y = getY(val, maxV);
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
    
    // Nodes
    for(let i=0; i<n; i++){
      const val = getter(pts[i]);
      const x = getX(i);
      const y = getY(val, maxV);
      ctx.beginPath();
      ctx.arc(x, y, (hoverIdx === i) ? 5 : 3.5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#070a13';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }
  
  const dGrad = ctx.createLinearGradient(0, padT, 0, padT + plotH);
  dGrad.addColorStop(0, 'rgba(0, 242, 254, 0.25)');
  dGrad.addColorStop(1, 'rgba(0, 242, 254, 0.0)');
  
  const uGrad = ctx.createLinearGradient(0, padT, 0, padT + plotH);
  uGrad.addColorStop(0, 'rgba(168, 85, 247, 0.22)');
  uGrad.addColorStop(1, 'rgba(168, 85, 247, 0.0)');
  
  if(chartMode === 'all' || chartMode === 'speed'){
    drawLine(p => (p.download ? p.download.mbps : 0), '#00f2fe', dGrad, false);
    drawLine(p => (p.upload ? p.upload.mbps : 0), '#a855f7', uGrad, false);
  }
  if(chartMode === 'all' || chartMode === 'ping'){
    drawLine(p => (p.ping ? p.ping.avg : 0), '#38bdf8', null, true);
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
    
    const dVal = p.download ? p.download.mbps : 0;
    const uVal = p.upload ? p.upload.mbps : 0;
    const pVal = p.ping ? p.ping.avg : 0;
    const tip = `${p.timestamp || ''} | ${dVal}M / ${uVal}M | ${pVal}ms`;
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

// Canvas interaction
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
    if(d.wifi){
      document.getElementById('rssiVal').innerText = d.wifi.rssi || '--';
      document.getElementById('rssiQuality').innerText = (d.wifi.quality || '--') + ' (' + (d.wifi.percent || 0) + '%)';
    }
    if(d.last){
      document.getElementById('downVal').innerText = d.last.download.mbps;
      document.getElementById('upVal').innerText = d.last.upload.mbps;
      document.getElementById('pingVal').innerText = d.last.ping.avg;
      document.getElementById('jitterSub').innerText = 'Jitter: ' + d.last.ping.jitter + ' ms';
      document.getElementById('lastTested').innerText = 'Last test: ' + d.last.timestamp + ' (' + d.last.rating + ')';
    }
    if(d.history){
      historyData = d.history;
      drawChart();
      if(d.history.length > 0){
        let h = '';
        for(let i=d.history.length-1; i>=0; i--){
          const x = d.history[i];
          h += `<tr><td>${x.date ? (x.date.slice(5) + ' ') : ''}${x.timestamp}</td><td style="color:var(--cyan);font-weight:700">${x.download.mbps} Mbps</td><td style="color:var(--purple);font-weight:700">${x.upload.mbps} Mbps</td><td>${x.ping.avg} ms</td><td><span style="color:var(--green);font-weight:600">${x.rating}</span></td></tr>`;
        }
        document.getElementById('histBody').innerHTML = h;
      }
    }
    if(d.stats){
      renderExtremes(d.stats);
    }
    if(d.interval_min !== undefined){
      const sel = document.getElementById('intervalSel');
      if(document.activeElement !== sel){
        sel.value = d.interval_min;
      }
      const sched = document.getElementById('schedPill');
      if(d.interval_min === 0){
        sched.innerText = 'Auto-test: Off';
      }else if(d.next_test_in_s !== null && d.next_test_in_s !== undefined){
        const m = Math.floor(d.next_test_in_s / 60);
        const s = d.next_test_in_s % 60;
        sched.innerText = `Next: ${m}m ${s}s`;
      }else{
        sched.innerText = `Auto-test: ${d.interval_min}m`;
      }
    }

    const btn = document.getElementById('runBtn');
    const pill = document.getElementById('statusPill');
    const txt = document.getElementById('statusTxt');
    if(d.is_running){
      btn.disabled = true;
      btn.querySelector('span').innerText = 'Testing in progress...';
      pill.className = 'pill busy';
      txt.innerText = 'Testing...';
      if(!polling){ polling = setInterval(fetchStatus, 2000); }
    }else{
      btn.disabled = false;
      btn.querySelector('span').innerText = 'Start Speed Test';
      pill.className = 'pill';
      txt.innerText = 'Ready';
      if(polling){ clearInterval(polling); polling = false; }
    }
  }catch(e){ console.error(e); }
}

function renderExtremes(s){
  const td = s.today || {};
  if(td.date) document.getElementById('tdTag').innerText = td.date;
  if(td.count > 0){
    document.getElementById('tdDownMax').innerText = td.down_max;
    document.getElementById('tdDownMin').innerText = td.down_min;
    document.getElementById('tdUpMax').innerText = td.up_max;
    document.getElementById('tdUpMin').innerText = td.up_min;
    document.getElementById('tdPingMin').innerText = td.ping_min;
    document.getElementById('tdPingMax').innerText = td.ping_max;
    const avgD = (td.down_sum / td.count).toFixed(1);
    const avgU = (td.up_sum / td.count).toFixed(1);
    document.getElementById('tdSummary').innerText = `Avg: ${avgD} Mbps down, ${avgU} Mbps up | Total: ${td.count} tests`;
  }

  const mo = s.month || {};
  if(mo.month) document.getElementById('moTag').innerText = mo.month;
  if(mo.count > 0){
    document.getElementById('moDownMax').innerText = mo.down_max;
    document.getElementById('moDownMin').innerText = mo.down_min;
    document.getElementById('moUpMax').innerText = mo.up_max;
    document.getElementById('moUpMin').innerText = mo.up_min;
    document.getElementById('moPingMin').innerText = mo.ping_min;
    document.getElementById('moPingMax').innerText = mo.ping_max;
    const avgD = (mo.down_sum / mo.count).toFixed(1);
    const avgU = (mo.up_sum / mo.count).toFixed(1);
    document.getElementById('moSummary').innerText = `Avg: ${avgD} Mbps down, ${avgU} Mbps up | Total: ${mo.count} tests`;
  }
}

async function triggerTest(){
  const btn = document.getElementById('runBtn');
  btn.disabled = true;
  btn.querySelector('span').innerText = 'Running speed test...';
  const pill = document.getElementById('statusPill');
  pill.className = 'pill busy';
  document.getElementById('statusTxt').innerText = 'Testing...';
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
    if(attempts > 12){
      clearInterval(pollInterval);
      fetchStatus();
    }
  }, 2500);
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

async function saveWifi(){
  const s = document.getElementById('ssid').value;
  const p = document.getElementById('pw').value;
  if(!s){ alert('Please enter SSID'); return; }
  const msg = document.getElementById('saveMsg');
  msg.innerText = 'Saving credentials and restarting Wi-Fi...';
  await fetch('/api/config', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ssid:s, password:p})
  });
}

fetchStatus();
setInterval(fetchStatus, 8000);
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
        print(f"Web server started on port {port}")

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
                data = {
                    "wifi": self.tester.get_wifi_info(),
                    "is_running": self.tester.is_running,
                    "last": self.tester.last_result,
                    "history": self.tester.history,
                    "stats": getattr(self.tester, "stats", {}),
                    "interval_min": self.config_manager.config.get("auto_test_interval_min", 30),
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
