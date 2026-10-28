from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import os
from urllib.parse import parse_qs, urlparse
from datetime import datetime
import csv
import html
import io
import math
import pickle

HOST = "0.0.0.0"  # Required for cloud hosting
PORT = int(os.environ.get("PORT", "8000"))
MODEL_FILE = Path(__file__).with_name("city_model.pkl")

# The app can use the saved model made by train_model.py. If the saved model
# is unavailable or has another format, the dashboard remains available in demo mode.
MODEL_WEIGHTS = [0.9, 1.1, 1.0, 0.8, 1.0]
MODEL_BIAS = -1.8
MODEL_STATUS = "DEMO SCORING MODE — city_model.pkl could not be loaded"
try:
    with MODEL_FILE.open("rb") as model_file:
        saved_model = pickle.load(model_file)
    if isinstance(saved_model, dict):
        loaded_weights = saved_model.get("weights")
        loaded_bias = saved_model.get("bias")
    else:
        loaded_weights = getattr(saved_model, "weights", None)
        loaded_bias = getattr(saved_model, "bias", None)
    if loaded_weights is None or loaded_bias is None or len(loaded_weights) < 5:
        raise ValueError("Expected five model weights and a bias value")
    MODEL_WEIGHTS = [float(value) for value in loaded_weights[:5]]
    MODEL_BIAS = float(loaded_bias)
    MODEL_STATUS = "MODEL LOADED · city_model.pkl"
except Exception as exc:
    print("Model loading note:", exc)
    print("Running with clearly labelled demo scoring until a compatible model is available.")

# Recent results and alerts stay in memory while the server is running.
# This is a prototype, not a persistent municipal database.
ASSESSMENTS = []
NEXT_ID = 1


def predict(rainfall, traffic, road_age, complaints, maintenance_gap):
    normalized_values = [
        rainfall / 150.0,
        traffic / 100.0,
        road_age / 15.0,
        complaints / 20.0,
        maintenance_gap / 20.0,
    ]
    z = MODEL_BIAS + sum(w * value for w, value in zip(MODEL_WEIGHTS, normalized_values))
    z = max(-60.0, min(60.0, z))
    return round(100.0 / (1.0 + math.exp(-z)), 1)


def factor_level(value, medium, high):
    if value >= high:
        return "HIGH"
    if value >= medium:
        return "MEDIUM"
    return "LOW"


def safe_number(form, key, default, minimum, maximum):
    try:
        value = float(form.get(key, [str(default)])[0])
        if not math.isfinite(value):
            raise ValueError("Number must be finite")
    except (TypeError, ValueError, OverflowError):
        value = float(default)
    return max(float(minimum), min(float(maximum), value))


def risk_details(probability):
    if probability >= 75:
        risk, color, action, priority = (
            "CRITICAL", "#fb7185",
            "Arrange an urgent on-site inspection and prioritise immediate protective maintenance.",
            "EMERGENCY",
        )
    elif probability >= 50:
        risk, color, action, priority = (
            "HIGH", "#fb923c",
            "Schedule an urgent site inspection and prepare a repair or mitigation plan.",
            "HIGH PRIORITY",
        )
    elif probability >= 30:
        risk, color, action, priority = (
            "MODERATE", "#fbbf24",
            "Inspect the location soon, record observations, and monitor changing conditions.",
            "MEDIUM PRIORITY",
        )
    else:
        risk, color, action, priority = (
            "LOW", "#34d399",
            "Continue routine monitoring and follow the planned maintenance schedule.",
            "ROUTINE",
        )
    return risk, color, action, priority


def route_department(values):
    rainfall, traffic, road_age, complaints, maintenance_gap = values
    # Route to the most relevant service desk using transparent prototype rules.
    candidates = [
        (rainfall / 150.0, "Drainage & Flood Management", "Rainfall is a notable factor in this assessment."),
        (traffic / 100.0, "Traffic Management Department", "Traffic intensity is a notable factor in this assessment."),
        (road_age / 15.0, "Roads & Infrastructure Department", "Road age is a notable factor in this assessment."),
        (complaints / 20.0, "Public Grievance Cell", "Previous complaints are a notable factor in this assessment."),
        (maintenance_gap / 20.0, "Infrastructure Maintenance Department", "Time since the last maintenance is a notable factor in this assessment."),
    ]
    score, department, reason = max(candidates, key=lambda item: item[0])
    if score < 0.25:
        return "City Monitoring Department", "No single input stands out; routine monitoring is suggested."
    return department, reason


