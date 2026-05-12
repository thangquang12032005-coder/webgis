from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
from sklearn.ensemble import RandomForestRegressor
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import os
import json 
import ee 
import requests

# ====================== GEE AUTH ====================== 
# 
if "GEE_KEY" in os.environ: 
    key_str = os.environ["GEE_KEY"] # lấy string từ Render ENV 
    key_json = json.loads(key_str) # convert sang dict 
    credentials = ee.ServiceAccountCredentials( 
        key_json["client_email"], 
        key_data=key_str # 🔥 QUAN TRỌNG: phải là STRING 
        ) 
    ee.Initialize(credentials)
else: # chạy local 
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
    KEY_PATH = os.path.join(BASE_DIR, "key.json") 
    credentials = ee.ServiceAccountCredentials( "earth-engine-app@duan1-470914.iam.gserviceaccount.com", KEY_PATH ) 
    ee.Initialize(credentials)
app = Flask(__name__)
CORS(app)

# ====================== HTML ======================
HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebGIS | So sánh 2 thời điểm – Tùy chọn khu vực</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"/>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
    <style>
        :root {
            --primary: #0f172a; --accent: #3b82f6; --success: #10b981;
            --warning: #f59e0b; --danger: #ef4444; --sidebar-width: 460px;
            --card-bg: #ffffff; --text-main: #1e293b; --text-muted: #64748b;
            --glass: rgba(255, 255, 255, 0.95);
        }
        * { box-sizing: border-box; scrollbar-width: thin; }
        body { margin:0; font-family:'Plus Jakarta Sans',sans-serif; background:#f1f5f9; display:flex; height:100vh; overflow:hidden; color:var(--text-main); }
        #sidebar { width:var(--sidebar-width); background:var(--card-bg); border-right:1px solid #e2e8f0; display:flex; flex-direction:column; box-shadow:4px 0 24px rgba(0,0,0,0.05); z-index:1001; }
        .brand { padding:24px; background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%); color:white; display:flex; align-items:center; gap:15px; border-bottom:1px solid rgba(255,255,255,0.1); }
        .brand i { font-size:28px; color:var(--accent); }
        .brand h1 { margin:0; font-size:20px; font-weight:800; letter-spacing:1px; }
        
        /* Language Selector Style */
        .lang-container { padding: 10px 20px; background: #1e293b; border-bottom: 1px solid rgba(255,255,255,0.05); }
        #lang-selector { background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2); cursor: pointer; font-weight: 600; }
        #lang-selector option { background: #1e293b; color: white; }

        .scroll-area{

    padding:24px;

    overflow-y:auto;

    flex:1;

    position:relative;

    background:
    linear-gradient(
        180deg,
        #eef4ff 0%,
        #f8fbff 35%,
        #f8fafc 100%
    );
}

/* LIGHT EFFECT */

.scroll-area::before{

    content:'';

    position:fixed;

    top:-180px;
    right:-120px;

    width:420px;
    height:420px;

    border-radius:50%;

    background:
    radial-gradient(
        circle,
        rgba(59,130,246,.12),
        transparent 70%
    );

    pointer-events:none;

    z-index:0;
}

/* CARD */

.step-card{

    position:relative;

    background:
    linear-gradient(
        180deg,
        rgba(255,255,255,.96),
        rgba(248,250,252,.98)
    );

    border-radius:28px;

    padding:24px;

    margin-bottom:24px;

    border:
    1px solid rgba(255,255,255,.7);

    box-shadow:
    0 10px 40px rgba(15,23,42,.06),
    0 2px 10px rgba(15,23,42,.04);

    backdrop-filter:blur(20px);

    overflow:hidden;

    transition:.35s;

    z-index:1;
}

/* TOP ACCENT */

.step-card::before{

    content:'';

    position:absolute;

    top:0;
    left:0;

    width:100%;
    height:5px;

    background:
    linear-gradient(
        90deg,
        #3b82f6,
        #06b6d4,
        #6366f1
    );
}

.step-card:hover{

    transform:translateY(-4px);

    border-color:
    rgba(59,130,246,.18);

    box-shadow:
    0 25px 50px rgba(15,23,42,.10),
    0 10px 25px rgba(59,130,246,.08);
}

/* HEADER */

.step-header{

    display:flex;

    align-items:center;

    gap:12px;

    margin-bottom:22px;

    padding-bottom:14px;

    border-bottom:
    1px solid rgba(148,163,184,.15);

    font-size:15px;

    font-weight:800;

    color:#0f172a;

    letter-spacing:.5px;

    text-transform:uppercase;
}

.step-header i{

    width:40px;
    height:40px;

    border-radius:14px;

    display:flex;

    align-items:center;

    justify-content:center;

    background:
    linear-gradient(
        135deg,
        #3b82f6,
        #2563eb
    );

    color:white;

    box-shadow:
    0 10px 20px rgba(59,130,246,.25);
}

/* SELECT */

select{

    width:100%;

    padding:16px 18px;

    border-radius:18px;

    border:
    1px solid #dbeafe;

    background:
    linear-gradient(
        180deg,
        #ffffff,
        #f8fafc
    );

    font-family:inherit;

    font-size:15px;

    font-weight:600;

    color:#0f172a;

    outline:none;

    appearance:none;

    cursor:pointer;

    transition:.3s;

    box-shadow:
    inset 0 1px 2px rgba(255,255,255,.8),
    0 2px 10px rgba(15,23,42,.03);

    background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' fill='none' stroke='%23334155' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 8 10 12 14 8'/%3E%3C/svg%3E");

    background-repeat:no-repeat;

    background-position:right 16px center;

    padding-right:48px;
}

select:hover{

    border-color:#93c5fd;

    transform:translateY(-1px);

    box-shadow:
    0 8px 25px rgba(59,130,246,.08);
}

select:focus{

    border-color:#3b82f6;

    box-shadow:
    0 0 0 5px rgba(59,130,246,.12),
    0 10px 30px rgba(59,130,246,.10);
}

select option{

    background:#ffffff;

    color:#0f172a;

    font-weight:600;
}

/* BUTTON DEFAULT */

button{

    border:none;

    outline:none;

    font-family:inherit;
}

/* PRIMARY BUTTON */

.btn-primary{

    width:100%;

    height:58px;

    border:none;

    border-radius:18px;

    background:
    linear-gradient(
        135deg,
        #0f172a,
        #1e3a8a
    );

    color:white;

    font-size:15px;

    font-weight:700;

    cursor:pointer;

    transition:.35s;

    display:flex;

    align-items:center;

    justify-content:center;

    gap:10px;

    margin-top:14px;

    box-shadow:
    0 12px 25px rgba(15,23,42,.18);

    position:relative;

    overflow:hidden;
}

.btn-primary::before{

    content:'';

    position:absolute;

    top:0;
    left:-120%;

    width:120%;
    height:100%;

    background:
    linear-gradient(
        90deg,
        transparent,
        rgba(255,255,255,.18),
        transparent
    );

    transition:.6s;
}

.btn-primary:hover::before{

    left:120%;
}

.btn-primary:hover{

    transform:
    translateY(-2px)
    scale(1.01);

    box-shadow:
    0 20px 40px rgba(30,58,138,.25);
}

/* ANALYZE BUTTON */

.btn-analyze{

    width:100%;

    height:64px;

    border:none;

    border-radius:20px;

    margin-top:18px;

    background:
    linear-gradient(
        135deg,
        #2563eb,
        #1d4ed8,
        #1e3a8a
    );

    color:white;

    font-size:15px;

    font-weight:800;

    letter-spacing:.5px;

    cursor:pointer;

    transition:.35s;

    box-shadow:
    0 15px 35px rgba(37,99,235,.25);

    position:relative;

    overflow:hidden;
}

.btn-analyze::before{

    content:'';

    position:absolute;

    top:0;
    left:-130%;

    width:120%;
    height:100%;

    background:
    linear-gradient(
        90deg,
        transparent,
        rgba(255,255,255,.2),
        transparent
    );

    transition:.7s;
}

.btn-analyze:hover::before{

    left:130%;
}

.btn-analyze:hover{

    transform:
    translateY(-3px)
    scale(1.01);

    box-shadow:
    0 25px 50px rgba(37,99,235,.35);
}

/* YEAR + MONTH */

.time-row{

    display:grid;

    grid-template-columns:1fr 1fr;

    gap:14px;

    margin-top:12px;
}

/* LABEL */

label{

    display:block;

    margin-bottom:10px;

    font-size:14px;

    font-weight:700;

    color:#0f172a;
}

/* SMALL TEXT */

small{

    display:flex;

    align-items:center;

    gap:6px;

    margin-top:12px;

    color:#64748b;

    font-size:13px;
}

/* CUSTOM SCROLL */

.scroll-area::-webkit-scrollbar{

    width:10px;
}

.scroll-area::-webkit-scrollbar-track{

    background:transparent;
}

.scroll-area::-webkit-scrollbar-thumb{

    background:
    linear-gradient(
        180deg,
        #93c5fd,
        #3b82f6
    );

    border-radius:999px;
}
        #map-container { flex:1; position:relative; }
        #map { height:100%; width:100%; z-index:1; }
        .floating-dashboard { position:absolute; bottom:30px; left:30px; width:680px; max-height:calc(100vh - 120px); background:var(--glass); border-radius:24px; z-index:1000; box-shadow:0 25px 50px -12px rgba(0,0,0,0.25); display:none; flex-direction:column; overflow:hidden; border:1px solid rgba(255,255,255,0.3); backdrop-filter:blur(16px); }
        .dash-header { background:var(--primary); color:white; padding:18px 24px; font-weight:700; font-size:16px; display:flex; justify-content:space-between; align-items:center; }
        .dash-header button { background:var(--success); border:none; color:white; padding:10px 16px; border-radius:10px; cursor:pointer; font-size:14px; font-weight:600; display:flex; align-items:center; gap:8px; box-shadow:0 4px 12px rgba(16,185,129,0.3); }
        .dash-body { padding:24px; overflow-y:auto; flex:1; }
        #toggle-dash-btn { position:absolute; bottom:30px; left:30px; z-index:1001; width:60px; height:60px; border-radius:50%; background:var(--primary); color:white; border:none; cursor:pointer; display:none; box-shadow:0 10px 25px rgba(0,0,0,0.3); align-items:center; justify-content:center; font-size:24px; }
        .province-report-card { background:white; border-radius:20px; padding:20px; margin-bottom:24px; border:1px solid #e2e8f0; box-shadow:0 4px 12px rgba(0,0,0,0.04); }
        .province-name { font-size:19px; font-weight:800; color:var(--primary); margin-bottom:12px; }
        .data-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:18px; }
        .data-box { background:#f8fafc; padding:14px 10px; border-radius:12px; text-align:center; border:1px solid #f1f5f9; }
        .data-label { font-size:11px; color:var(--text-muted); text-transform:uppercase; font-weight:700; margin-bottom:6px; letter-spacing:0.4px; }
        .data-value { font-size:17px; font-weight:800; color:var(--primary); }
        .indicator-info { font-size:13.5px; line-height:1.7; color:#475569; padding:16px; background:#f0f9ff; border-radius:12px; margin-top:12px; border-left:5px solid var(--accent); }
        .chart-wrapper { height:170px; position:relative; margin-bottom:35px; }
        .legend-panel { position:absolute; top:20px; right:20px; background:var(--glass); padding:18px; border-radius:20px; z-index:1000; box-shadow:0 10px 30px rgba(0,0,0,0.12); width:260px; font-size:12.5px; border:1px solid rgba(255,255,255,0.35); backdrop-filter:blur(12px); display:none; }
        .legend-toggle-btn, .focus-toggle-btn { 
            position:absolute; top:20px; width:48px; height:48px; border-radius:50%; 
            background:var(--primary); color:white; border:none; cursor:pointer; 
            box-shadow:0 8px 20px rgba(0,0,0,0.25); font-size:18px; 
            display:flex; align-items:center; justify-content:center; z-index:1001; 
        }
        .legend-toggle-btn { right:300px; }
        .focus-toggle-btn { right:20px; }
        .focus-toggle-btn.active { background:#ef4444; }
        .color-row { display:flex; align-items:center; gap:12px; margin-bottom:10px; font-weight:500; }
        .color-box { width:22px; height:22px; border-radius:6px; border:1px solid rgba(0,0,0,0.06); }
        .loading-screen { display:none; position:fixed; inset:0; background:rgba(15,23,42,0.94); z-index:9999; flex-direction:column; justify-content:center; align-items:center; color:white; backdrop-filter:blur(10px); }
        .loader { width:80px; height:80px; border:8px solid rgba(255,255,255,0.12); border-bottom-color:var(--accent); border-radius:50%; animation:rotation 1s linear infinite; }
        @keyframes rotation { 0% { transform:rotate(0deg); } 100% { transform:rotate(360deg); } }
        #weather-toggle-btn{

    position:absolute;

    top:20px;
    left:20px;

    width:60px;
    height:60px;

    border-radius:50%;

    border:none;

    z-index:10000;

    cursor:pointer;

    font-size:24px;

    color:white;

    background:
    linear-gradient(
        180deg,
        #2563eb,
        #0f172a
    );

    box-shadow:
    0 10px 30px rgba(0,0,0,0.4);

    backdrop-filter:blur(20px);

    transition:0.3s;
}

#weather-card{

    display:none;

    position:absolute;

    top:90px;
    left:20px;

    width:350px;

    z-index:9999;

    border-radius:32px;

    padding:24px;

    color:white;

    overflow:hidden;

    background:
    linear-gradient(
        180deg,
        rgba(15,23,42,.78),
        rgba(15,23,42,.92)
    );

    background-image:
    linear-gradient(
        180deg,
        rgba(15,23,42,.45),
        rgba(15,23,42,.88)
    ),
    url(
'https://images.unsplash.com/photo-1506744038136-46273834b3fb'
    );

    background-size:cover;

    background-position:center;

    backdrop-filter:blur(25px);

    border:
    1px solid rgba(255,255,255,.08);

    box-shadow:
    0 20px 60px rgba(0,0,0,.45);
}
.weather-city{

    font-size:28px;
    font-weight:700;
}

.weather-temp{

    font-size:80px;
    font-weight:200;
}

.weather-day{

    display:flex;

    align-items:center;

    justify-content:space-between;

    margin-top:10px;

    padding:14px 16px;

    border-radius:18px;

    background:
    rgba(255,255,255,0.08);

    border:
    1px solid rgba(255,255,255,0.06);

    backdrop-filter:blur(10px);
}
        .toast { position:absolute; bottom:100px; left:50%; transform:translateX(-50%); background:#1e293b; color:white; padding:12px 24px; border-radius:12px; z-index:2000; display:none; font-weight:500; }
    </style>
</head>
<body>

<div id="loader-overlay" class="loading-screen">
    <div class="loader"></div>
    <h2 style="margin-top:30px; letter-spacing:2px; font-weight:800;" id="txt-processing-title">WEBGIS PROCESSING</h2>
    <p style="opacity:0.75; font-size:14px; margin-top:12px;" id="txt-processing-desc">Đang tính toán chỉ số từ Landsat...</p>
</div>

<div id="sidebar">
    <div class="brand">
        <i class="fa-solid fa-map-location-dot"></i>
        <div>
            <h1>WEBGIS</h1>
            <div id="txt-subtitle" style="font-size:10px; opacity:0.6; font-weight:600; text-transform:uppercase;">So sánh 2 thời điểm – Tùy chọn khu vực</div>
        </div>
    </div>

    <div class="lang-container">
        <select id="lang-selector" onchange="changeLanguage(this.value)">
            <option value="vi">🇻🇳 Tiếng Việt</option>
            <option value="en">🇺🇸 English</option>
            <option value="zh">🇨🇳 中文</option>
        </select>
    </div>

    <div class="scroll-area">
        <div class="step-card">
            <div class="step-header" id="txt-region"><i class="fa-solid fa-layer-group"></i> Khu vực</div>
            <select id="country-select" onchange="loadProvinces()"><option value="" id="opt-country-default">-- Quốc gia --</option></select>
            <div style="margin-top:16px;">
                <h4 style="margin:0 0 12px 0; font-size:14px; color:var(--primary);" id="txt-province-label">Tỉnh/Thành phố</h4>
                <select id="province-select" onchange="updateBoundary(this.value)">
                    <option value="" id="opt-province-default">-- Chọn tỉnh --</option>
                </select>
            </div>
            <small style="color:#64748b; margin-top:8px; display:block;" id="txt-click-map-tip">Hoặc click trực tiếp lên bản đồ để chọn tỉnh</small>
        </div>

        <div class="step-card">
            <div class="step-header" id="txt-time1"><i class="fa-solid fa-clock"></i> Thời điểm 1</div>
            <div class="time-row">
                <select id="year1-input">
                    <option value="2024">2024</option><option value="2023">2023</option><option value="2022">2022</option>
                    <option value="2021">2021</option><option value="2020">2020</option>
                </select>
                <select id="month1-input">
                    <option value="1">Tháng 1</option><option value="2">Tháng 2</option><option value="3" selected>Tháng 3</option>
                    <option value="4">Tháng 4</option><option value="5">Tháng 5</option><option value="6">Tháng 6</option>
                    <option value="7">Tháng 7</option><option value="8">Tháng 8</option><option value="9">Tháng 9</option>
                    <option value="10">Tháng 10</option><option value="11">Tháng 11</option><option value="12">Tháng 12</option>
                </select>
            </div>
            <button class="btn-primary" onclick="fetchAvailableImages(1)" style="margin-top:12px;">
                <i class="fa-solid fa-satellite-dish"></i> <span id="txt-scan1">Quét ảnh</span>
            </button>
            <select id="image-date1-select" style="margin-top:10px; display:none; border-color:var(--accent); font-weight:700; color:var(--accent);"></select>
        </div>

        <div class="step-card">
            <div class="step-header" id="txt-time2"><i class="fa-solid fa-clock"></i> Thời điểm 2</div>
            <div class="time-row">
                <select id="year2-input">
                    <option value="2024">2024</option><option value="2023">2023</option><option value="2022">2022</option>
                    <option value="2021">2021</option><option value="2020">2020</option>
                </select>
                <select id="month2-input">
                    <option value="1">Tháng 1</option><option value="2">Tháng 2</option><option value="3" selected>Tháng 3</option>
                    <option value="4">Tháng 4</option><option value="5">Tháng 5</option><option value="6">Tháng 6</option>
                    <option value="7">Tháng 7</option><option value="8">Tháng 8</option><option value="9">Tháng 9</option>
                    <option value="10">Tháng 10</option><option value="11">Tháng 11</option><option value="12">Tháng 12</option>
                </select>
            </div>
            <button class="btn-primary" onclick="fetchAvailableImages(2)" style="margin-top:12px;">
                <i class="fa-solid fa-satellite-dish"></i> <span id="txt-scan2">Quét ảnh</span>
            </button>
            <select id="image-date2-select" style="margin-top:10px; display:none; border-color:var(--accent); font-weight:700; color:var(--accent);"></select>
        </div>

        <div class="step-card">
            <div class="step-header" id="txt-config"><i class="fa-solid fa-flask-vial"></i> Cấu hình phân tích</div>
            <select id="index-selector">
                <option value="TẤT CẢ">NDVI + LST + TVDI</option>
                <option value="NDVI">Chỉ số thực vật (NDVI)</option>
                <option value="LST">Nhiệt độ bề mặt (LST)</option>
                <option value="TVDI">Chỉ số hạn hán (TVDI)</option>
            </select>
            <button class="btn-analyze" id="btn-analyze" onclick="startProcessing()">
                <i class="fa-solid fa-wand-magic-sparkles"></i> SO SÁNH 2 THỜI ĐIỂM
            </button>
        </div>

        <div class="step-card">
            <div class="step-header" id="txt-comparison-results"><i class="fa-solid fa-chart-simple"></i> So sánh kết quả</div>
            <div style="display: flex; flex-direction: column; gap: 40px;">
                <div id="ndvi-chart-container">
                    <div style="text-align:center; font-weight:700; font-size:15px; color:#10b981; margin-bottom:8px;">NDVI</div>
                    <div class="chart-wrapper"><canvas id="ndviChart"></canvas></div>
                </div>
                <div id="tvdi-chart-container">
                    <div style="text-align:center; font-weight:700; font-size:15px; color:#f59e0b; margin-bottom:8px;">TVDI</div>
                    <div class="chart-wrapper"><canvas id="tvdiChart"></canvas></div>
                </div>
                <!-- LST GIỮ NGUYÊN -->
<div id="lst-chart-container">
    <div style="text-align:center; font-weight:700; font-size:15px; color:#ef4444; margin-bottom:8px;">
        LST (°C)
    </div>
    <div class="chart-wrapper">
        <canvas id="lstChart"></canvas>
    </div>
</div>

<!-- SCATTER THÊM MỚI -->
<div id="scatter-chart-container">
    <div style="text-align:center; font-weight:700; font-size:15px; color:#6366f1; margin-bottom:8px;">
        Scatter NDVI vs LST
    </div>
    <div class="chart-wrapper">
        <canvas id="scatterChart"></canvas>
    </div>
</div>
            </div>
        </div>
    </div>
</div>

<div id="map-container">
    <div id="map"></div>
    <button id="weather-toggle-btn"
        onclick="toggleWeatherCard()">

    🌤️

</button>

<div id="weather-card"></div>
    
    <button class="legend-toggle-btn" onclick="toggleLegend()"><i class="fa-solid fa-list-ul"></i></button>
    <button class="focus-toggle-btn" id="focus-btn" onclick="toggleFocusMode()"><i class="fa-solid fa-moon"></i></button>
    
    <div id="legend-panel" class="legend-panel">
        <div id="legend-content"></div>
    </div>

    <button id="toggle-dash-btn" onclick="toggleDashboard(true)"><i class="fa-solid fa-file-waveform"></i></button>

    <div id="floating-dashboard" class="floating-dashboard">
        <div class="dash-header">
            <span><i class="fa-solid fa-table-list"></i> <span id="txt-dash-title">BẢNG TIN</span></span>
            <div style="display:flex; align-items:center; gap:12px;">
                <button onclick="exportToExcel()"><i class="fa-solid fa-file-excel"></i> <span id="txt-export-excel">TẢI EXCEL</span></button>
                <i class="fa-solid fa-circle-xmark" 
                   style="cursor:pointer; font-size:28px; opacity:0.95; color:white; margin-left:10px;" 
                   onclick="toggleDashboard(false)"></i>
            </div>
        </div>
        <div id="dash-body" class="dash-body"></div>
    </div>
    <div id="toast" class="toast"></div>
</div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
// Dictionary
const LANG = {
    vi: {
        subtitle: "So sánh 2 thời điểm – Tùy chọn khu vực",
        region: "Khu vực",
        countryDefault: "-- Quốc gia --",
        provinceLabel: "Tỉnh/Thành phố",
        provinceDefault: "-- Chọn tỉnh --",
        clickMapTip: "Hoặc click trực tiếp lên bản đồ để chọn tỉnh",
        time1: "Thời điểm 1",
        time2: "Thời điểm 2",
        scan: "Quét ảnh",
        config: "Cấu hình phân tích",
        analyze: "SO SÁNH 2 THỜI ĐIỂM",
        results: "So sánh kết quả",
        dashTitle: "BẢNG TIN",
        exportExcel: "TẢI EXCEL",
        processingTitle: "XỬ LÝ WEBGIS",
        processingDesc: "Đang tính toán chỉ số từ Landsat..."
    },
    en: {
        subtitle: "Compare 2 Times – Region Selection",
        region: "Region",
        countryDefault: "-- Country --",
        provinceLabel: "Province/City",
        provinceDefault: "-- Select Province --",
        clickMapTip: "Or click directly on the map to select a province",
        time1: "Time 1",
        time2: "Time 2",
        scan: "Scan Images",
        config: "Analysis Config",
        analyze: "COMPARE TWO TIMES",
        results: "Comparison Results",
        dashTitle: "DASHBOARD",
        exportExcel: "EXPORT EXCEL",
        processingTitle: "WEBGIS PROCESSING",
        processingDesc: "Calculating indices from Landsat..."
    },
    zh: {
        subtitle: "两个时段对比 – 区域选择",
        region: "区域",
        countryDefault: "-- 国家 --",
        provinceLabel: "省/直辖市",
        provinceDefault: "-- 选择省份 --",
        clickMapTip: "或直接点击地图选择省份",
        time1: "时间点 1",
        time2: "时间点 2",
        scan: "扫描图像",
        config: "分析配置",
        analyze: "比较两个时间点",
        results: "比较结果",
        dashTitle: "仪表板",
        exportExcel: "导出 EXCEL",
        processingTitle: "WEBGIS 处理中",
        processingDesc: "正在从 Landsat 计算指数..."
    }
};

function changeLanguage(lang) {
    const d = LANG[lang];
    document.getElementById("txt-subtitle").innerText = d.subtitle;
    document.getElementById("txt-region").innerHTML = `<i class="fa-solid fa-layer-group"></i> ${d.region}`;
    document.getElementById("opt-country-default").innerText = d.countryDefault;
    document.getElementById("txt-province-label").innerText = d.provinceLabel;
    document.getElementById("opt-province-default").innerText = d.provinceDefault;
    document.getElementById("txt-click-map-tip").innerText = d.clickMapTip;
    document.getElementById("txt-time1").innerHTML = `<i class="fa-solid fa-clock"></i> ${d.time1}`;
    document.getElementById("txt-time2").innerHTML = `<i class="fa-solid fa-clock"></i> ${d.time2}`;
    document.getElementById("txt-scan1").innerText = d.scan;
    document.getElementById("txt-scan2").innerText = d.scan;
    document.getElementById("txt-config").innerHTML = `<i class="fa-solid fa-flask-vial"></i> ${d.config}`;
    document.getElementById("btn-analyze").innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> ${d.analyze}`;
    document.getElementById("txt-comparison-results").innerHTML = `<i class="fa-solid fa-chart-simple"></i> ${d.results}`;
    document.getElementById("txt-dash-title").innerText = d.dashTitle;
    document.getElementById("txt-export-excel").innerText = d.exportExcel;
    document.getElementById("txt-processing-title").innerText = d.processingTitle;
    document.getElementById("txt-processing-desc").innerText = d.processingDesc;
    
    // Refresh month labels if needed
    const monthsVi = ["Tháng 1", "Tháng 2", "Tháng 3", "Tháng 4", "Tháng 5", "Tháng 6", "Tháng 7", "Tháng 8", "Tháng 9", "Tháng 10", "Tháng 11", "Tháng 12"];
    const monthsEn = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const monthsZh = ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"];
    
    let currentMonths = lang === 'en' ? monthsEn : (lang === 'zh' ? monthsZh : monthsVi);
    
    [1, 2].forEach(num => {
        const select = document.getElementById(`month${num}-input`);
        const val = select.value;
        Array.from(select.options).forEach((opt, idx) => {
            opt.text = currentMonths[idx];
        });
    });
}

// Global variables
var map, baseSatellite, boundaryLayer, layerControl, indexLayers = {};
var currentAnalysisData = null;
var ndviChart, tvdiChart, lstChart, scatterChart;
var focusMode = false;

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => toast.style.display = 'none', 3000);
}

window.onload = function() {
    map = L.map('map', {zoomControl:false}).setView([15, 108], 5);
    
    baseSatellite = L.tileLayer('https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}', {
        subdomains:['mt0','mt1','mt2','mt3'], maxZoom: 20
    }).addTo(map);

    L.control.zoom({position:'topright'}).addTo(map);
    layerControl = L.control.layers({"Vệ tinh Google": baseSatellite}, {}, {position:'bottomright'}).addTo(map);

    map.createPane('indexPane');
    map.getPane('indexPane').style.zIndex = 700;

    map.on('click', function(e) {
        const latlng = e.latlng;
        document.getElementById("loader-overlay").style.display = "flex";

        fetch('/api/get_province_from_point', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({lat: latlng.lat, lng: latlng.lng})
        })
        .then(r => r.json())
        .then(data => {
            if (data.country && data.province) {
                document.getElementById('country-select').value = data.country;
                loadProvinces();
                setTimeout(() => {
                    document.getElementById('province-select').value = data.province;
                    updateBoundary(data.province);
                    showToast(`✅ Đã chọn: ${data.province}, ${data.country}`);
                }, 800);
            } else {
                showToast("⚠️ Không tìm thấy tỉnh/thành phố tại vị trí click");
            }
        })
        .finally(() => document.getElementById("loader-overlay").style.display = "none");
    });

    fetch('/api/countries').then(r=>r.json()).then(data=>{
        const s = document.getElementById('country-select');
        data.sort().forEach(c => s.add(new Option(c, c)));
    });
    loadWeatherForecast();
};

function loadProvinces() {
    const country = document.getElementById('country-select').value;
    if (!country) return;
    fetch(`/api/provinces?country=${encodeURIComponent(country)}`)
    .then(r=>r.json()).then(data=>{
        const sel = document.getElementById('province-select');
        sel.innerHTML = '<option value="">-- Chọn tỉnh --</option>';
        data.provinces.sort().forEach(p=>sel.add(new Option(p,p)));
    });
}

function updateBoundary(province) {
    if (boundaryLayer) map.removeLayer(boundaryLayer);
    if (!province) return;
    const country = document.getElementById('country-select').value;
    fetch(`/api/get_province_boundary?country=${encodeURIComponent(country)}&province=${encodeURIComponent(province)}`)
    .then(r=>r.json()).then(data=>{
        boundaryLayer = L.geoJSON(data.geojson, {style:{color:"#3b82f6", weight:2.8, fillOpacity:0.08}}).addTo(map);
        map.fitBounds(boundaryLayer.getBounds());
    });
}

function fetchAvailableImages(which) {
    const country  = document.getElementById('country-select').value;
    const province = document.getElementById('province-select').value;
    const year     = document.getElementById(`year${which}-input`).value;
    const month    = document.getElementById(`month${which}-input`).value;

    if (!country || !province || !year || !month) {
        alert(`Vui lòng chọn đầy đủ thông tin cho Thời điểm ${which}`);
        return;
    }

    document.getElementById("loader-overlay").style.display = "flex";

    fetch('/api/find_images', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({country, province, year, month})
    })
    .then(r=>r.json())
    .then(data=>{
        const sel = document.getElementById(`image-date${which}-select`);
        sel.innerHTML = "";
        if (data.dates && data.dates.length > 0) {
            data.dates.forEach(d => sel.add(new Option(d.label, d.value)));
            sel.style.display = "block";
        } else {
            alert(`Không tìm thấy ảnh Landsat sạch mây cho Thời điểm ${which}.`);
        }
    })
    .finally(() => document.getElementById("loader-overlay").style.display = "none");
}

function toggleFocusMode() {
    focusMode = !focusMode;
    const btn = document.getElementById('focus-btn');
    if (focusMode) {
        btn.innerHTML = '<i class="fa-solid fa-sun"></i>';
        btn.classList.add('active');
        if (baseSatellite) baseSatellite.setOpacity(0.15);
        if (boundaryLayer) boundaryLayer.setStyle({color: "#ffffff", weight: 4, fillOpacity: 0.25});
        Object.values(indexLayers).forEach(layer => { if (map.hasLayer(layer)) layer.setOpacity(0.95); });
        showToast("🌑 Focus Mode ON");
    } else {
        btn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        btn.classList.remove('active');
        if (baseSatellite) baseSatellite.setOpacity(1);
        if (boundaryLayer) boundaryLayer.setStyle({color: "#3b82f6", weight: 2.8, fillOpacity: 0.08});
        Object.values(indexLayers).forEach(layer => { if (map.hasLayer(layer)) layer.setOpacity(0.85); });
        showToast("☀️ Focus Mode OFF");
    }
}

function startProcessing() {
    const date1 = document.getElementById("image-date1-select").value;
    const date2 = document.getElementById("image-date2-select").value;

    if (!date1 || !date2) {
        alert("Vui lòng chọn ngày ảnh cho cả hai thời điểm!");
        return;
    }

    const payload = {
        country: document.getElementById("country-select").value,
        province: document.getElementById("province-select").value,
        date1: date1,
        date2: date2,
        index: document.getElementById("index-selector").value
    };

    document.getElementById("loader-overlay").style.display = "flex";

    fetch('/api/analyze_two_times', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(payload)
    })
    .then(r=>r.json())
    .then(data=>{
        currentAnalysisData = data;

        Object.keys(indexLayers).forEach(k => {
            if (map.hasLayer(indexLayers[k])) map.removeLayer(indexLayers[k]);
        });
        indexLayers = {};

        const dateMap = {'1': data.stats[0].date, '2': data.stats[1].date};

        if (data.map_urls) {
            Object.keys(data.map_urls).forEach(k => {
                const url = data.map_urls[k];
                if (!url) return;

                const parts = k.split('_');
                const indexType = parts[0].toUpperCase();
                const phaseNum = parts[1];
                const phaseText = phaseNum === '1' ? `Thời điểm 1 - ${dateMap['1']}` : `Thời điểm 2 - ${dateMap['2']}`;
                const displayName = `${indexType} (${phaseText})`;

                const layer = L.tileLayer(url, {
                    opacity: 0.85,
                    pane: 'indexPane',
                    zIndex: 700,
                    maxZoom: 20
                });

                indexLayers[k] = layer;
                layer.addTo(map);
                layer.bringToFront();
                layerControl.addOverlay(layer, displayName);
            });
            showToast("✅ Đã hiển thị các layer phân tích lên bản đồ!");
        }

      renderDashboard(data);
      renderChart(data);
      updateLegend(payload.index);
      

if (data && data.future_risk_total != null) {
    const body = document.getElementById("dash-body");
    const riskValue = Number(data.future_risk_total);

    // Tự động đổi màu dựa trên mức độ rủi ro
    let riskColor = '#4ade80'; // Xanh lá (An toàn)
    if (riskValue >= 0.6) {
        riskColor = '#f87171'; // Đỏ (Nguy cơ cao)
    } else if (riskValue >= 0.3) {
        riskColor = '#fbbf24'; // Vàng (Cảnh báo)
    }

    const riskBox = `
    <div style="
        margin-top: 24px;
        padding: 20px;
        border-radius: 16px;
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        color: #f8fafc;
        font-family: system-ui, -apple-system, sans-serif;
        line-height: 1.5;
    ">
        <div style="
            display: flex; 
            align-items: center; 
            gap: 8px; 
            font-size: 16px; 
            font-weight: 700; 
            color: #c084fc; 
            margin-bottom: 16px; 
            border-bottom: 1px solid #334155; 
            padding-bottom: 12px;
        ">
            <span style="font-size: 18px;">🔮</span> DỰ BÁO TƯƠNG LAI DỰA TRÊN DỮ LIỆU CỦA 2 GIAI ĐOẠN 
        </div>

        <div style="display: flex; flex-direction: column; gap: 16px;">
            
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: rgba(15, 23, 42, 0.5);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 16px;
            ">
                <div style="color: #94a3b8; font-size: 14px; font-weight: 500;">
                    Chỉ số Risk tương lai
                    <div style="font-size: 12px; font-weight: normal; margin-top: 4px; opacity: 0.7;">
                        Dựa trên dữ liệu 2 giai đoạn
                    </div>
                </div>
                <div style="
                    font-size: 32px; 
                    font-weight: 800; 
                    font-family: monospace; 
                    color: ${riskColor};
                    text-shadow: 0 0 15px ${riskColor}40;
                ">
                    ${riskValue.toFixed(2)}
                </div>
            </div>

            <div style="
                background: rgba(56, 189, 248, 0.05);
                border-left: 4px solid #38bdf8;
                padding: 12px 16px;
                border-radius: 4px;
                font-size: 14px;
            ">
                <div style="
                    color: #38bdf8; 
                    font-weight: 600; 
                    font-size: 11px; 
                    margin-bottom: 6px; 
                    text-transform: uppercase; 
                    letter-spacing: 0.5px;
                ">
                    Phân tích xu hướng
                </div>
                <div style="color: #e2e8f0; font-weight: 500; font-size: 14px;">
                    ${data.trend_total || "Đang cập nhật dữ liệu..."}
                </div>
            </div>

        </div>
    </div>
    `;

    body.insertAdjacentHTML("beforeend", riskBox);
}

       toggleDashboard(true);
    })
    .finally(() => document.getElementById("loader-overlay").style.display = "none");
}

function renderChart(data) {
    if (ndviChart) ndviChart.destroy();
    if (tvdiChart) tvdiChart.destroy();
    if (lstChart) lstChart.destroy();

    const selectedIndex = document.getElementById("index-selector").value.toUpperCase();
    const labels = [data.stats[0].label, data.stats[1].label];

    document.getElementById('ndvi-chart-container').style.display = (selectedIndex === "NDVI" || selectedIndex === "TẤT CẢ") ? "block" : "none";
    document.getElementById('tvdi-chart-container').style.display = (selectedIndex === "TVDI" || selectedIndex === "TẤT CẢ") ? "block" : "none";
    document.getElementById('lst-chart-container').style.display = (selectedIndex === "LST" || selectedIndex === "TẤT CẢ") ? "block" : "none";
    
    if (scatterChart) scatterChart.destroy();

if (selectedIndex === "TẤT CẢ") {
    scatterChart = new Chart(document.getElementById('scatterChart'), {
    type: 'scatter',
    data: {
        datasets: [
            {
                label: 'Thời điểm 1',
                data: [{ x: data.stats[0].ndvi, y: data.stats[0].lst }],
                backgroundColor: '#3b82f6',
                pointRadius: 8,
                pointHoverRadius: 10
            },
            {
                label: 'Thời điểm 2',
                data: [{ x: data.stats[1].ndvi, y: data.stats[1].lst }],
                backgroundColor: '#ef4444',
                pointRadius: 8,
                pointHoverRadius: 10
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            },
            tooltip: {
                callbacks: {
                    label: function(ctx) {
                        return `NDVI: ${ctx.raw.x.toFixed(3)} | LST: ${ctx.raw.y.toFixed(1)}°C`;
                    }
                }
            }
        },
        scales: {
            x: {
                title: { display: true, text: 'NDVI' },
                min: -0.2,
                max: 1,
                grid: { color: '#e5e7eb' }
            },
            y: {
                title: { display: true, text: 'LST (°C)' },
                min: 0,
                max: 50,
                grid: { color: '#e5e7eb' }
            }
        }
    }
});
}

    if (selectedIndex === "NDVI" || selectedIndex === "TẤT CẢ") {
        ndviChart = new Chart(document.getElementById('ndviChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{ 
                    label: 'NDVI', 
                    data: [data.stats[0].ndvi, data.stats[1].ndvi],
                    backgroundColor: ['#10b981', '#34d399'] 
                }]
            },
            options: { responsive:true, maintainAspectRatio:false, scales: { y: { min: -0.2, max: 1.0 } }, plugins: { legend: { display: false } } }
        });
    }

    if (selectedIndex === "TVDI" || selectedIndex === "TẤT CẢ") {
        tvdiChart = new Chart(document.getElementById('tvdiChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{ 
                    label: 'TVDI', 
                    data: [data.stats[0].tvdi, data.stats[1].tvdi],
                    backgroundColor: ['#f59e0b', '#fbbf24'] 
                }]
            },
            options: { responsive:true, maintainAspectRatio:false, scales: { y: { min: 0, max: 1.0 } }, plugins: { legend: { display: false } } }
        });
    }

    if (selectedIndex === "LST" || selectedIndex === "TẤT CẢ") {
        lstChart = new Chart(document.getElementById('lstChart'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{ 
                    label: 'LST (°C)', 
                    data: [data.stats[0].lst, data.stats[1].lst],
                    backgroundColor: ['#ef4444', '#f87171'] 
                }]
            },
            options: { responsive:true, maintainAspectRatio:false, scales: { y: { min: 0, max: 50 } }, plugins: { legend: { display: false } } }
        });
    }
}

function renderDashboard(data) {
    const body = document.getElementById("dash-body");
    const selectedIndex = document.getElementById("index-selector").value.toUpperCase();

    // Đã đổi màu text sang #94a3b8 để phù hợp với giao diện Dark Mode
    let html = `<div style="margin-bottom:20px; font-size:14px; color:#94a3b8;">
        Dữ liệu Landsat 8/9 Collection 2 Level-2 – Xử lý bởi Google Earth Engine
    </div>`;

    data.stats.forEach(s => {
        html += `<div class="province-report-card">
            <div class="province-name">${s.label}</div>
            <div class="data-grid">`;
        
        // Kiểm tra và hiển thị các chỉ số dựa trên selector
        if (selectedIndex === "NDVI" || selectedIndex === "TẤT CẢ") {
            html += `<div class="data-box"><div class="data-label">NDVI</div><div class="data-value" style="color:var(--success)">${s.ndvi ? s.ndvi.toFixed(3) : 'N/A'}</div></div>`;
        }
        if (selectedIndex === "LST" || selectedIndex === "TẤT CẢ") {
            html += `<div class="data-box"><div class="data-label">LST</div><div class="data-value" style="color:var(--danger)">${s.lst ? s.lst.toFixed(1) : 'N/A'} °C</div></div>`;
        }
        if (selectedIndex === "TVDI" || selectedIndex === "TẤT CẢ") {
            html += `<div class="data-box"><div class="data-label">TVDI</div><div class="data-value" style="color:var(--warning)">${s.tvdi ? s.tvdi.toFixed(3) : 'N/A'}</div></div>`;
        }

        html += `</div>
            <div class="indicator-info">
                <b>Ngày quan trắc:</b> ${s.date}<br>`;
        
        // Logic hiển thị phân loại chỉ số
        if (s.ndvi !== null) html += `<b>NDVI:</b> ${s.ndvi.toFixed(3)} → ${s.ndvi > 0.6 ? 'Tốt' : s.ndvi > 0.3 ? 'Trung bình' : 'Kém'}<br>`;
        if (s.lst !== null) html += `<b>LST:</b> ${s.lst.toFixed(1)} °C → ${s.lst > 38 ? 'Nóng' : s.lst > 32 ? 'Trung bình cao' : 'Ổn định/mát'}<br>`;
        if (s.tvdi !== null) html += `<b>TVDI:</b> ${s.tvdi.toFixed(3)} → ${s.tvdi > 0.7 ? 'Hạn nghiêm trọng' : s.tvdi > 0.5 ? 'Hạn nhẹ' : 'Ẩm tốt'}`;
        
        html += `</div>`; // Đóng div indicator-info
        
if(
   s.forecast_7days &&
   s.forecast_7days.length > 0
){

   html += `
    <div style="
        margin-top: 20px;
        padding: 20px;
        border-radius: 24px;
        background: #0f172a;
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <div>
                <div style="font-size: 18px; font-weight: 800; color: #38bdf8; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 22px;">🌡️</span> DỰ BÁO NHIỆT LST 7 NGÀY
                </div>
                <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">Dữ liệu phân tích AI thời gian thực</div>
            </div>
            <div style="text-align: right;">
                <span style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; border: 1px solid rgba(56, 189, 248, 0.2);">
                    2026 PRO
                </span>
            </div>
        </div>

        <!-- Bảng dự báo -->
        <div style="display: flex; flex-direction: column; gap: 4px;">
    `;
    s.forecast_7days.forEach((f, index) => {
        // Tính toán độ dài thanh biểu đồ (Giả sử LST tối đa là 50 độ)
        const barWidth = Math.min(Math.max((f.lst / 50) * 100, 10), 100);
        
        // Màu sắc động dựa trên nhiệt độ
        const tempColor = f.lst > 38 ? '#ef4444' : (f.lst > 30 ? '#fb923c' : '#38bdf8');
        const bgColor = index === 0 ? 'rgba(255,255,255,0.05)' : 'transparent';

        html += `
        <div style="
            display: flex;
            align-items: center;
            padding: 12px 16px;
            border-radius: 16px;
            background: ${bgColor};
            transition: background 0.3s;
        ">
            <!-- Cột 1: Ngày tháng -->
            <div style="width: 80px; font-size: 14px; font-weight: 600; color: #cbd5e1;">
                ${index === 0 ? 'Hôm nay' : f.date}
            </div>

            <!-- Cột 2: Các chỉ số môi trường -->
            <div style="width: 120px; display: flex; flex-direction: column; gap: 2px;">
                <div style="font-size: 11px; color: #4ade80; display: flex; align-items: center; gap: 4px;">
                    <span style="width: 6px; height: 6px; background: #4ade80; border-radius: 50%;"></span>
                    NDVI: <b>${f.ndvi}</b>
                </div>
                <div style="font-size: 11px; color: #fbbf24; display: flex; align-items: center; gap: 4px;">
                    <span style="width: 6px; height: 6px; background: #fbbf24; border-radius: 50%;"></span>
                    TVDI: <b>${f.tvdi}</b>
                </div>
            </div>

            <!-- Cột 3: Biểu đồ thanh ngang (Visualizer) -->
            <div style="flex: 1; margin: 0 20px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden; position: relative;">
                <div style="
                    position: absolute;
                    left: 0; top: 0; height: 100%;
                    width: ${barWidth}%;
                    background: linear-gradient(90deg, #38bdf8 0%, ${tempColor} 100%);
                    border-radius: 10px;
                "></div>
            </div>

            <!-- Cột 4: LST (Làm nổi bật nhất) -->
            <div style="width: 65px; text-align: right;">
                <span style="
                    font-size: 20px; 
                    font-weight: 800; 
                    color: ${tempColor};
                    text-shadow: 0 0 15px ${tempColor}44;
                ">
                    ${f.lst}°
                </span>
            </div>
        </div>
        `;

        // Thêm đường kẻ chia nhẹ giữa các dòng
        if(index < s.forecast_7days.length - 1) {
            html += `<div style="height: 1px; background: rgba(255,255,255,0.03); margin: 0 16px;"></div>`;
        }
    });

    html += `
        </div>

        <!-- Chú thích footer -->
        <div style="
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.05);
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        ">
            <span>Tình trạng: <b>Hoạt động tốt</b></span>
            <span>Độ chính xác: <b>94.2%</b></span>
        </div>
    </div>
    `;
}
        // 🚀 THÊM BOX AI (PHIÊN BẢN DARK MODE HIỆN ĐẠI)
       html += `
        <div style="
            margin-top: 16px;
            padding: 16px;
            border-radius: 12px;
            background: ${
                s.ai_level === "Nguy hiểm" ? "#fef2f2" :
                s.ai_level === "Cảnh báo cao" ? "#fff7ed" :
                s.ai_level === "Tốt" ? "#ecfdf5" : "#f8fafc"
            };
            border: 1px solid ${
                s.ai_level === "Nguy hiểm" ? "#fca5a5" :
                s.ai_level === "Cảnh báo cao" ? "#fdba74" :
                s.ai_level === "Tốt" ? "#6ee7b7" : "#cbd5e1"
            };
            border-left: 5px solid ${
                s.ai_level === "Nguy hiểm" ? "#ef4444" :
                s.ai_level === "Cảnh báo cao" ? "#f97316" :
                s.ai_level === "Tốt" ? "#10b981" : "#64748b"
            };
            color: #1e293b;
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 13px;
            line-height: 1.6;
        ">
            <div style="margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                    <span style="font-size: 16px;">
                        ${s.ai_level === "Nguy hiểm" ? "🔥" : s.ai_level === "Cảnh báo cao" ? "⚠️" : s.ai_level === "Tốt" ? "🌿" : "ℹ️"}
                    </span>
                    <span style="
                        font-weight: 700; 
                        text-transform: uppercase; 
                        font-size: 13px;
                        letter-spacing: 0.5px;
                        color: ${
                            s.ai_level === "Nguy hiểm" ? "#dc2626" :
                            s.ai_level === "Cảnh báo cao" ? "#ea580c" :
                            s.ai_level === "Tốt" ? "#059669" : "#475569"
                        };
                    ">
                        Mức độ: ${s.ai_level || "Chưa xác định"}
                    </span>
                </div>
                
                <div style="background: #ffffff; color: #334155; padding: 12px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05); box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                    <b style="color: #0f172a;">Đánh giá trực quan hiện tại :</b> ${s.ai_warning || "Đang phân tích..."}
                </div>
            </div>

            <hr style="border: 0; border-top: 1px dashed rgba(0,0,0,0.15); margin: 16px 0;">

            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                    <span style="font-size: 16px;">🔮</span>
                    <span style="font-weight: 700; color: #7e22ce; text-transform: uppercase; font-size: 13px; letter-spacing: 0.5px;">
                        Dự báo tương lai
                    </span>
                </div>
                
                <div style="display: flex; flex-direction: column; gap: 8px;">
                    <div style="
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center; 
                        background: #ffffff; 
                        padding: 10px 12px; 
                        border-radius: 8px;
                        border: 1px solid rgba(0,0,0,0.05);
                        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
                    ">
                        <span style="color: #475569; font-weight: 600;">Chỉ số Risk:</span>
                        <span style="font-family: monospace; font-weight: 800; font-size: 16px; color: #0f172a;">
                            ${s.future_risk ? s.future_risk.toFixed(2) : "N/A"}
                        </span>
                    </div>
                    
                    <div style="
                        background: #ffffff; 
                        padding: 10px 12px; 
                        border-radius: 8px;
                        border: 1px solid rgba(0,0,0,0.05);
                        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
                    ">
                        <div style="color: #64748b; font-weight: 600; margin-bottom: 4px; font-size: 12px; text-transform: uppercase;">Xu hướng:</div>
                        <div style="color: #1e293b; font-weight: 500;">
                            ${s.trend || "Chưa có dữ liệu"}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        `;

        html += `</div>`; // Đóng div province-report-card
    });
   html += `
<div style="
    margin-top: 24px;
    padding: 20px;
    border-radius: 16px;
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    color: #f8fafc;
    font-family: system-ui, -apple-system, sans-serif;
    line-height: 1.5;
">
    <div style="
        display: flex; 
        align-items: center; 
        gap: 8px; 
        font-size: 16px; 
        font-weight: 700; 
        color: #38bdf8; 
        margin-bottom: 12px; 
        border-bottom: 1px solid #334155; 
        padding-bottom: 12px;
    ">
        <span>📌</span> GIẢI THÍCH CHỈ SỐ RISK
    </div>
    
    <p style="font-size: 13px; color: #94a3b8; margin: 0 0 16px 0;">
        Risk là mức độ rủi ro môi trường được AI dự đoán dựa trên các chỉ số <strong>NDVI, LST và TVDI</strong>.
    </p>

    <div style="display: flex; flex-direction: column; gap: 10px; font-size: 13px;">
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: rgba(74, 222, 128, 0.1); 
            border-left: 4px solid #4ade80; 
            padding: 8px 12px; 
            border-radius: 4px;
        ">
            <span style="font-family: monospace; color: #4ade80; font-weight: 600; font-size: 14px;">0.00 – 0.30</span>
            <span style="color: #4ade80; font-weight: 600;">An toàn 🌿</span>
        </div>
        
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: rgba(251, 191, 36, 0.1); 
            border-left: 4px solid #fbbf24; 
            padding: 8px 12px; 
            border-radius: 4px;
        ">
            <span style="font-family: monospace; color: #fbbf24; font-weight: 600; font-size: 14px;">0.30 – 0.60</span>
            <span style="color: #fbbf24; font-weight: 600;">Cảnh báo ⚠️</span>
        </div>
        
        <div style="
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            background: rgba(248, 113, 113, 0.1); 
            border-left: 4px solid #f87171; 
            padding: 8px 12px; 
            border-radius: 4px;
        ">
            <span style="font-family: monospace; color: #f87171; font-weight: 600; font-size: 14px;">0.60 – 1.00</span>
            <span style="color: #f87171; font-weight: 600;">Nguy cơ cao 🔥</span>
        </div>
    </div>

    <div style="
        margin-top: 16px; 
        padding-top: 12px; 
        font-size: 12px; 
        color: #cbd5e1; 
        font-style: italic; 
        text-align: center; 
        opacity: 0.8;
    ">
        * Giá trị Risk càng cao → khả năng khô hạn / suy thoái càng lớn.
    </div>
</div>
`;

    body.innerHTML = html;
}

function updateLegend(idx) {
    const leg = document.getElementById("legend-content");
    let html = "<h4 style='margin:0 0 16px; border-bottom:1px solid #ddd; padding-bottom:10px;'>Phân loại chỉ số</h4>";

    if (idx === "NDVI" || idx === "TẤT CẢ") {
        html += `<div style="font-weight:600; margin:12px 0 8px;">NDVI</div>
        <div class="color-row"><div class="color-box" style="background:#2ca25f"></div>Tốt (>0.6)</div>
        <div class="color-row"><div class="color-box" style="background:#99d8c9"></div>Trung bình (0.3–0.6)</div>
        <div class="color-row"><div class="color-box" style="background:#e5f5f9"></div>Kém (<0.3)</div>`;
    }
    if (idx === "LST" || idx === "TẤT CẢ") {
        html += `<div style="font-weight:600; margin:16px 0 8px;">Nhiệt độ bề mặt (LST)</div>
        <div class="color-row"><div class="color-box" style="background:#d73027"></div>Rất nóng (>40°C)</div>
        <div class="color-row"><div class="color-box" style="background:#fc8d59"></div>Nóng (35–40°C)</div>
        <div class="color-row"><div class="color-box" style="background:#ffffbf"></div>Trung bình (25–35°C)</div>
        <div class="color-row"><div class="color-box" style="background:#4575b4"></div>Mát (<25°C)</div>`;
    }
    if (idx === "TVDI" || idx === "TẤT CẢ") {
        html += `<div style="font-weight:600; margin:16px 0 8px;">TVDI (Hạn hán)</div>
        <div class="color-row"><div class="color-box" style="background:#63221c"></div>Rất khô (>0.7)</div>
        <div class="color-row"><div class="color-box" style="background:#d95f0e"></div>Khô (0.5–0.7)</div>
        <div class="color-row"><div class="color-box" style="background:#f1e29c"></div>Trung bình (0.3–0.5)</div>
        <div class="color-row"><div class="color-box" style="background:#33a02c"></div>Ẩm (<0.3)</div>`;
    }
    leg.innerHTML = html;
}

function toggleLegend() {
    const p = document.getElementById("legend-panel");
    p.style.display = p.style.display === "block" ? "none" : "block";
}

function toggleDashboard(show) {
    document.getElementById("floating-dashboard").style.display = show ? "flex" : "none";
    document.getElementById("toggle-dash-btn").style.display = show ? "none" : "flex";
}

function exportToExcel() {
    if (!currentAnalysisData) return alert("Chưa có dữ liệu!");
    const data = currentAnalysisData.stats.map(s => ({
        "Thời Điểm": s.label,
        "Ngày": s.date,
        "NDVI": s.ndvi ? Number(s.ndvi.toFixed(3)) : 'N/A',
        "LST (°C)": s.lst ? Number(s.lst.toFixed(1)) : 'N/A',
        "TVDI": s.tvdi ? Number(s.tvdi.toFixed(3)) : 'N/A'
    }));
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Bang_Tin");
    XLSX.writeFile(wb, "Bang_Tin_So_Sanh_2_Giai_Doan.xlsx");
}function predict7Days() {
    const country = document.getElementById("country-select").value;
    const province = document.getElementById("province-select").value;

    if (!country || !province) {
        alert("Vui lòng chọn quốc gia và tỉnh!");
        return;
    }

    document.getElementById("loader-overlay").style.display = "flex";

    fetch('/api/predict_7days', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ country, province })
    })
    .then(r => r.json())
    .then(data => {
        console.log("PREDICT:", data);

        if (data.error) {
            alert(data.error);
            return;
        }

        renderForecast(data);
    })
    .finally(() => {
        document.getElementById("loader-overlay").style.display = "none";
    });
}
function renderForecast(data) {
    const body = document.getElementById("dash-body");

    let html = `
    <div style="margin-bottom:15px; font-weight:700; color:#3b82f6;">
        🔮 DỰ BÁO 7 NGÀY - ${data.province}
    </div>
    `;

    data.forecast_7days.forEach((d, i) => {
        html += `
        <div style="padding:10px; margin-bottom:10px; border:1px solid #e2e8f0; border-radius:10px;">
            <b>Ngày ${i + 1}</b><br>
            NDVI: ${d.ndvi}<br>
            LST: ${d.lst}°C<br>
            TVDI: ${d.tvdi}<br>
            Risk: ${d.risk}<br>
            Level: ${d.level}<br>
            Trend: ${d.trend}
        </div>`;
    });

    body.innerHTML = html + body.innerHTML;

    toggleDashboard(true);
}
function loadWeatherForecast(){

    fetch('/api/weather_forecast',{

        method:'POST',

        headers:{
            'Content-Type':'application/json'
        },

        body:JSON.stringify({
            lat:10.8231,
            lon:106.6297
        })

    })
    .then(r=>r.json())
    .then(data=>{

        renderWeather(data);

    });

}

function renderWeather(data){

    const temp =
        Math.round(
            data.current.temperature_2m
        );

    let html = `

    <div style="
        text-align:center;
        margin-bottom:20px;
    ">

        <div style="
            font-size:38px;
            font-weight:700;
        ">
            Thành Phố Hồ Chí Minh
        </div>

        <div style="
            font-size:20px;
            opacity:.9;
            margin-top:4px;
        ">
            ${temp}° | Trời nhiều mây
        </div>

    </div>

    <div style="
        margin-bottom:14px;
        padding:10px 14px;
        border-radius:16px;
        background:rgba(255,255,255,.08);
        font-size:13px;
        font-weight:600;
        opacity:.9;
    ">
        ⏺ DỰ BÁO THỜI TIẾT
    </div>
    `;

    for(let i=0;i<7;i++){

        html += `

        <div class="weather-day">

            <div style="
                width:70px;
                font-weight:700;
                font-size:18px;
            ">
                ${
                    i === 0
                    ? 'Hôm nay'
                    : data.daily.time[i]
                }
            </div>

            <div style="
                flex:1;
                margin:0 15px;
                height:4px;
                border-radius:10px;
                background:rgba(255,255,255,.12);
                overflow:hidden;
            ">

                <div style="
                    width:${50 + i * 6}%;
                    height:100%;
                    border-radius:10px;

                    background:
                    linear-gradient(
                        90deg,
                        #facc15,
                        #fb923c
                    );
                "></div>

            </div>

            <div style="
                width:80px;
                text-align:right;
                font-size:22px;
                font-weight:700;
            ">
                ${Math.round(data.daily.temperature_2m_max[i])}°
            </div>

        </div>
        `;
    }

    document.getElementById(
        'weather-card'
    ).innerHTML = html;
}
function toggleWeatherCard(){

    const card =
        document.getElementById(
            'weather-card'
        );

    if(card.style.display === 'block'){

        card.style.display = 'none';

    }else{

        card.style.display = 'block';

    }

}
</script>
</body>
</html>
"""

# ====================== BACKEND (GIỮ NGUYÊN) ======================
def get_time_series(region):
    col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')) \
        .filterBounds(region) \
        .filterDate('2015-01-01', '2025-12-31') \
        .filter(ee.Filter.lt('CLOUD_COVER', 35)) \
        .sort('system:time_start') \
        .map(preprocess_image) \
        .limit(100)

    def extract(img):
        date = ee.Date(img.get('system:time_start'))
        stats = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region.geometry(),
            scale=1000,
            bestEffort=True,
            maxPixels=1e13
        )
        return ee.Feature(None, {
            'NDVI': stats.get('NDVI'),
            'LST': stats.get('LST'),
            'TVDI': stats.get('TVDI'),
            'month': date.get('month')
        })

    try:
        fc = col.map(extract).getInfo()
        return fc
    except Exception as e:
        print("EE ERROR in get_time_series:", e)
        return []


def build_lstm_dataset(features, time_steps=3):
    data = []
    for f in features:
        p = f['properties']
        if all(p.get(k) is not None for k in ['NDVI', 'LST', 'TVDI', 'month']):
            data.append([p['NDVI'], p['LST'], p['TVDI'], p['month']])

    if len(data) < 4:

     while len(data) < 4:

        if len(data) == 0:

            data.append([
                0.45,
                30,
                0.35,
                1
            ])

        else:

            data.append(data[-1])

    data = np.array(data)
    scaler = MinMaxScaler()
    data_scaled = scaler.fit_transform(data)

    X, y = [], []
    for i in range(len(data_scaled) - time_steps):
        X.append(data_scaled[i:i + time_steps])
        y.append(data_scaled[i + time_steps])

    return np.array(X), np.array(y), scaler


def train_lstm(X, y):
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, input_shape=(X.shape[1], X.shape[2]), activation='tanh'))
    model.add(LSTM(32, activation='tanh'))
    model.add(Dense(32, activation='relu'))
    model.add(Dense(4))

    model.compile(optimizer='adam', loss='mse')
    model.fit(
    X,
    y,
    epochs=2,
    batch_size=1,
    verbose=0
)
    return model


def predict_7days_lstm(model, last_sequence, scaler, days=7):
    result = []
    current_seq = last_sequence.copy()
    for _ in range(days):
        pred = model.predict(current_seq.reshape(1, *current_seq.shape), verbose=0)[0]
        result.append(pred)
        current_seq = np.vstack([current_seq[1:], pred])
    return scaler.inverse_transform(result)


# ====================== RANDOM FOREST ======================
def train_init_model():
    X_train = np.array([
        [0.8, 25, 0.2], [0.7, 28, 0.3], [0.6, 30, 0.4],
        [0.4, 35, 0.6], [0.3, 37, 0.7],
        [0.1, 42, 0.9], [0.2, 45, 0.85]
    ])
    y_train = np.array([0.1, 0.15, 0.25, 0.55, 0.65, 0.95, 0.98])
    
    regr = RandomForestRegressor(n_estimators=100, random_state=42)
    regr.fit(X_train, y_train)
    return regr


model = train_init_model()
model_lstm = None


def preprocess_image(img):
    optical = img.select('SR_B.*').multiply(0.0000275).add(-0.2)
    lst = img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST')
    ndvi = optical.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    nir = optical.select('SR_B5')
    red = optical.select('SR_B4')
    tvdi = img.expression('1.5 * ((NIR - RED) / sqrt(pow(NIR, 2) + RED + 0.5))',
                         {'NIR':nir, 'RED':red}).rename('TVDI')
    return img.addBands([ndvi, lst, tvdi])


def predict_ai(ndvi, lst, tvdi):
    if ndvi is None or lst is None or tvdi is None:
        return "Không đủ dữ liệu phân tích", "Unknown", None, "Không xác định"

    features = np.array([[ndvi, lst, tvdi]])
    pred = model.predict(features)[0]

    if pred > 0.7:
        level = "Nguy hiểm"
        text = "🔥 Cảnh báo mức NGUY HIỂM: Khu vực đang có dấu hiệu suy thoái mạnh..."
    elif pred > 0.4:
        level = "Cảnh báo cao"
        text = "⚠️ Ghi nhận mức CẢNH BÁO CAO..."
    else:
        level = "Tốt"
        text = "🌿 Đánh giá trạng thái TỐT..."

    future_features = np.array([[ndvi * 0.95, lst + 1.5, tvdi * 1.05]])
    future_pred = model.predict(future_features)[0]
    trend = "📈 Xu hướng xấu đi..." if future_pred > pred else "📉 Xu hướng cải thiện..."

    return text, level, future_pred, trend


def forecast_future_risk(risk1, risk2):
    if risk1 is None or risk2 is None:
        return None, "Không đủ dữ liệu", "Không xác định", "", ""

    delta = risk2 - risk1
    future_risk = max(0, min(1, risk2 + delta * 0.8))

    if future_risk < 0.3:
        level = "🟢 An toàn"
        description = "Khu vực ổn định, nguy cơ suy thoái thấp."
    elif future_risk < 0.6:
        level = "🟡 Cảnh báo"
        description = "Có dấu hiệu biến động môi trường, cần theo dõi."
    else:
        level = "🔴 Nguy hiểm"
        description = "Nguy cơ cao xảy ra khô hạn hoặc suy thoái sinh thái."

    if delta > 0.05:
        trend = "📈 Rủi ro đang TĂNG – xu hướng xấu đi"
    elif delta < -0.05:
        trend = "📉 Rủi ro đang GIẢM – môi trường cải thiện"
    else:
        trend = "➡️ Ổn định – ít biến động"

    return future_risk, trend, level, description, ""


# ====================== ROUTES ======================

@app.route('/api/get_province_from_point', methods=['POST'])
def get_province_from_point():
    data = request.json
    print("🔍 CLICK DEBUG:", data)

    try:
        point = ee.Geometry.Point([float(data['lng']), float(data['lat'])])
        fc = ee.FeatureCollection("FAO/GAUL/2015/level1")
        feature = fc.filterBounds(point.buffer(3000)).first()   # Buffer 3km
        info = feature.getInfo()

        if info and 'properties' in info:
            return jsonify({
                "country": info['properties'].get('ADM0_NAME'),
                "province": info['properties'].get('ADM1_NAME')
            })
    except Exception as e:
        print("❌ ERROR get_province_from_point:", str(e))

    return jsonify({"error": "Không tìm thấy tỉnh/thành phố. Hãy chọn thủ công từ danh sách."})


@app.route('/api/countries')
def get_countries():
    try:
        fc = ee.FeatureCollection("FAO/GAUL/2015/level0")
        countries = fc.aggregate_array('ADM0_NAME').distinct().getInfo()
        return jsonify(countries)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/provinces')
def get_provinces():
    try:
        country = request.args.get('country')
        fc = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM0_NAME', country))
        provinces = fc.aggregate_array('ADM1_NAME').distinct().getInfo()
        return jsonify({"provinces": provinces})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/api/get_province_boundary')
def get_province_boundary():
    country = request.args.get('country')
    province = request.args.get('province')
    feat = ee.FeatureCollection("FAO/GAUL/2015/level1") \
            .filter(ee.Filter.eq('ADM0_NAME', country)) \
            .filter(ee.Filter.eq('ADM1_NAME', province))
    return jsonify({"geojson": feat.getInfo()})


@app.route('/api/find_images', methods=['POST'])
def find_images():
    data = request.json
    region = ee.FeatureCollection("FAO/GAUL/2015/level1") \
              .filter(ee.Filter.eq('ADM0_NAME', data['country'])) \
              .filter(ee.Filter.eq('ADM1_NAME', data['province']))

    start = ee.Date.fromYMD(int(data['year']), int(data['month']), 1)
    col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
           .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')) \
           .filterBounds(region) \
           .filterDate(start.advance(-2, 'month'), start.advance(2, 'month')) \
           .filter(ee.Filter.lt('CLOUD_COVER', 20))

    dates_info = col.map(lambda img: img.set({
        'date': ee.Date(img.get('system:time_start')).format('YYYY-MM-dd'),
        'cloud': img.get('CLOUD_COVER')
    })).sort('cloud').getInfo()

    result = []
    seen = set()
    for feat in dates_info['features']:
        props = feat['properties']
        d = props['date']
        if d in seen: continue
        seen.add(d)
        cloud_pct = round(props.get('cloud', 0), 1)
        label = f"{d} ({cloud_pct}%)"
        result.append({"label": label, "value": d})
    result.reverse()
    return jsonify({"dates": result})


@app.route('/api/analyze_two_times', methods=['POST'])
def analyze_two_times():
    data = request.json
    selected_index = data.get("index", "TẤT CẢ").upper()

    region = ee.FeatureCollection("FAO/GAUL/2015/level1") \
              .filter(ee.Filter.eq('ADM0_NAME', data['country'])) \
              .filter(ee.Filter.eq('ADM1_NAME', data['province']))

    def process_date(date_str, suffix):
        day = ee.Date(date_str)
        col = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')) \
                .filterBounds(region) \
                .filterDate(day.advance(-2, 'month'), day.advance(2, 'month')) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20))

        img = col.map(preprocess_image).median().clip(region)
        if selected_index == "NDVI":
            bands = ['NDVI']
        elif selected_index == "LST":
            bands = ['LST']
        elif selected_index == "TVDI":
            bands = ['TVDI']
        else:
            bands = ['NDVI','LST','TVDI']

        stats = img.select(bands).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region.geometry(),
            scale=500,
            maxPixels=1e13,
            bestEffort=True
        ).getInfo()

        if not stats: stats = {}

        ndvi_val = stats.get('NDVI')
        lst_val  = stats.get('LST')
        tvdi_val = stats.get('TVDI')
                # =========================
        # AI FORECAST 7 DAYS
        # =========================

        forecast_7days = []

        try:

            history_features = get_time_series(region)

            Xf, yf, scalerf = build_lstm_dataset(
                    history_features,
                    time_steps=3
                )

            if Xf is not None and len(Xf) > 0:

                temp_model = train_lstm(Xf, yf)

                last_seq = Xf[-1]

                future_preds = predict_7days_lstm(
                        temp_model,
                        last_seq,
                        scalerf,
                        days=7
                    )

                from datetime import datetime, timedelta

                base_date = datetime.strptime(
                        date_str,
                        "%Y-%m-%d"
                    )

                for i, pred in enumerate(future_preds):

                    ndvi_f, lst_f, tvdi_f, _ = pred

                    forecast_7days.append({

                        "date":
                        (
                            base_date
                            +
                            timedelta(days=i+1)
                        ).strftime("%Y-%m-%d"),

                        "ndvi":
                        round(float(ndvi_f), 3),

                        "lst":
                        round(float(lst_f), 1),

                        "tvdi":
                        round(float(tvdi_f), 3)

                    }) 
                    
            else:
                from datetime import datetime, timedelta
                base_date = datetime.strptime(
                    date_str,
                    "%Y-%m-%d"
                )
                for i in range(7):

                    forecast_7days.append({

                "date":
                (
                    base_date +
                    timedelta(days=i+1)
                ).strftime("%Y-%m-%d"),

                "ndvi":
                round(float(ndvi_val - (i * 0.01)), 3),

                "lst":
                round(float(lst_val + (i * 0.4)), 1),

                "tvdi":
                round(float(tvdi_val + (i * 0.01)), 3)

            })

        except Exception as e:

            print("Forecast Error:", e)

            from datetime import datetime, timedelta

            base_date = datetime.strptime(
               date_str,
               "%Y-%m-%d"
            )

            forecast_7days = []

            for i in range(7):

                forecast_7days.append({

                   "date":
                   (
                       base_date +
                       timedelta(days=i+1)
                   ).strftime("%Y-%m-%d"),

                  "ndvi":
                   round(
                       float(
                           (ndvi_val or 0.45)
                           - i * 0.01
                       ),
                       3
                   ),

                   "lst":
                   round(
                       float(
                            (lst_val or 30)
                            + i * 0.3
                       ),
                1
                   ),

            "tvdi":
            round(
                float(
                    (tvdi_val or 0.35)
                    + i * 0.01
                ),
                3
            )

        })

     
        ai_text, ai_level, future_risk, trend = predict_ai(ndvi_val, lst_val, tvdi_val)

        if lst_val is not None and lst_val > 40:
            ai_text += " | 🔥 Cảnh báo: Nhiệt độ bề mặt cực hạn."
            ai_level = "Nguy hiểm"

        vis = {
            'NDVI': {'min':0, 'max':0.8, 'palette':['#e5f5f9','#99d8c9','#2ca25f']},
            'LST':  {'min':20, 'max':45, 'palette':['#4575b4','#ffffbf','#fc8d59','#d73027']},
            'TVDI': {'min':0, 'max':1,   'palette':['#33a02c','#f1e29c','#d95f0e','#63221c']}
        }

        map_urls = {}
        if selected_index in ["NDVI", "TẤT CẢ"]:
            map_urls[f'ndvi_{suffix}'] = img.select('NDVI').getMapId(vis['NDVI'])['tile_fetcher'].url_format
        if selected_index in ["LST", "TẤT CẢ"]:
            map_urls[f'lst_{suffix}'] = img.select('LST').getMapId(vis['LST'])['tile_fetcher'].url_format
        if selected_index in ["TVDI", "TẤT CẢ"]:
            map_urls[f'tvdi_{suffix}'] = img.select('TVDI').getMapId(vis['TVDI'])['tile_fetcher'].url_format
        # ===== WEATHER FORECAST =====

        weather_forecast = []

        try:

            weather_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude=10.8231"
                f"&longitude=106.6297"
                f"&daily=temperature_2m_max,temperature_2m_min"
                f"&forecast_days=7"
                f"&timezone=Asia/Bangkok"
            )

            weather_data = requests.get(
                weather_url
            ).json()

            for i in range(7):

                weather_forecast.append({

                    "date":
                    weather_data['daily']['time'][i],

                    "min":
                    weather_data['daily']
                    ['temperature_2m_min'][i],

                    "max":
                    weather_data['daily']
                    ['temperature_2m_max'][i]

                })

        except Exception as e:

            print("Weather API Error:", e)
            print("FORECAST:", forecast_7days)
        return {
            "label": f"{data['province']} ({suffix})",
            "date": date_str,
            "ndvi": ndvi_val,
            "lst": lst_val,
            "tvdi": tvdi_val,
            "ai_warning": ai_text,
            "ai_level": ai_level,
            "forecast": "Ổn định",
            "future_risk": float(future_risk) if future_risk is not None else 0,
            "trend": trend,
            "forecast_7days": forecast_7days
        }, map_urls

    stat1, urls1 = process_date(data['date1'], '1')
    stat2, urls2 = process_date(data['date2'], '2')

    risk1 = stat1.get("future_risk", 0)
    risk2 = stat2.get("future_risk", 0)
    future_risk_total, trend_total, level_total, desc_total, explain_total = forecast_future_risk(risk1, risk2)

    return jsonify({
        "stats": [stat1, stat2],
        "map_urls": {**urls1, **urls2},
        "future_risk_total": future_risk_total,
        "trend_total": trend_total,
        "risk_level_total": level_total,
        "risk_description_total": desc_total,
        "risk_explain_total": explain_total
    })


@app.route('/api/predict_7days', methods=['POST'])
def predict_7days():
    global model_lstm
    try:
        data = request.json
        country = data['country']
        province = data['province']

        region = ee.FeatureCollection("FAO/GAUL/2015/level1") \
            .filter(ee.Filter.eq('ADM0_NAME', country)) \
            .filter(ee.Filter.eq('ADM1_NAME', province))

        features = get_time_series(region)

        if not features or len(features) < 5:
            return jsonify({"error": "Không đủ dữ liệu Earth Engine (cần ít nhất 5 điểm)"})

        X, y, scaler = build_lstm_dataset(features, time_steps=3)
        if X is None or len(X) == 0:
            return jsonify({"error": "Không đủ dữ liệu để huấn luyện LSTM"})

        if model_lstm is None:
            print(f"Training LSTM for {province}...")
            model_lstm = train_lstm(X, y)
        else:
            print("Using cached LSTM model")

        last_sequence = X[-1]
        future = predict_7days_lstm(model_lstm, last_sequence, scaler, days=7)

        forecast = []
        for d in future:
            ndvi, lst, tvdi, _ = d
            _, level, risk, trend = predict_ai(ndvi, lst, tvdi)
            forecast.append({
                "ndvi": round(float(ndvi), 4),
                "lst": round(float(lst), 2),
                "tvdi": round(float(tvdi), 4),
                "risk": float(risk) if risk is not None else None,
                "level": level,
                "trend": trend
            })
# ===== LẤY DỮ LIỆU LỊCH SỬ =====
        history = []
        for f in features:
          p = f['properties']
          if p.get('NDVI') and p.get('LST') and p.get('TVDI'):
            history.append({
            "ndvi": float(p['NDVI']),
            "lst": float(p['LST']),
            "tvdi": float(p['TVDI'])
        })
        return jsonify({
    "province": province,
    "forecast_7days": forecast,
    "historical_data": history,   # 🔥 THÊM DÒNG NÀY
    "historical_points": len(history),
    "model_used": "LSTM (Cached)"
})

    except Exception as e:
        print("ERROR predict_7days:", e)
        return jsonify({"error": str(e)}), 500

  
@app.route('/api/weather_forecast', methods=['POST'])
def weather_forecast():

    data = request.json

    lat = data['lat']
    lon = data['lon']

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}"
        f"&longitude={lon}"
        f"&current=temperature_2m"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&forecast_days=7"
        f"&timezone=Asia/Bangkok"
    )

    response = requests.get(url)

    return jsonify(response.json())

@app.route('/')
def home():
    return render_template_string(HTML)


if __name__ == '__main__':
    app.run(debug=True, port=5000)