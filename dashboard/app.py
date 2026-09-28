# dashboard/app.py
import os
import json
import glob
from flask import Flask, jsonify, render_template_string
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

def get_latest_report() -> dict:
    """Load the most recent report from the reports/ folder."""
    reports = glob.glob("reports/report_*.json")
    if not reports:
        return None
    latest = max(reports, key=os.path.getctime)
    with open(latest) as f:
        return json.load(f)

def get_all_reports() -> list:
    """Load all reports for history chart."""
    reports = glob.glob("reports/report_*.json")
    reports.sort()
    history = []
    for r in reports[-10:]:  # last 10 reports
        with open(r) as f:
            data = json.load(f)
            history.append({
                "timestamp":    data.get("timestamp", "")[:16],
                "health_score": data.get("health_score", 0),
            })
    return history

@app.route("/api/report")
def api_report():
    report = get_latest_report()
    if not report:
        return jsonify({"error": "No reports found. Run main.py first."}), 404
    report["history"] = get_all_reports()
    return jsonify(report)

@app.route("/api/run")
def api_run():
    """Trigger a fresh DriftWatch scan."""
    import subprocess
    subprocess.Popen(["python", "main.py"])
    return jsonify({"status": "scan started"})

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DriftWatch — Infrastructure Intelligence</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #0d1117; color: #e6edf3; min-height: 100vh; }

  .header { background: #161b22; border-bottom: 1px solid #30363d;
            padding: 16px 32px; display: flex; align-items: center;
            justify-content: space-between; }
  .logo { font-size: 20px; font-weight: 700; color: #58a6ff; }
  .logo span { color: #e6edf3; }
  .run-btn { background: #238636; color: #fff; border: none;
             padding: 8px 20px; border-radius: 6px; cursor: pointer;
             font-size: 14px; font-weight: 600; }
  .run-btn:hover { background: #2ea043; }

  .container { max-width: 1200px; margin: 0 auto; padding: 32px; }

  .grid-top { display: grid; grid-template-columns: 280px 1fr; gap: 24px;
              margin-bottom: 24px; }
  .grid-mid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
              margin-bottom: 24px; }

  .card { background: #161b22; border: 1px solid #30363d;
          border-radius: 12px; padding: 24px; }
  .card h2 { font-size: 13px; font-weight: 600; color: #8b949e;
             text-transform: uppercase; letter-spacing: 0.5px;
             margin-bottom: 16px; }

  /* Health Score */
  .score-ring { text-align: center; padding: 8px 0; }
  .score-number { font-size: 64px; font-weight: 700; line-height: 1; }
  .score-label { font-size: 13px; color: #8b949e; margin-top: 8px; }
  .score-bar { height: 8px; background: #21262d; border-radius: 4px;
               margin-top: 16px; overflow: hidden; }
  .score-fill { height: 100%; border-radius: 4px;
                transition: width 0.8s ease; }

  /* Risk items */
  .risk-item { background: #0d1117; border: 1px solid #30363d;
               border-radius: 8px; padding: 14px; margin-bottom: 10px; }
  .risk-header { display: flex; justify-content: space-between;
                 align-items: flex-start; margin-bottom: 6px; }
  .risk-text { font-size: 14px; flex: 1; margin-right: 12px; }
  .badge { font-size: 11px; font-weight: 600; padding: 2px 8px;
           border-radius: 12px; white-space: nowrap; }
  .badge-critical { background: #3d1c1c; color: #f85149; }
  .badge-high     { background: #2d1f00; color: #d29922; }
  .badge-medium   { background: #1c2d1c; color: #3fb950; }
  .badge-low      { background: #1c2433; color: #58a6ff; }

  /* Action plan */
  .action-item { display: flex; gap: 14px; margin-bottom: 14px;
                 padding-bottom: 14px; border-bottom: 1px solid #21262d; }
  .action-num { width: 28px; height: 28px; background: #238636;
                border-radius: 50%; display: flex; align-items: center;
                justify-content: center; font-size: 13px; font-weight: 700;
                flex-shrink: 0; }
  .action-text { font-size: 14px; line-height: 1.5; }
  .action-meta { display: flex; gap: 8px; margin-top: 6px; flex-wrap: wrap; }
  .meta-tag { font-size: 11px; background: #21262d; padding: 2px 8px;
              border-radius: 4px; color: #8b949e; }

  /* Digest */
  .digest-text { font-size: 15px; line-height: 1.7; color: #c9d1d9; }

  /* Issues */
  .issue-item { display: flex; align-items: center; gap: 10px;
                padding: 10px 0; border-bottom: 1px solid #21262d; }
  .issue-icon { color: #3fb950; font-size: 16px; }
  .issue-link { color: #58a6ff; text-decoration: none; font-size: 14px; }
  .issue-link:hover { text-decoration: underline; }

  /* Chart */
  .chart-container { height: 200px; }

  /* Timestamp */
  .timestamp { font-size: 12px; color: #8b949e; text-align: right;
               margin-bottom: 24px; }

  .loading { text-align: center; padding: 80px; color: #8b949e; }
  .error   { color: #f85149; text-align: center; padding: 40px; }
</style>
</head>
<body>

<div class="header">
  <div class="logo">🌊 Drift<span>Watch</span></div>
  <button class="run-btn" onclick="triggerScan()">▶ Run New Scan</button>
</div>

<div class="container">
  <div id="app"><div class="loading">⏳ Loading DriftWatch data...</div></div>
</div>

<script>
async function loadReport() {
  try {
    const res = await fetch('/api/report');
    if (!res.ok) throw new Error('No report found. Run main.py first.');
    const data = await res.json();
    renderDashboard(data);
  } catch (e) {
    document.getElementById('app').innerHTML =
      `<div class="error">❌ ${e.message}</div>`;
  }
}

function getScoreColor(score) {
  if (score >= 80) return '#3fb950';
  if (score >= 60) return '#d29922';
  if (score >= 40) return '#f0883e';
  return '#f85149';
}

function getBadgeClass(level) {
  const l = (level || '').toUpperCase();
  if (l.includes('CRITICAL')) return 'badge-critical';
  if (l.includes('HIGH'))     return 'badge-high';
  if (l.includes('MEDIUM'))   return 'badge-medium';
  return 'badge-low';
}

function parseActionPlan(strategy) {
  const actions = [];
  const lines = strategy.split('\\n');
  let current = null;
  for (const line of lines) {
    const trimmed = line.trim();
    if (/^\\d+\\.\\s+ACTION:/.test(trimmed)) {
      if (current) actions.push(current);
      current = { action: trimmed.replace(/^\\d+\\.\\s+ACTION:/, '').trim(),
                  effort: '', impact: '', timeline: '', why: '' };
    } else if (current) {
      if (trimmed.startsWith('EFFORT:'))   current.effort   = trimmed.replace('EFFORT:', '').trim();
      if (trimmed.startsWith('IMPACT:'))   current.impact   = trimmed.replace('IMPACT:', '').trim();
      if (trimmed.startsWith('TIMELINE:')) current.timeline = trimmed.replace('TIMELINE:', '').trim();
      if (trimmed.startsWith('WHY:'))      current.why      = trimmed.replace('WHY:', '').trim();
      if (trimmed.startsWith('GITHUB_ISSUES')) { if (current) actions.push(current); current = null; break; }
    }
  }
  if (current) actions.push(current);
  return actions.slice(0, 3);
}

function parseRisks(analysis) {
  const risks = [];
  const lines = analysis.split('\\n');
  let current = null;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('- RISK:')) {
      if (current) risks.push(current);
      current = { risk: trimmed.replace('- RISK:', '').trim(), blast: 'LOW', urgency: '' };
    } else if (current) {
      if (trimmed.startsWith('BLAST_RADIUS:')) current.blast   = trimmed.replace('BLAST_RADIUS:', '').trim();
      if (trimmed.startsWith('URGENCY:'))      current.urgency = trimmed.replace('URGENCY:', '').trim();
      if (trimmed.startsWith('TOP_PRIORITY'))  { if (current) risks.push(current); current = null; break; }
    }
  }
  if (current) risks.push(current);
  return risks;
}

function renderDashboard(data) {
  const score    = data.health_score || 0;
  const color    = getScoreColor(score);
  const risks    = parseRisks(data.analysis || '');
  const actions  = parseActionPlan(data.strategy || '');
  const digest   = data.weekly_digest || 'No digest available.';
  const issues   = data.issues_created || [];
  const history  = data.history || [];
  const ts       = (data.timestamp || '').replace('T', ' ').slice(0, 16);

  const risksHTML = risks.length
    ? risks.map(r => `
        <div class="risk-item">
          <div class="risk-header">
            <div class="risk-text">${r.risk}</div>
            <span class="badge ${getBadgeClass(r.blast)}">${r.blast}</span>
          </div>
          <span class="badge badge-low">${r.urgency}</span>
        </div>`).join('')
    : '<p style="color:#8b949e;font-size:14px">No compound risks identified.</p>';

  const actionsHTML = actions.length
    ? actions.map((a, i) => `
        <div class="action-item">
          <div class="action-num">${i+1}</div>
          <div>
            <div class="action-text">${a.action}</div>
            <div class="action-meta">
              <span class="meta-tag">⚡ Effort: ${a.effort}</span>
              <span class="meta-tag">🎯 Impact: ${a.impact}</span>
              <span class="meta-tag">📅 ${a.timeline}</span>
            </div>
            ${a.why ? `<div style="font-size:13px;color:#8b949e;margin-top:6px">${a.why}</div>` : ''}
          </div>
        </div>`).join('')
    : '<p style="color:#8b949e;font-size:14px">No actions found.</p>';

  const issuesHTML = issues.filter(i => i.created).length
    ? issues.filter(i => i.created).map(i =>
        `<div class="issue-item">
           <span class="issue-icon">●</span>
           <a class="issue-link" href="${i.url}" target="_blank">
             #${i.number} — Auto-created by DriftWatch</a>
         </div>`).join('')
    : '<p style="color:#8b949e;font-size:14px">No issues created this run.</p>';

  document.getElementById('app').innerHTML = `
    <div class="timestamp">Last scan: ${ts}</div>

    <div class="grid-top">
      <div class="card">
        <h2>Health Score</h2>
        <div class="score-ring">
          <div class="score-number" style="color:${color}">${score}</div>
          <div class="score-label">out of 100</div>
          <div class="score-bar">
            <div class="score-fill" style="width:${score}%;background:${color}"></div>
          </div>
        </div>
      </div>
      <div class="card">
        <h2>Health Score History</h2>
        <div class="chart-container">
          <canvas id="historyChart"></canvas>
        </div>
      </div>
    </div>

    <div class="grid-mid">
      <div class="card">
        <h2>Compound Risks</h2>
        ${risksHTML}
      </div>
      <div class="card">
        <h2>Strategic Action Plan</h2>
        ${actionsHTML}
      </div>
    </div>

    <div class="grid-mid">
      <div class="card">
        <h2>Weekly Digest</h2>
        <div class="digest-text">${digest}</div>
      </div>
      <div class="card">
        <h2>GitHub Issues Created</h2>
        ${issuesHTML}
      </div>
    </div>
  `;

  // Draw history chart
  if (history.length > 1) {
    const ctx = document.getElementById('historyChart').getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: history.map(h => h.timestamp.slice(11)),
        datasets: [{
          label: 'Health Score',
          data: history.map(h => h.health_score),
          borderColor: '#58a6ff',
          backgroundColor: 'rgba(88,166,255,0.1)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: history.map(h => getScoreColor(h.health_score)),
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 100, grid: { color: '#21262d' },
               ticks: { color: '#8b949e' } },
          x: { grid: { color: '#21262d' }, ticks: { color: '#8b949e' } }
        }
      }
    });
  } else {
    const ctx = document.getElementById('historyChart');
    if (ctx) ctx.parentElement.innerHTML =
      '<p style="color:#8b949e;font-size:13px;padding-top:70px;text-align:center">Run 2+ scans to see history chart</p>';
  }
}

async function triggerScan() {
  const btn = document.querySelector('.run-btn');
  btn.textContent = '⏳ Scanning...';
  btn.disabled = true;
  await fetch('/api/run');
  setTimeout(() => {
    btn.textContent = '▶ Run New Scan';
    btn.disabled = false;
    loadReport();
  }, 45000); // wait ~45s for scan to complete
}

loadReport();
</script>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)

if __name__ == "__main__":
    print("🌊 DriftWatch Dashboard running at http://localhost:5000")
    app.run(debug=True, port=5000)