def make_assessment(values):
    global NEXT_ID
    rainfall, traffic, road_age, complaints, maintenance_gap = values
    probability = predict(*values)
    risk, color, action, priority = risk_details(probability)
    department, routing_reason = route_department(values)
    factors = [
        ("Rainfall", rainfall, "mm", factor_level(rainfall, 30, 70)),
        ("Traffic intensity", traffic, "%", factor_level(traffic, 40, 75)),
        ("Road age", road_age, "years", factor_level(road_age, 5, 10)),
        ("Previous complaints", complaints, "", factor_level(complaints, 5, 10)),
        ("Maintenance gap", maintenance_gap, "months", factor_level(maintenance_gap, 5, 10)),
    ]
    record = {
        "id": NEXT_ID,
        "time": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "values": list(values),
        "probability": probability,
        "risk": risk,
        "color": color,
        "action": action,
        "priority": priority,
        "department": department,
        "routing_reason": routing_reason,
        "factors": factors,
    }
    NEXT_ID += 1
    ASSESSMENTS.insert(0, record)
    del ASSESSMENTS[100:]
    return record


def esc(value):
    return html.escape(str(value), quote=True)


CSS = r'''<style>
:root{color-scheme:dark;--bg:#08111f;--panel:#101c2e;--panel2:#0c1727;--line:#263750;--muted:#9aacc5;--text:#eff6ff;--blue:#58b7ff;--blue2:#267ee8;--green:#34d399;--red:#fb7185;--orange:#fb923c;--yellow:#fbbf24}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 88% -10%,#17365a 0,transparent 33%),var(--bg);font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--text);font-size:14px}a{color:inherit;text-decoration:none}button,input{font:inherit}.app{min-height:100vh;display:grid;grid-template-columns:248px minmax(0,1fr)}.sidebar{position:sticky;top:0;height:100vh;border-right:1px solid var(--line);background:rgba(7,16,29,.92);padding:24px 16px;display:flex;flex-direction:column;gap:28px}.brand{display:flex;align-items:center;gap:12px;padding:0 8px}.brand-icon{width:43px;height:43px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(140deg,#177add,#25bad1);font-size:24px;box-shadow:0 8px 22px #137cd733}.brand-name{font-size:15px;font-weight:800;letter-spacing:.1px}.brand-sub{font-size:10px;color:var(--muted);margin-top:4px;letter-spacing:1.1px;text-transform:uppercase}.nav-label{font-size:10px;letter-spacing:1.5px;font-weight:800;color:#657a97;padding:0 12px;margin:0 0 8px}.nav{display:grid;gap:6px}.nav a{display:flex;align-items:center;gap:12px;padding:12px;border-radius:11px;color:#9eb0c9;font-weight:600;transition:.15s}.nav a:hover{background:#13253c;color:white}.nav a.active{background:linear-gradient(90deg,#153e66,#122c48);color:#bde5ff;border:1px solid #235a86}.nav-icon{font-size:17px;width:22px;text-align:center}.sidebar-bottom{margin-top:auto}.prototype-note{border:1px solid var(--line);background:#0d192a;border-radius:13px;padding:13px;color:var(--muted);font-size:11px;line-height:1.6}.prototype-note b{display:block;color:#dcecff;font-size:12px;margin-bottom:5px}.main{min-width:0}.topbar{height:76px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:20px;padding:0 34px;background:rgba(8,17,31,.65);backdrop-filter:blur(10px)}.crumb{font-size:12px;color:var(--muted)}.crumb b{color:var(--text)}.top-right{display:flex;align-items:center;gap:12px}.status-dot{display:inline-flex;align-items:center;gap:8px;border:1px solid #255773;background:#0d2a3a;color:#9fe4ff;padding:8px 11px;border-radius:999px;font-size:10px;font-weight:800;letter-spacing:.5px}.dot{width:7px;height:7px;border-radius:50%;background:#34d399;box-shadow:0 0 0 4px #34d39920}.avatar{width:34px;height:34px;border-radius:11px;background:#203751;color:#bde5ff;display:grid;place-items:center;font-weight:800}.content{max-width:1500px;margin:auto;padding:30px 34px 42px}.page-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;margin-bottom:24px}.eyebrow{text-transform:uppercase;letter-spacing:1.8px;font-size:10px;font-weight:900;color:#70c8ff;margin-bottom:9px}.page-heading h1{margin:0;font-size:clamp(25px,3vw,32px);letter-spacing:-.7px}.page-heading p{margin:9px 0 0;color:var(--muted);line-height:1.6;max-width:680px}.btn{display:inline-flex;justify-content:center;align-items:center;gap:8px;border:1px solid #347cba;background:linear-gradient(100deg,#176fd0,#178ec0);padding:11px 15px;color:white;border-radius:10px;font-weight:800;font-size:12px;cursor:pointer}.btn:hover{filter:brightness(1.1)}.btn.secondary{background:#13243a;border-color:#30445f;color:#d7eaff}.btn.ghost{background:transparent;border-color:var(--line);color:#c4d6ed}.cards{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:18px}.panel,.metric{background:linear-gradient(160deg,rgba(18,31,51,.97),rgba(13,24,41,.97));border:1px solid var(--line);border-radius:16px;box-shadow:0 14px 34px #00000012}.metric{padding:19px}.metric-top{display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px;gap:9px}.metric-icon{width:34px;height:34px;display:grid;place-items:center;border-radius:10px;background:#183653;color:#9ddcff;font-size:16px}.metric-number{font-size:30px;font-weight:850;margin:15px 0 5px;letter-spacing:-1px}.metric-foot{font-size:11px;color:#8197b4;line-height:1.5}.metric-foot strong{color:#9be8c2}.content-grid{display:grid;grid-template-columns:minmax(0,1.28fr) minmax(280px,.82fr);gap:18px;align-items:start}.panel{padding:21px;margin-bottom:18px}.panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:18px}.panel-head h2{font-size:16px;margin:0}.panel-head p{font-size:12px;line-height:1.5;color:var(--muted);margin:7px 0 0}.pill{border-radius:999px;padding:6px 9px;background:#1a2b42;color:#c4d5eb;font-size:10px;font-weight:900;white-space:nowrap}.pill.LOW{background:#15392f;color:#8ef0bd}.pill.MODERATE{background:#44381b;color:#ffdb80}.pill.HIGH{background:#4b2d1c;color:#ffc096}.pill.CRITICAL{background:#4b202d;color:#ffabb8}.hero{padding:25px;background:linear-gradient(120deg,#12345b,#12223a 60%,#10273b);border:1px solid #285477;border-radius:17px;margin-bottom:19px;display:flex;justify-content:space-between;align-items:center;gap:20px;overflow:hidden;position:relative}.hero:after{content:'⌖';font-size:140px;color:#5ebcff10;position:absolute;right:25px;top:-30px}.hero-copy{position:relative;z-index:1;max-width:630px}.hero h2{font-size:22px;margin:0 0 9px}.hero p{color:#b3c7df;line-height:1.7;margin:0 0 17px;font-size:13px}.hero-actions{display:flex;gap:9px;flex-wrap:wrap}.hero-stat{position:relative;z-index:1;min-width:130px;text-align:center;padding:12px 16px;border-left:1px solid #49708e}.hero-stat strong{display:block;font-size:31px}.hero-stat span{font-size:10px;text-transform:uppercase;letter-spacing:1px;color:#a5c8e9}.quick-items{display:grid;gap:11px}.quick-item{display:flex;gap:12px;align-items:flex-start;padding:12px;border-radius:12px;background:#0c1728;border:1px solid #233750}.quick-icon{width:34px;height:34px;flex:none;border-radius:10px;background:#172e49;display:grid;place-items:center;font-size:16px}.quick-item b{display:block;font-size:12px;margin:1px 0 5px}.quick-item span{font-size:11px;color:var(--muted);line-height:1.5}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;white-space:nowrap}th{text-align:left;color:#8298b4;font-size:10px;text-transform:uppercase;letter-spacing:1px;font-weight:800;padding:11px 10px;border-bottom:1px solid var(--line)}td{padding:13px 10px;border-bottom:1px solid #1f3046;color:#d8e5f6;font-size:12px}tbody tr:last-child td{border-bottom:0}.muted{color:var(--muted)}.small-tag{font-size:9px;letter-spacing:.6px;font-weight:900;padding:5px 7px;border-radius:6px;background:#1b2b40;color:#d4e3f7}.riskbar{height:9px;background:#21344c;border-radius:99px;overflow:hidden;margin:14px 0 7px}.riskbar div{height:100%;border-radius:99px}.bar-rows{display:grid;gap:15px}.bar-row-head{display:flex;justify-content:space-between;gap:15px;margin-bottom:7px;font-size:12px}.bar-row-head span:last-child{color:var(--muted)}.empty{padding:28px 15px;text-align:center;color:var(--muted);line-height:1.7}.empty-icon{font-size:28px;margin-bottom:8px}.form-layout{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:18px;align-items:start}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:5px 14px}.field{margin:10px 0 13px}.field-top{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px;font-size:12px}.range{color:#7ec9ff;font-weight:800;font-size:11px}.field input{width:100%;padding:12px;border:1px solid #354b67;border-radius:10px;background:#091525;color:var(--text);outline:none}.field input:focus{border-color:var(--blue);box-shadow:0 0 0 3px #58b7ff18}.field small{display:block;margin-top:6px;font-size:10px;color:#8398b4;line-height:1.45}.full{grid-column:1/-1}.submit-row{margin-top:8px}.submit-row .btn{width:100%;padding:14px}.risk-score{font-size:54px;font-weight:900;letter-spacing:-2px;margin:18px 0 2px}.risk-score small{font-size:18px;letter-spacing:0;color:var(--muted)}.meter{height:11px;background:#26364e;border-radius:20px;overflow:hidden;margin:17px 0 8px}.meter-fill{height:100%;border-radius:20px}.meter-labels{display:flex;justify-content:space-between;color:var(--muted);font-size:10px}.factor{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:12px 0;border-bottom:1px solid #26364e;font-size:12px}.factor:last-child{border-bottom:0}.level{font-size:9px;font-weight:900;border-radius:6px;padding:5px 7px}.level-HIGH{color:#ffabb8;background:#4a2029}.level-MEDIUM{color:#ffdc91;background:#45391b}.level-LOW{color:#98f0bb;background:#173d32}.action-box{padding:15px;border-radius:12px;margin-top:15px;background:#0b1729;border:1px solid var(--line);line-height:1.65;font-size:12px}.action-box strong{display:block;margin-bottom:5px}.alert-box{margin-top:12px;padding:15px;border-radius:12px;background:#172438;border:1px solid var(--line);font-size:12px;line-height:1.7}.alert-box strong{display:block;margin-bottom:5px}.note{border-left:3px solid #3ba6ea;padding:10px 13px;color:#9eb4cf;font-size:11px;line-height:1.65;background:#0c1929;border-radius:0 9px 9px 0;margin-top:14px}.detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.detail{padding:13px;border:1px solid var(--line);background:#0b1727;border-radius:11px}.detail span{display:block;color:var(--muted);font-size:10px;margin-bottom:7px}.detail b{font-size:13px}.step-list{display:grid;gap:12px}.step{display:flex;gap:12px}.step-num{height:27px;width:27px;flex:none;border-radius:9px;background:#173958;color:#9bdcff;display:grid;place-items:center;font-weight:900}.step b{display:block;font-size:12px;margin:2px 0 5px}.step p{margin:0;color:var(--muted);font-size:11px;line-height:1.55}.footer{padding:16px 34px 28px;color:#71839d;font-size:10px;text-align:center}.notice{border:1px solid #5d4b25;background:#2d2719;color:#f5d88d;padding:12px 14px;border-radius:11px;font-size:11px;line-height:1.6;margin-bottom:18px}
@media(max-width:1120px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.content-grid,.form-layout{grid-template-columns:1fr}.sidebar{width:225px}.app{grid-template-columns:225px minmax(0,1fr)}.hero-stat{min-width:100px}}
@media(max-width:760px){.app{display:block}.sidebar{position:relative;height:auto;width:auto;padding:14px;gap:15px;border-right:0;border-bottom:1px solid var(--line)}.brand{padding:0 4px}.nav-label,.sidebar-bottom{display:none}.nav{display:flex;overflow-x:auto}.nav a{padding:10px;flex:none;font-size:11px}.nav-icon{width:auto}.topbar{height:auto;min-height:62px;padding:13px 17px}.top-right .status-dot{max-width:190px;overflow:hidden;text-overflow:ellipsis}.content{padding:22px 15px}.page-heading{flex-direction:column}.hero{align-items:flex-start;flex-direction:column;padding:20px}.hero-stat{border-left:0;border-top:1px solid #49708e;padding:12px 0 0;width:100%;text-align:left}.cards{gap:10px}.metric{padding:14px}.metric-number{font-size:25px}.panel{padding:16px}.form-grid{grid-template-columns:1fr}.full{grid-column:auto}.footer{padding:15px}.avatar{display:none}}
@media(max-width:420px){.cards{grid-template-columns:1fr 1fr}.metric-top{align-items:flex-start;flex-direction:column}.metric-icon{order:-1}.metric-number{font-size:23px}.status-dot{font-size:8px}.brand-name{font-size:13px}.topbar{gap:7px}}
</style>'''


