from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import json
import os
import ee

if "GEE_KEY" in os.environ:
    # chạy trên server
    key_json = json.loads(os.environ["GEE_KEY"])
    credentials = ee.ServiceAccountCredentials(
        key_json["client_email"],
        key_data=key_json
    )
else:
    # chạy local
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    KEY_PATH = os.path.join(BASE_DIR, "key.json")

    credentials = ee.ServiceAccountCredentials(
        "earth-engine-app@duan1-470914.iam.gserviceaccount.com",
        KEY_PATH
    )

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
    <title>WebGIS | So sánh 2 giai đoạn – Cùng khu vực</title>
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
        .scroll-area { padding:20px; overflow-y:auto; flex:1; background:#f8fafc; }
        .step-card { background:white; border-radius:16px; padding:20px; margin-bottom:20px; border:1px solid #e2e8f0; transition:0.3s; }
        .step-card:hover { border-color:var(--accent); box-shadow:0 10px 20px rgba(0,0,0,0.02); }
        .step-header { display:flex; align-items:center; gap:10px; margin-bottom:16px; font-weight:700; font-size:13px; color:var(--primary); text-transform:uppercase; border-bottom:1px solid #f1f5f9; padding-bottom:8px; }
        select, button { width:100%; padding:12px 16px; border-radius:10px; border:1px solid #e2e8f0; font-family:inherit; font-size:14px; transition:all 0.2s; outline:none; }
        select:focus { border-color:var(--accent); box-shadow:0 0 0 3px rgba(59,130,246,0.1); }
        .btn-primary { background:var(--primary); color:white; font-weight:600; cursor:pointer; border:none; display:flex; align-items:center; justify-content:center; gap:8px; margin-top:10px; }
        .btn-analyze { background:var(--accent); padding:16px; font-weight:700; box-shadow:0 10px 15px -3px rgba(59,130,246,0.3); border:none; cursor:pointer; color:white; margin-top:15px; }
        .btn-analyze:hover { transform:translateY(-2px); box-shadow:0 15px 20px -3px rgba(59,130,246,0.4); }
        .time-row { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:8px; }
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
        .toast { position:absolute; bottom:100px; left:50%; transform:translateX(-50%); background:#1e293b; color:white; padding:12px 24px; border-radius:12px; z-index:2000; display:none; font-weight:500; }
    </style>
</head>
<body>

<div id="loader-overlay" class="loading-screen">
    <div class="loader"></div>
    <h2 style="margin-top:30px; letter-spacing:2px; font-weight:800;">WEBGIS PROCESSING</h2>
    <p style="opacity:0.75; font-size:14px; margin-top:12px;">Đang tính toán chỉ số từ Landsat...</p>
</div>

<div id="sidebar">
    <div class="brand">
        <i class="fa-solid fa-map-location-dot"></i>
        <div>
            <h1>WEBGIS</h1>
            <div style="font-size:10px; opacity:0.6; font-weight:600; text-transform:uppercase;">So sánh 2 giai đoạn – Cùng khu vực</div>
        </div>
    </div>

    <div class="scroll-area">
        <div class="step-card">
            <div class="step-header"><i class="fa-solid fa-layer-group"></i> Khu vực</div>
            <select id="country-select" onchange="loadProvinces()"><option value="">-- Quốc gia --</option></select>
            <div style="margin-top:16px;">
                <h4 style="margin:0 0 12px 0; font-size:14px; color:var(--primary);">Tỉnh/Thành phố</h4>
                <select id="province-select" onchange="updateBoundary(this.value)">
                    <option value="">-- Chọn tỉnh --</option>
                </select>
            </div>
            <small style="color:#64748b; margin-top:8px; display:block;">Hoặc click trực tiếp lên bản đồ để chọn tỉnh</small>
        </div>

        <div class="step-card">
            <div class="step-header"><i class="fa-solid fa-clock"></i> Giai đoạn 1</div>
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
                <i class="fa-solid fa-satellite-dish"></i> Quét ảnh
            </button>
            <select id="image-date1-select" style="margin-top:10px; display:none; border-color:var(--accent); font-weight:700; color:var(--accent);"></select>
        </div>

        <div class="step-card">
            <div class="step-header"><i class="fa-solid fa-clock"></i> Giai đoạn 2</div>
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
                <i class="fa-solid fa-satellite-dish"></i> Quét ảnh
            </button>
            <select id="image-date2-select" style="margin-top:10px; display:none; border-color:var(--accent); font-weight:700; color:var(--accent);"></select>
        </div>

        <div class="step-card">
            <div class="step-header"><i class="fa-solid fa-flask-vial"></i> Cấu hình phân tích</div>
            <select id="index-selector">
                <option value="TẤT CẢ">NDVI + LST + TVDI</option>
                <option value="NDVI">Chỉ số thực vật (NDVI)</option>
                <option value="LST">Nhiệt độ bề mặt (LST)</option>
                <option value="TVDI">Chỉ số hạn hán (TVDI)</option>
            </select>
            <button class="btn-analyze" onclick="startProcessing()">
                <i class="fa-solid fa-wand-magic-sparkles"></i> SO SÁNH 2 GIAI ĐOẠN
            </button>
        </div>

        <div class="step-card">
            <div class="step-header"><i class="fa-solid fa-chart-simple"></i> So sánh kết quả</div>
            <div style="display: flex; flex-direction: column; gap: 40px;">
                <div>
                    <div style="text-align:center; font-weight:700; font-size:15px; color:#10b981; margin-bottom:8px;">NDVI</div>
                    <div class="chart-wrapper"><canvas id="ndviChart"></canvas></div>
                </div>
                <div>
                    <div style="text-align:center; font-weight:700; font-size:15px; color:#f59e0b; margin-bottom:8px;">TVDI</div>
                    <div class="chart-wrapper"><canvas id="tvdiChart"></canvas></div>
                </div>
                <div>
                    <div style="text-align:center; font-weight:700; font-size:15px; color:#ef4444; margin-bottom:8px;">LST (°C)</div>
                    <div class="chart-wrapper"><canvas id="lstChart"></canvas></div>
                </div>
            </div>
        </div>
    </div>
</div>

<div id="map-container">
    <div id="map"></div>
    
    <button class="legend-toggle-btn" onclick="toggleLegend()"><i class="fa-solid fa-list-ul"></i></button>
    <button class="focus-toggle-btn" id="focus-btn" onclick="toggleFocusMode()"><i class="fa-solid fa-moon"></i></button>
    
    <div id="legend-panel" class="legend-panel">
        <div id="legend-content"></div>
    </div>

    <button id="toggle-dash-btn" onclick="toggleDashboard(true)"><i class="fa-solid fa-file-waveform"></i></button>

    <div id="floating-dashboard" class="floating-dashboard">
        <div class="dash-header">
            <span><i class="fa-solid fa-table-list"></i> BẢNG TIN</span>
            <div style="display:flex; align-items:center; gap:12px;">
                <button onclick="exportToExcel()"><i class="fa-solid fa-file-excel"></i> TẢI EXCEL</button>
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
// Global variables
var map, baseSatellite, boundaryLayer, layerControl, indexLayers = {};
var currentAnalysisData = null;
var ndviChart, tvdiChart, lstChart;
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
        alert(`Vui lòng chọn đầy đủ thông tin cho Giai đoạn ${which}`);
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
            alert(`Không tìm thấy ảnh Landsat sạch mây cho Giai đoạn ${which}.`);
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
        alert("Vui lòng chọn ngày ảnh cho cả hai giai đoạn!");
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
                const phaseText = phaseNum === '1' ? `Giai đoạn 1 - ${dateMap['1']}` : `Giai đoạn 2 - ${dateMap['2']}`;
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
        toggleDashboard(true);
    })
    .finally(() => document.getElementById("loader-overlay").style.display = "none");
}

function renderChart(data) {
    if (ndviChart) ndviChart.destroy();
    if (tvdiChart) tvdiChart.destroy();
    if (lstChart) lstChart.destroy();

    const labels = [data.stats[0].label, data.stats[1].label];

    ndviChart = new Chart(document.getElementById('ndviChart'), {
        type: 'bar', data: { labels: labels, datasets: [{ label: 'NDVI', data: [data.stats[0].ndvi, data.stats[1].ndvi], backgroundColor: ['#10b981', '#ef4444'] }] },
        options: { responsive:true, maintainAspectRatio:false, scales: { y: { min: -0.5, max: 1.0 } }, plugins: { legend: { display: false } } }
    });

    tvdiChart = new Chart(document.getElementById('tvdiChart'), {
        type: 'bar', data: { labels: labels, datasets: [{ label: 'TVDI', data: [data.stats[0].tvdi, data.stats[1].tvdi], backgroundColor: ['#f59e0b', '#ef4444'] }] },
        options: { responsive:true, maintainAspectRatio:false, scales: { y: { min: -0.1, max: 1.0 } }, plugins: { legend: { display: false } } }
    });

    lstChart = new Chart(document.getElementById('lstChart'), {
        type: 'bar', data: { labels: labels, datasets: [{ label: 'LST (°C)', data: [data.stats[0].lst, data.stats[1].lst], backgroundColor: ['#3b82f6', '#f59e0b'] }] },
        options: { responsive:true, maintainAspectRatio:false, scales: { y: { min: 0, max: 50 } }, plugins: { legend: { display: false } } }
    });
}

function renderDashboard(data) {
    const body = document.getElementById("dash-body");
    let html = `<div style="margin-bottom:20px; font-size:14px; color:#475569;">
        Dữ liệu Landsat 8/9 Collection 2 Level-2 – Xử lý bởi Google Earth Engine
    </div>`;

    data.stats.forEach(s => {
        html += `
        <div class="province-report-card">
            <div class="province-name">${s.label}</div>
            <div class="data-grid">
                <div class="data-box"><div class="data-label">NDVI</div><div class="data-value" style="color:var(--success)">${s.ndvi.toFixed(3)}</div></div>
                <div class="data-box"><div class="data-label">LST</div><div class="data-value" style="color:var(--danger)">${s.lst.toFixed(1)} °C</div></div>
                <div class="data-box"><div class="data-label">TVDI</div><div class="data-value" style="color:var(--warning)">${s.tvdi.toFixed(3)}</div></div>
            </div>
            <div class="indicator-info">
                <b>Ngày quan trắc:</b> ${s.date}<br>
                <b>NDVI:</b> ${s.ndvi.toFixed(3)} → ${s.ndvi > 0.6 ? 'Tốt' : s.ndvi > 0.3 ? 'Trung bình' : 'Kém'}<br>
                <b>LST:</b> ${s.lst.toFixed(1)} °C → ${s.lst > 38 ? 'Nóng' : s.lst > 32 ? 'Trung bình cao' : 'Ổn định/mát'}<br>
                <b>TVDI:</b> ${s.tvdi.toFixed(3)} → ${s.tvdi > 0.7 ? 'Hạn nghiêm trọng' : s.tvdi > 0.5 ? 'Hạn nhẹ' : 'Ẩm tốt'}
            </div>
        </div>`;
    });

    const dNDVI = (data.stats[1].ndvi - data.stats[0].ndvi).toFixed(3);
    const dTVDI = (data.stats[1].tvdi - data.stats[0].tvdi).toFixed(3);
    const dLST  = (data.stats[1].lst  - data.stats[0].lst).toFixed(1);

    html += `
    <div class="province-report-card" style="background:#f0f9ff; border-left:6px solid #3b82f6;">
        <div class="province-name" style="color:#1e40af;">Phân tích sự biến đổi giữa hai giai đoạn</div>
        <div class="indicator-info" style="border-left:none; background:white;">
            <p><b>NDVI:</b> Từ ${data.stats[0].ndvi.toFixed(3)} → thay đổi <b>${dNDVI}</b></p>
            <p><b>TVDI:</b> Từ ${data.stats[0].tvdi.toFixed(3)} → thay đổi <b>${dTVDI}</b></p>
            <p><b>LST:</b> Từ ${data.stats[0].lst.toFixed(1)}°C → thay đổi <b>${dLST}°C</b></p>
            <p><b>Tổng kết:</b> Khu vực đang có những biến đổi rõ nét về thảm thực vật và nhiệt độ bề mặt.</p>
        </div>
    </div>`;

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
        "Giai đoạn": s.label,
        "Ngày": s.date,
        "NDVI": Number(s.ndvi.toFixed(3)),
        "LST (°C)": Number(s.lst.toFixed(1)),
        "TVDI": Number(s.tvdi.toFixed(3))
    }));
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Bang_Tin");
    XLSX.writeFile(wb, "Bang_Tin_So_Sanh_2_Giai_Doan.xlsx");
}
</script>
</body>
</html>
"""

# ====================== BACKEND (GIỮ NGUYÊN) ======================
def preprocess_image(img):
    optical = img.select('SR_B.*').multiply(0.0000275).add(-0.2)
    lst = img.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST')
    ndvi = optical.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    nir, red = optical.select('SR_B5'), optical.select('SR_B4')
    tvdi = img.expression('1.5 * ((NIR - RED) / sqrt(pow(NIR, 2) + RED + 0.5))', {'NIR':nir, 'RED':red}).rename('TVDI')
    return img.addBands([ndvi, lst, tvdi])

@app.route('/api/get_province_from_point', methods=['POST'])
def get_province_from_point():
    data = request.json
    point = ee.Geometry.Point([data['lng'], data['lat']])
    fc = ee.FeatureCollection("FAO/GAUL/2015/level1")
    feature = fc.filterBounds(point).first()
    info = feature.getInfo()
    if info and 'properties' in info:
        return jsonify({
            "country": info['properties'].get('ADM0_NAME'),
            "province": info['properties'].get('ADM1_NAME')
        })
    return jsonify({"error": "Không tìm thấy"})

@app.route('/api/countries')
def get_countries():
    fc = ee.FeatureCollection("FAO/GAUL/2015/level0")
    return jsonify(fc.aggregate_array('ADM0_NAME').sort().getInfo())

@app.route('/api/provinces')
def get_provinces():
    country = request.args.get('country')
    fc = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM0_NAME', country))
    provinces = fc.aggregate_array('ADM1_NAME').getInfo()
    return jsonify({"provinces": list(set(provinces))})

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
          .filterDate(start, start.advance(1, 'month')) \
          .filter(ee.Filter.lt('CLOUD_COVER', 30))

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
    region = ee.FeatureCollection("FAO/GAUL/2015/level1") \
             .filter(ee.Filter.eq('ADM0_NAME', data['country'])) \
             .filter(ee.Filter.eq('ADM1_NAME', data['province']))

    def process_date(date_str, suffix):
        day = ee.Date(date_str)
        img = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
               .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')) \
               .filterBounds(region) \
               .filterDate(day, day.advance(1, 'day')) \
               .map(preprocess_image) \
               .median() \
               .clip(region)

        stats = img.select(['NDVI','LST','TVDI']) \
                   .reduceRegion(ee.Reducer.mean(), region.geometry(), 30) \
                   .getInfo()

        vis = {
            'NDVI': {'min':0, 'max':0.8, 'palette':['#e5f5f9','#99d8c9','#2ca25f']},
            'LST':  {'min':20, 'max':45, 'palette':['#4575b4','#ffffbf','#fc8d59','#d73027']},
            'TVDI': {'min':0, 'max':1,   'palette':['#33a02c','#f1e29c','#d95f0e','#63221c']}
        }

        map_urls = {
            f'ndvi_{suffix}': img.select('NDVI').getMapId(vis['NDVI'])['tile_fetcher'].url_format,
            f'lst_{suffix}':  img.select('LST').getMapId(vis['LST'])['tile_fetcher'].url_format,
            f'tvdi_{suffix}': img.select('TVDI').getMapId(vis['TVDI'])['tile_fetcher'].url_format
        }

        return {
            "label": f"{data['province']} (Giai đoạn {suffix})",
            "date": date_str,
            "ndvi": stats.get('NDVI', 0),
            "lst":  stats.get('LST',  0),
            "tvdi": stats.get('TVDI', 0)
        }, map_urls

    stat1, urls1 = process_date(data['date1'], '1')
    stat2, urls2 = process_date(data['date2'], '2')

    return jsonify({
        "stats": [stat1, stat2],
        "map_urls": {**urls1, **urls2}
    })

@app.route('/')
def home():
    return render_template_string(HTML)

if __name__ == '__main__':
    app.run(debug=True, port=5000)