def nav_link(path, current, icon, label):
    active = " active" if current == path or (path == "/dashboard" and current == "/") else ""
    return f'<a class="{active.strip()}" href="{path}"><span class="nav-icon">{icon}</span><span>{label}</span></a>'


def shell(title, subtitle, current, body, action=""):
    nav = ''.join([
        nav_link("/dashboard", current, "▦", "Overview"),
        nav_link("/predict", current, "⌁", "Risk Predictor"),
        nav_link("/alerts", current, "♧", "Department Alerts"),
        nav_link("/reports", current, "▤", "Reports & History"),
        nav_link("/guide", current, "ⓘ", "System Guide"),
    ])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} · AI City Problem Predictor</title>{CSS}</head><body><div class="app">
<aside class="sidebar"><div class="brand"><div class="brand-icon">⌁</div><div><div class="brand-name">AI City Predictor</div><div class="brand-sub">Smart city intelligence</div></div></div>
<div><div class="nav-label">WORKSPACE</div><nav class="nav">{nav}</nav></div>
<div class="sidebar-bottom"><div class="prototype-note"><b>◈ Prototype environment</b>Assessment results and generated alerts are kept in memory while this local app runs. No external messages are sent.</div></div></aside>
<div class="main"><div class="topbar"><div class="crumb">Smart City <span class="muted">/</span> <b>{esc(title)}</b></div><div class="top-right"><span class="status-dot"><span class="dot"></span>{esc(MODEL_STATUS)}</span><div class="avatar">AI</div></div></div>
<main class="content"><div class="page-heading"><div><div class="eyebrow">MISSION 05 · SMART CITY</div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>{action}</div>{body}</main><div class="footer">AI City Problem Predictor · Hackathon prototype · Use predictions for prioritisation only; confirm risks through on-site inspection.</div></div></div></body></html>'''.encode("utf-8")


def assessment_rows(records, limit=6):
    if not records:
        return '<tr><td colspan="6"><div class="empty"><div class="empty-icon">⌖</div><b>No assessments yet</b><br>Run a prediction to build your local history.</div></td></tr>'
    rows = []
    for item in records[:limit]:
        rows.append('<tr>'
                    f'<td><b>CP-{item["id"]:04d}</b></td>'
                    f'<td>{esc(item["time"])}</td>'
                    f'<td><b>{item["probability"]:.1f}%</b></td>'
                    f'<td><span class="pill {esc(item["risk"])}">{esc(item["risk"])}</span></td>'
                    f'<td>{esc(item["department"])}</td>'
                    f'<td><span class="small-tag">{esc(item["priority"])}</span></td></tr>')
    return ''.join(rows)


def distribution_html(records):
    total = len(records)
    groups = [("Low", "LOW", "#34d399"), ("Moderate", "MODERATE", "#fbbf24"),
              ("High", "HIGH", "#fb923c"), ("Critical", "CRITICAL", "#fb7185")]
    output = []
    for label, key, color in groups:
        count = sum(1 for item in records if item["risk"] == key)
        width = round((count / total) * 100) if total else 0
        output.append(f'<div><div class="bar-row-head"><span>{label} risk</span><span>{count} assessment(s)</span></div><div class="riskbar"><div style="width:{width}%;background:{color}"></div></div></div>')
    return ''.join(output)


def dashboard_page():
    total = len(ASSESSMENTS)
    high_count = sum(1 for item in ASSESSMENTS if item["risk"] in ("HIGH", "CRITICAL"))
    alerts = sum(1 for item in ASSESSMENTS if item["priority"] != "ROUTINE")
    latest = ASSESSMENTS[0] if ASSESSMENTS else None
    if latest:
        hero_stat = f'<div class="hero-stat"><strong>{latest["probability"]:.1f}%</strong><span>Latest risk score</span></div>'
        latest_summary = f'<span class="pill {esc(latest["risk"])}">{esc(latest["risk"])} RISK</span>'
        last_line = f'Your latest assessment CP-{latest["id"]:04d} is {latest["risk"].lower()} at {latest["probability"]:.1f}%. Review the recommendation and department routing.'
    else:
        hero_stat = '<div class="hero-stat"><strong>Ready</strong><span>Prediction engine</span></div>'
        latest_summary = '<span class="pill">NO PREDICTIONS YET</span>'
        last_line = 'No assessment has been saved in this running session. Start with the risk predictor to calculate a score and create an action recommendation.'
    body = f'''<section class="hero"><div class="hero-copy"><div class="eyebrow">CITY INFRASTRUCTURE MONITORING</div><h2>See risk earlier. Plan response smarter.</h2><p>Estimate infrastructure problem risk from rainfall, traffic, road age, previous complaints and the time since the last maintenance activity. Use the result to support inspection planning.</p><div class="hero-actions"><a class="btn" href="/predict">＋ New risk assessment</a><a class="btn secondary" href="/reports">View reports ↗</a></div></div>{hero_stat}</section>
<div class="cards">
<div class="metric"><div class="metric-top"><span>Total assessments</span><span class="metric-icon">▦</span></div><div class="metric-number">{total}</div><div class="metric-foot">Saved in this running session</div></div>
<div class="metric"><div class="metric-top"><span>High / critical risks</span><span class="metric-icon">⚠</span></div><div class="metric-number">{high_count}</div><div class="metric-foot">Assessments scoring 50% or above</div></div>
<div class="metric"><div class="metric-top"><span>Action alerts</span><span class="metric-icon">♧</span></div><div class="metric-number">{alerts}</div><div class="metric-foot">Suggested follow-up required</div></div>
<div class="metric"><div class="metric-top"><span>Model status</span><span class="metric-icon">✳</span></div><div class="metric-number" style="font-size:20px;color:#83d6ff">{'Loaded' if MODEL_STATUS.startswith('MODEL LOADED') else 'Demo mode'}</div><div class="metric-foot">{esc(MODEL_STATUS)}</div></div></div>
<div class="content-grid"><section class="panel"><div class="panel-head"><div><h2>Recent assessments</h2><p>Latest risk predictions created in this app session</p></div><a class="btn ghost" href="/reports">View all →</a></div><div class="table-wrap"><table><thead><tr><th>Reference</th><th>Time</th><th>Risk score</th><th>Level</th><th>Suggested department</th><th>Priority</th></tr></thead><tbody>{assessment_rows(ASSESSMENTS, 5)}</tbody></table></div></section>
<div><section class="panel"><div class="panel-head"><div><h2>Risk distribution</h2><p>Based on current session history</p></div><span class="pill">{total} TOTAL</span></div><div class="bar-rows">{distribution_html(ASSESSMENTS)}</div></section>
<section class="panel"><div class="panel-head"><div><h2>Latest assessment</h2><p>Next recommended step</p></div>{latest_summary}</div><div class="quick-items"><div class="quick-item"><div class="quick-icon">⌖</div><div><b>Assessment summary</b><span>{esc(last_line)}</span></div></div><div class="quick-item"><div class="quick-icon">♧</div><div><b>Department workflow</b><span>Each prediction suggests a responsible department and priority. This local prototype does not send external notifications.</span></div></div></div></section></div></div>'''
    return shell("Overview", "A single workspace for infrastructure risk checks, recommended actions and department follow-up.", "/dashboard", body)


def result_panel(record):
    factors = ''.join('<div class="factor"><span>' + esc(name) + ': <b>' + esc(f'{number:g}{(" " + unit) if unit else ""}') + '</b></span><span class="level level-' + esc(level) + '">' + esc(level) + '</span></div>' for name, number, unit, level in record["factors"])
    return f'''<section class="panel"><div class="panel-head"><div><h2>AI prediction result</h2><p>Assessment CP-{record["id"]:04d} · {esc(record["time"])}</p></div><span class="pill {esc(record["risk"])}">{esc(record["risk"])} RISK</span></div>
<div class="risk-score" style="color:{record["color"]}">{record["probability"]:.1f}<small>%</small></div><div class="meter"><div class="meter-fill" style="width:{record["probability"]}%;background:{record["color"]}"></div></div><div class="meter-labels"><span>LOW</span><span>MODERATE</span><span>HIGH</span></div>
<h3 class="section-title">Risk factor analysis</h3>{factors}<div class="action-box"><strong>Recommended action</strong>{esc(record["action"])}</div><div class="alert-box"><strong>Department alert · {esc(record["priority"])}</strong>Suggested department: <b>{esc(record["department"])}</b><br>{esc(record["routing_reason"])}<br>Alert status: <b>Generated in this dashboard</b><br><span class="muted">No actual SMS, phone call or external notification is sent by this prototype.</span></div></section>'''


def predictor_page(record=None, values=None):
    if values is None:
        values = [45.0, 55.0, 5.0, 3.0, 6.0]
    fields = [
        ("rainfall", "Rainfall", "mm", 0, 150, values[0], "Recent or forecast rainfall level"),
        ("traffic", "Traffic intensity", "%", 0, 100, values[1], "Estimated traffic load for the location"),
        ("road_age", "Road age", "years", 0, 15, values[2], "Approximate age of the road surface"),
        ("complaints", "Previous complaints", "", 0, 20, values[3], "Reported issues in the selected period"),
        ("maintenance_gap", "Maintenance gap", "months", 0, 20, values[4], "Months since the last maintenance activity"),
    ]
    inputs = []
    for key, label, unit, minimum, maximum, value, help_text in fields:
        label_text = f'{label} ({unit})' if unit else label
        inputs.append(f'''<div class="field"><div class="field-top"><label for="{key}">{esc(label_text)}</label><span class="range">{minimum}–{maximum}</span></div><input id="{key}" name="{key}" type="number" min="{minimum}" max="{maximum}" step="any" value="{value:g}" required><small>{esc(help_text)}</small></div>''')
    results = result_panel(record) if record else '''<section class="panel"><div class="empty"><div class="empty-icon">◉</div><h2>Prediction will appear here</h2><p>Enter the current conditions and select <b>Predict infrastructure risk</b>.<br>The dashboard will calculate a risk score, explain the factors, and suggest an action and department.</p></div><div class="note">Model results are estimates based on the saved model or clearly labelled demo scoring. They are not a substitute for field inspection or official risk assessment.</div></section>'''
    body = f'''<div class="form-layout"><section class="panel"><div class="panel-head"><div><h2>City risk assessment</h2><p>Enter numeric values for the selected location. Values are limited to the ranges shown.</p></div><span class="pill">5 INPUTS</span></div><form method="POST" action="/predict"><div class="form-grid">{''.join(inputs)}<div class="full submit-row"><button class="btn" type="submit">✳ &nbsp; Predict infrastructure risk</button></div></div></form><div class="note">Tip: use the same reporting period for complaint counts when comparing different locations. Example values are provided to make the prototype easy to test.</div></section><div>{results}</div></div>'''
    return shell("Risk Predictor", "Estimate infrastructure risk from five city-condition indicators and review a suggested response.", "/predict", body)


def alerts_page():
    nonroutine = [item for item in ASSESSMENTS if item["priority"] != "ROUTINE"]
    rows = []
    for item in nonroutine:
        rows.append(f'<tr><td><b>AL-{item["id"]:04d}</b></td><td>{esc(item["time"])}</td><td><span class="pill {esc(item["risk"])}">{esc(item["risk"])}</span></td><td>{esc(item["department"])}</td><td><span class="small-tag">{esc(item["priority"])}</span></td><td>{esc(item["action"])}</td></tr>')
    if not rows:
        rows_html = '<tr><td colspan="6"><div class="empty"><div class="empty-icon">♧</div><b>No action alerts yet</b><br>Alerts are listed here after you run a risk assessment with a non-routine priority.</div></td></tr>'
    else:
        rows_html = ''.join(rows)
    body = f'''<div class="notice"><b>Prototype notice:</b> Department routing and alert records are generated inside this dashboard only. No phone call, SMS, email or external department system is contacted.</div><div class="cards"><div class="metric"><div class="metric-top"><span>Action alerts</span><span class="metric-icon">♧</span></div><div class="metric-number">{len(nonroutine)}</div><div class="metric-foot">Non-routine priorities in this session</div></div><div class="metric"><div class="metric-top"><span>Emergency</span><span class="metric-icon">⚠</span></div><div class="metric-number">{sum(1 for x in nonroutine if x["priority"] == "EMERGENCY")}</div><div class="metric-foot">Critical risk assessments</div></div><div class="metric"><div class="metric-top"><span>Departments</span><span class="metric-icon">⌂</span></div><div class="metric-number">{len(set(x["department"] for x in nonroutine))}</div><div class="metric-foot">Distinct suggested service desks</div></div><div class="metric"><div class="metric-top"><span>Delivery status</span><span class="metric-icon">ⓘ</span></div><div class="metric-number" style="font-size:18px">Local only</div><div class="metric-foot">External messaging not configured</div></div></div><section class="panel"><div class="panel-head"><div><h2>Department alert register</h2><p>Suggested assignment and action priority for recorded predictions</p></div><a class="btn secondary" href="/predict">＋ New assessment</a></div><div class="table-wrap"><table><thead><tr><th>Alert ref</th><th>Created</th><th>Risk level</th><th>Department</th><th>Priority</th><th>Recommended action</th></tr></thead><tbody>{rows_html}</tbody></table></div></section>'''
    return shell("Department Alerts", "Review generated alert records, suggested department routing and the next action for each assessment.", "/alerts", body)


def reports_page():
    average_risk = (sum(x["probability"] for x in ASSESSMENTS) / len(ASSESSMENTS)) if ASSESSMENTS else 0.0
    body = f'''<div class="cards"><div class="metric"><div class="metric-top"><span>Records available</span><span class="metric-icon">▤</span></div><div class="metric-number">{len(ASSESSMENTS)}</div><div class="metric-foot">Current local server session</div></div><div class="metric"><div class="metric-top"><span>Average risk</span><span class="metric-icon">％</span></div><div class="metric-number">{average_risk:.1f}%</div><div class="metric-foot">Across recorded assessments</div></div><div class="metric"><div class="metric-top"><span>High / critical</span><span class="metric-icon">⚠</span></div><div class="metric-number">{sum(1 for x in ASSESSMENTS if x["risk"] in ("HIGH", "CRITICAL"))}</div><div class="metric-foot">Risk score at least 50%</div></div><div class="metric"><div class="metric-top"><span>Export format</span><span class="metric-icon">⇩</span></div><div class="metric-number" style="font-size:22px">CSV</div><div class="metric-foot">Open in Excel or a spreadsheet app</div></div></div><section class="panel"><div class="panel-head"><div><h2>Assessment history</h2><p>Most recent predictions first; records reset when the server is restarted.</p></div><a class="btn" href="/download/report.csv">⇩ Download CSV report</a></div><div class="table-wrap"><table><thead><tr><th>Reference</th><th>Created</th><th>Rainfall</th><th>Traffic</th><th>Road age</th><th>Complaints</th><th>Maintenance gap</th><th>Risk score</th><th>Level</th></tr></thead><tbody>{''.join(f'<tr><td><b>CP-{x["id"]:04d}</b></td><td>{esc(x["time"])}</td><td>{x["values"][0]:g} mm</td><td>{x["values"][1]:g}%</td><td>{x["values"][2]:g} yr</td><td>{x["values"][3]:g}</td><td>{x["values"][4]:g} mo</td><td><b>{x["probability"]:.1f}%</b></td><td><span class="pill {esc(x["risk"])}">{esc(x["risk"])}</span></td></tr>' for x in ASSESSMENTS) if ASSESSMENTS else '<tr><td colspan="9"><div class="empty"><div class="empty-icon">▤</div><b>No report records yet</b><br>Create an assessment first, then return here to view and export your results.</div></td></tr>'}</tbody></table></div></section><div class="note">CSV export includes model score, input values, risk category, priority, recommended department and recommended action. Store approved records in a database before using this design beyond a local demo.</div>'''
    return shell("Reports & History", "Review recent assessments and export the current session records for analysis.", "/reports", body)


def guide_page():
    body = '''<div class="content-grid"><section class="panel"><div class="panel-head"><div><h2>How to use the predictor</h2><p>Follow these steps to create and review an assessment.</p></div></div><div class="step-list"><div class="step"><div class="step-num">1</div><div><b>Enter city conditions</b><p>Provide rainfall, traffic intensity, road age, number of previous complaints and months since maintenance for the location.</p></div></div><div class="step"><div class="step-num">2</div><div><b>Generate a prediction</b><p>Select “Predict infrastructure risk” to calculate a score from 0–100% and review the risk-factor levels.</p></div></div><div class="step"><div class="step-num">3</div><div><b>Review the recommendation</b><p>Read the recommended action, suggested department and priority. A prediction is a decision-support estimate, not proof that a failure will happen.</p></div></div><div class="step"><div class="step-num">4</div><div><b>Track and export</b><p>Use Department Alerts and Reports & History to review results created during the current server session. Download CSV for further analysis.</p></div></div></div></section><section class="panel"><div class="panel-head"><div><h2>Risk levels</h2><p>Prototype threshold rules used by this application</p></div></div><div class="quick-items"><div class="quick-item"><div class="quick-icon">🟢</div><div><b>LOW · below 30%</b><span>Routine monitoring and scheduled maintenance.</span></div></div><div class="quick-item"><div class="quick-icon">🟡</div><div><b>MODERATE · 30–49.9%</b><span>Inspect soon and monitor conditions.</span></div></div><div class="quick-item"><div class="quick-icon">🟠</div><div><b>HIGH · 50–74.9%</b><span>Urgent site inspection and repair planning.</span></div></div><div class="quick-item"><div class="quick-icon">🔴</div><div><b>CRITICAL · 75–100%</b><span>Immediate inspection and protective maintenance planning.</span></div></div></div><div class="note">Risk-factor labels use simple indicator thresholds. The final score depends on the saved model weights when a compatible model file is available.</div></section></div><section class="panel"><div class="panel-head"><div><h2>Scope and current limitations</h2><p>Important details for a responsible hackathon demonstration</p></div></div><div class="detail-grid"><div class="detail"><span>Model</span><b>{esc(MODEL_STATUS)}</b></div><div class="detail"><span>Storage</span><b>Temporary memory only</b></div><div class="detail"><span>Notifications</span><b>Dashboard records only</b></div><div class="detail"><span>Data source</span><b>User-entered example values</b></div></div><div class="note">This prototype does not automatically fetch live municipal data, GPS location, weather or traffic. It does not send real external alerts. For deployment, add validated training data, persistent storage, authentication, audit logs and an approved notification integration.</div></section>'''
    return shell("System Guide", "Understand the workflow, risk categories and limitations before demonstrating the application.", "/guide", body)


class CityPredictor(BaseHTTPRequestHandler):
    def send_bytes(self, content, content_type="text/html; charset=utf-8", status=200, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/dashboard"):
            response = dashboard_page()
        elif path == "/predict":
            response = predictor_page()
        elif path == "/alerts":
            response = alerts_page()
        elif path == "/reports":
            response = reports_page()
        elif path == "/guide":
            response = guide_page()
        elif path == "/download/report.csv":
            stream = io.StringIO(newline="")
            writer = csv.writer(stream)
            writer.writerow(["Reference", "Timestamp", "Rainfall_mm", "Traffic_percent", "Road_age_years", "Previous_complaints", "Maintenance_gap_months", "Risk_score_percent", "Risk_level", "Priority", "Suggested_department", "Recommended_action"])
            for item in reversed(ASSESSMENTS):
                writer.writerow([f'CP-{item["id"]:04d}', item["timestamp"], *item["values"], item["probability"], item["risk"], item["priority"], item["department"], item["action"]])
            content = stream.getvalue().encode("utf-8-sig")
            self.send_bytes(content, "text/csv; charset=utf-8", 200, {"Content-Disposition": 'attachment; filename="ai_city_risk_report.csv"'})
            return
        else:
            response = shell("Page not found", "The requested page is not available.", "", '<section class="panel"><h2>404 · Page not found</h2><p class="muted">Use the navigation menu to return to the application.</p><a class="btn" href="/dashboard">Go to overview</a></section>')
        self.send_bytes(response)

    def do_POST(self):
        global NEXT_ID
        path = urlparse(self.path).path
        if path not in ("/", "/predict"):
            self.send_response(303)
            self.send_header("Location", "/dashboard")
            self.end_headers()
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_data = self.rfile.read(length).decode("utf-8", errors="replace")
            form = parse_qs(raw_data)
            values = [
                safe_number(form, "rainfall", 45, 0, 150),
                safe_number(form, "traffic", 55, 0, 100),
                safe_number(form, "road_age", 5, 0, 15),
                safe_number(form, "complaints", 3, 0, 20),
                safe_number(form, "maintenance_gap", 6, 0, 20),
            ]
            record = make_assessment(values)
            self.send_bytes(predictor_page(record, values))
        except Exception as exc:
            print("Request processing error:", repr(exc))
            message = esc(exc)
            error = shell("Prediction error", "The prediction could not be completed.", "/predict", f'<section class="panel"><h2>Unable to calculate prediction</h2><p>{message}</p><a class="btn" href="/predict">Return to predictor</a></section>')
            try:
                self.send_bytes(error, status=500)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def log_message(self, format_string, *args):
        print("[AI City Predictor]", format_string % args)


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), CityPredictor)
    print("=" * 58)
    print("AI CITY PROBLEM PREDICTOR · Smart City Dashboard")
    print(f"Listening on {HOST}:{PORT}")
    print(MODEL_STATUS)
    print("Pages: /dashboard · /predict · /alerts · /reports · /guide")
    print("Press Ctrl+C to stop the server.")
    print("=" * 58)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()
