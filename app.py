import requests
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="台灣六都生活便利性評分系統 V7.7 (本地快取版)", layout="wide")
st.title("🏙️ 台灣六都生活便利性評分系統 (本地快取版)")

# --- 0. 本地快取數據庫配置 ---
CACHE_FILE = "osm_data_cache.json"
CACHE_EXPIRY_HOURS = 24

def load_or_initialize_cache():
    """加載或初始化本地快取"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                # 檢查快取是否過期
                if 'timestamp' in cache_data:
                    cache_time = datetime.fromisoformat(cache_data['timestamp'])
                    if datetime.now() - cache_time < timedelta(hours=CACHE_EXPIRY_HOURS):
                        st.success(f"✅ 使用本地快取數據 (更新於: {cache_data['timestamp']})")
                        return cache_data
        except:
            pass
    
    # 初始化默認快取
    return {
        "timestamp": datetime.now().isoformat(),
        "data": {}
    }

def save_cache(cache_data):
    """保存快取到本地"""
    cache_data['timestamp'] = datetime.now().isoformat()
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

# 加載快取
cache_data = load_or_initialize_cache()

# --- 1. 六都 152 個行政區完整資料庫 ---
@st.cache_data
def load_town_base_info():
    raw_cities = {
        "臺北市": [
            ("大安區", 11.36, 25.026, 121.543), ("信義區", 11.20, 25.033, 121.564),
            ("中正區", 7.60, 25.032, 121.518), ("中山區", 13.68, 25.068, 121.533),
            ("萬華區", 8.85, 25.029, 121.499), ("松山區", 9.28, 25.060, 121.560),
            ("大同區", 5.68, 25.063, 121.513), ("內湖區", 31.58, 25.069, 121.589),
            ("南港區", 21.84, 25.055, 121.606), ("文山區", 31.50, 24.998, 121.570),
            ("士林區", 62.37, 25.093, 121.526), ("北投區", 56.82, 25.132, 121.500)
        ],
        "新北市": [
            ("板橋區", 23.14, 25.011, 121.465), ("三重區", 16.32, 25.062, 121.498),
            ("中和區", 20.14, 24.999, 121.498), ("永和區", 5.71, 25.008, 121.516),
            ("新莊區", 19.74, 25.036, 121.445), ("新店區", 120.22, 24.968, 121.541),
            ("土城區", 29.56, 24.973, 121.444), ("蘆洲區", 7.44, 25.084, 121.474),
            ("汐止區", 71.24, 25.067, 121.659), ("樹林區", 33.12, 24.991, 121.420),
            ("淡水區", 70.65, 25.170, 121.442), ("林口區", 54.15, 25.077, 121.391),
            ("五股區", 34.86, 25.084, 121.438), ("泰山區", 19.16, 25.059, 121.431),
            ("三峽區", 191.15, 24.933, 121.373), ("鶯歌區", 21.12, 24.954, 121.355),
            ("八里區", 39.49, 25.147, 121.399), ("深坑區", 20.58, 25.003, 121.616),
            ("石碇區", 144.35, 24.992, 121.657), ("坪林區", 170.84, 24.937, 121.711),
            ("烏來區", 321.13, 24.864, 121.551), ("瑞芳區", 70.73, 25.109, 121.805),
            ("萬里區", 63.37, 25.175, 121.689), ("金山區", 49.21, 25.222, 121.638),
            ("石門區", 31.24, 25.290, 121.568), ("三芝區", 65.99, 25.257, 121.500),
            ("雙溪區", 146.25, 25.036, 121.863), ("貢寮區", 99.97, 25.022, 121.908),
            ("平溪區", 71.34, 25.025, 121.741)
        ],
        "桃園市": [
            ("桃園區", 34.80, 24.995, 121.306), ("中壢區", 76.52, 24.966, 121.224),
            ("平鎮區", 31.28, 24.945, 121.218), ("八德區", 33.71, 24.963, 121.294),
            ("蘆竹區", 75.50, 25.052, 121.288), ("龜山區", 72.01, 25.001, 121.338),
            ("大溪區", 105.12, 24.880, 121.287), ("楊梅區", 89.12, 24.909, 121.145),
            ("大園區", 87.39, 25.063, 121.196), ("龍潭區", 75.23, 24.864, 121.216),
            ("新屋區", 85.02, 24.972, 121.033), ("觀音區", 117.32, 25.035, 121.082),
            ("復興區", 350.78, 24.821, 121.352)
        ],
        "臺中市": [
            ("西屯區", 39.85, 24.182, 120.623), ("北屯區", 62.70, 24.181, 120.697),
            ("南屯區", 31.26, 24.137, 120.640), ("北區", 6.93, 24.156, 120.682),
            ("西區", 5.70, 24.141, 120.667), ("東區", 9.28, 24.136, 120.693),
            ("南區", 6.81, 24.118, 120.662), ("中區", 0.88, 24.143, 120.683),
            ("豐原區", 41.18, 24.252, 120.720), ("大里區", 32.45, 24.102, 120.677),
            ("太平區", 120.75, 24.127, 120.718), ("清水區", 64.17, 24.269, 120.538),
            ("沙鹿區", 40.46, 24.234, 120.565), ("大甲區", 58.51, 24.349, 120.624),
            ("梧棲區", 16.61, 24.255, 120.531), ("烏日區", 43.40, 24.105, 120.623),
            ("神岡區", 35.04, 24.257, 120.662), ("大雅區", 32.41, 24.229, 120.648),
            ("潭子區", 25.84, 24.212, 120.705), ("后里區", 58.94, 24.305, 120.720),
            ("東勢區", 117.48, 24.259, 120.829), ("外埔區", 42.45, 24.332, 120.654),
            ("大安區", 27.40, 24.346, 120.585), ("大肚區", 37.00, 24.153, 120.541),
            ("龍井區", 26.67, 24.192, 120.546), ("石岡區", 18.21, 24.275, 120.778),
            ("新社區", 68.89, 24.229, 120.811), ("和平區", 1037.82, 24.264, 121.002)
        ],
        "臺南市": [
            ("安平區", 11.06, 22.992, 120.168), ("東區", 13.44, 22.984, 120.222),
            ("北區", 10.43, 23.006, 120.210), ("南區", 27.26, 22.960, 120.184),
            ("中西區", 6.26, 22.992, 120.199), ("永康區", 40.05, 23.025, 120.254),
            ("安南區", 107.20, 23.047, 120.185), ("新營區", 38.54, 23.308, 120.317),
            ("鹽水區", 52.26, 23.320, 120.266), ("白河區", 126.40, 23.351, 120.416),
            ("柳營區", 61.29, 23.277, 120.332), ("後壁區", 72.22, 23.366, 120.362),
            ("佳里區", 38.94, 23.165, 120.177), ("麻豆區", 53.97, 23.181, 120.248),
            ("新化區", 62.05, 23.038, 120.342), ("善化區", 55.30, 23.132, 120.290),
            ("學甲區", 53.99, 23.232, 120.181), ("六甲區", 67.54, 23.232, 120.348),
            ("官田區", 70.79, 23.193, 120.318), ("西港區", 33.77, 23.123, 120.203),
            ("七股區", 110.15, 23.141, 120.140), ("將軍區", 41.97, 23.204, 120.155),
            ("北門區", 44.10, 23.267, 120.124), ("安定區", 31.27, 23.121, 120.237),
            ("山上區", 27.87, 23.084, 120.353), ("玉井區", 76.36, 23.124, 120.461),
            ("楠西區", 109.63, 23.174, 120.485), ("南化區", 171.51, 23.043, 120.541),
            ("左鎮區", 74.90, 23.058, 120.407), ("仁德區", 50.77, 22.972, 120.252),
            ("歸仁區", 55.79, 22.954, 120.294), ("關廟區", 53.64, 22.963, 120.328),
            ("龍崎區", 64.08, 22.966, 120.361), ("大內區", 70.32, 23.119, 120.351),
            ("下營區", 33.53, 23.228, 120.264)
        ],
        "高雄市": [
            ("三民區", 19.78, 22.643, 120.328), ("苓雅區", 8.15, 22.621, 120.329),
            ("左營區", 19.38, 22.690, 120.301), ("鼓山區", 14.74, 22.639, 120.275),
            ("前鎮區", 19.12, 22.597, 120.322), ("鳳山區", 26.75, 22.626, 120.359),
            ("小港區", 45.64, 22.565, 120.338), ("新興區", 1.97, 22.627, 120.304),
            ("前金區", 1.85, 22.627, 120.293), ("鹽埕區", 1.41, 22.623, 120.283),
            ("楠梓區", 25.83, 22.727, 120.311), ("岡山區", 47.94, 22.791, 120.295),
            ("橋頭區", 18.31, 22.757, 120.305), ("路竹區", 48.43, 22.855, 120.261),
            ("旗津區", 1.46, 22.561, 120.300), ("大寮區", 71.04, 22.605, 120.395),
            ("林園區", 32.29, 22.508, 120.396), ("鳥松區", 24.59, 22.659, 120.363),
            ("大樹區", 66.98, 22.693, 120.431), ("仁武區", 36.08, 22.701, 120.347),
            ("大社區", 26.58, 22.730, 120.348), ("燕巢區", 65.39, 22.793, 120.362),
            ("田寮區", 92.68, 22.868, 120.360), ("阿蓮區", 34.62, 22.885, 120.327),
            ("茄萣區", 15.76, 22.906, 120.181), ("永安區", 22.61, 22.818, 120.225),
            ("彌陀區", 14.78, 22.782, 120.247), ("梓官區", 11.60, 22.760, 120.267),
            ("旗山區", 94.61, 22.888, 120.484), ("美濃區", 120.03, 22.898, 120.542),
            ("六龜區", 194.16, 22.997, 120.635), ("甲仙區", 124.03, 23.082, 120.591),
            ("杉林區", 104.00, 22.973, 120.540), ("內門區", 95.62, 22.919, 120.456),
            ("茂林區", 194.00, 22.884, 120.724), ("桃源區", 928.98, 23.159, 120.781),
            ("那瑪夏區", 252.98, 23.267, 120.693)
        ]
    }
    
    data = []
    seen = set()
    for county, towns in raw_cities.items():
        for town, area, lat, lon in towns:
            key = (county, town.strip())
            if key not in seen:
                seen.add(key)
                data.append({
                    "COUNTYNAME": county, 
                    "TOWNNAME": town.strip(), 
                    "Area_SqKm": area, 
                    "Center_Lat": lat, 
                    "Center_Lon": lon
                })
    return pd.DataFrame(data)

df_info = load_town_base_info()

# --- 2. 介面連動與配置 ---
col_select1, col_select2 = st.columns(2)
with col_select1:
    selected_county = st.selectbox("🗺️ 請選擇直轄市：", ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"])
with col_select2:
    filtered_towns = df_info[df_info['COUNTYNAME'] == selected_county]['TOWNNAME'].unique()
    selected_town = st.selectbox("📍 請選擇鄉鎮市區：", sorted(filtered_towns))

# 側邊欄權重配置
st.sidebar.header("🔧 便利性指標權重配置")
w_store = st.sidebar.slider("🏪 生活機能", 0, 100, 30)
w_transport = st.sidebar.slider("🚌 交通便利性", 0, 100, 30)
w_medical = st.sidebar.slider("🏥 醫療資源", 0, 100, 20)
w_school = st.sidebar.slider("🎓 教育資源", 0, 100, 20)

if (w_store + w_transport + w_medical + w_school) != 100:
    st.sidebar.error("❌ 權重總和必須等於 100%")
    st.stop()

# --- 3. 智能快取策略：先快取，再嘗試更新 ---
cache_key = f"{selected_county}_{selected_town}"

def get_data_from_cache_or_fetch(county, town, lat, lon):
    """
    優先級順序：
    1. 本地快取（如果存在）
    2. 嘗試從 Overpass 更新
    3. 快取失敗時使用安全沙盒
    """
    global cache_data
    
    # 檢查本地快取是否有該行政區的數據
    if cache_key in cache_data.get("data", {}):
        st.info("📦 使用本地快取數據")
        return cache_data["data"][cache_key]
    
    # 如果快取沒有，嘗試從 Overpass 獲取
    st.info("🔄 嘗試從 OpenStreetMap 獲取最新數據...")
    
    fetched_data = try_fetch_from_all_mirrors(county, town, lat, lon)
    
    if fetched_data and any(v > 0 for v in fetched_data.values()):
        # 成功獲取，保存到快取
        cache_data["data"][cache_key] = fetched_data
        save_cache(cache_data)
        st.success("💾 新數據已保存到本地快取")
        return fetched_data
    else:
        # 所有方式都失敗，返回預設沙盒數據
        st.warning("⚠️ 無法獲取最新數據，使用安全沙盒數據")
        return get_sandbox_data()

def try_fetch_from_all_mirrors(county, town, lat, lon):
    """嘗試所有可用的 Overpass 鏡像"""
    mirrors = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.openstreetmap.ru/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]
    
    alt_county = county.replace("臺", "台") if "臺" in county else county.replace("台", "臺")
    
    res_data = get_empty_data_dict()
    
    for mirror_url in mirrors:
        try:
            # 嘗試簡化查詢
            query = f"""
            [out:json][timeout:10];
            (
              node["amenity"~"hospital|clinic|pharmacy"](around:3000,{lat},{lon});
              node["highway"="bus_stop"](around:2000,{lat},{lon});
              node["shop"~"convenience|supermarket"](around:2000,{lat},{lon});
              node["amenity"~"school|university"](around:2000,{lat},{lon});
            );
            out tags;
            """
            
            response = requests.post(mirror_url, data={"data": query}, timeout=10)
            if response.status_code == 200:
                elements = response.json().get("elements", [])
                res_data = parse_elements(elements, res_data)
                st.success(f"✅ 成功從 {mirror_url.split('/')[2]} 取得數據")
                return res_data
        except:
            continue
    
    return None

def get_empty_data_dict():
    """返回空的數據���典"""
    return {
        "Medical_Centers": 0, "Regional_Hospitals": 0, "Local_Hospitals": 0, "Clinics": 0, "Pharmacies": 0,
        "MRT_Stations": 0, "HSR_Stations": 0, "Train_Stations": 0, "Interchanges": 0, "Bus_Stations": 0, 
        "UBike_Stations": 0, "International_Airports": 0, "Domestic_Airports": 0,
        "Elementary_Schools": 0, "High_Schools": 0, "Universities": 0, "Libraries": 0,
        "c_stores": 0, "s_markets": 0, "f_foods": 0, "m_malls": 0, "t_markets": 0, "b_banks": 0, "p_parks": 0
    }

def parse_elements(elements, res_data):
    """解析 Overpass 元素"""
    for el in elements:
        tags = el.get("tags", {})
        amenity = tags.get("amenity")
        shop = tags.get("shop")
        highway = tags.get("highway")
        
        if amenity == "hospital": res_data["Local_Hospitals"] += 1
        elif amenity == "clinic": res_data["Clinics"] += 1
        elif amenity == "pharmacy": res_data["Pharmacies"] += 1
        elif amenity == "school": res_data["Elementary_Schools"] += 1
        elif amenity == "university": res_data["Universities"] += 1
        elif shop == "convenience": res_data["c_stores"] += 1
        elif shop == "supermarket": res_data["s_markets"] += 1
        elif highway == "bus_stop": res_data["Bus_Stations"] += 1
    
    return res_data

def get_sandbox_data():
    """返回安全沙盒數據"""
    return {
        "Medical_Centers": 0, "Regional_Hospitals": 1, "Local_Hospitals": 2, "Clinics": 45, "Pharmacies": 18,
        "MRT_Stations": 2, "HSR_Stations": 0, "Train_Stations": 1, "Interchanges": 1, "Bus_Stations": 54, 
        "UBike_Stations": 15, "International_Airports": 0, "Domestic_Airports": 0,
        "Elementary_Schools": 8, "High_Schools": 4, "Universities": 1, "Libraries": 2,
        "c_stores": 52, "s_markets": 8, "f_foods": 4, "m_malls": 1, "t_markets": 2, "b_banks": 12, "p_parks": 8
    }

# 讀取目標行政區基準資料
target_info = df_info[(df_info['COUNTYNAME'] == selected_county) & (df_info['TOWNNAME'] == selected_town)].iloc[0]

with st.spinner(f"🔍 正在查詢 {selected_county}{selected_town}..."):
    static_target = get_data_from_cache_or_fetch(selected_county, selected_town, target_info['Center_Lat'], target_info['Center_Lon'])

# 攤平區域變數
c_stores = static_target["c_stores"]
s_markets = static_target["s_markets"]
f_foods = static_target["f_foods"]
m_malls = static_target["m_malls"]
t_markets = static_target["t_markets"]
b_banks = static_target["b_banks"]
p_parks = static_target["p_parks"]

# --- 4. 密度運算模型 ---
area = target_info['Area_SqKm'] if target_info['Area_SqKm'] > 0 else 1.0

med_weight = (static_target["Medical_Centers"] * 18 + static_target["Regional_Hospitals"] * 14 + 
               static_target["Local_Hospitals"] * 10 + static_target["Clinics"] * 6 + static_target["Pharmacies"] * 2)
med_density = med_weight / area
med_score = round(100 * (med_density / (med_density + 15.0)), 1)

trans_weight = (static_target["MRT_Stations"] * 6 + static_target["HSR_Stations"] * 16 + 
                static_target["Train_Stations"] * 12 + static_target.get("Interchanges", 0) * 10 + 
                static_target["Bus_Stations"] * 2 + static_target["UBike_Stations"] * 1 + 
                static_target["International_Airports"] * 18 + static_target["Domestic_Airports"] * 12)
trans_density = trans_weight / area
trans_score = round(100 * (trans_density / (trans_density + 20.0)), 1)

edu_weight = (static_target["Elementary_Schools"] * 1 + static_target["High_Schools"] * 3 + 
               static_target["Universities"] * 15 + static_target["Libraries"] * 8)
edu_density = edu_weight / area
edu_score = round(100 * (edu_density / (edu_density + 4.5)), 1)

life_weight = (c_stores * 3 + s_markets * 6 + f_foods * 5 + m_malls * 15 + t_markets * 6 + b_banks * 5 + p_parks * 3)
life_density = life_weight / area
life_score = round(100 * (life_density / (life_density + 10.0)), 1)

final_score = round(life_score * (w_store/100) + trans_score * (w_transport/100) + med_score * (w_medical/100) + edu_score * (w_school/100), 1)

# --- 5. 前端圖表與地圖渲染 ---
st.markdown("---")
col_dash, col_map = st.columns([1, 1])

with col_dash:
    st.subheader(f"📊 {selected_county}{selected_town} 即時指標看板")
    st.metric(label="🏆 綜合生活便利性得分", value=f"{final_score} / 100 分")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏥 醫療資源", "🚌 交通機能", "🎓 教育資源", "🏪 生活機能"])
    
    with tab1:
        st.write(f"**醫療資源評分：{med_score} 分**")
        st.markdown(f"🩺 **醫學中心**：`{static_target['Medical_Centers']} 間` *(權重 × 18)*")
        st.markdown(f"🏥 **區域醫院**：`{static_target['Regional_Hospitals']} 間` *(權重 × 14)*")
        st.markdown(f"🏥 **地區醫院**：`{static_target['Local_Hospitals']} 間` *(權重 × 10)*")
        st.markdown(f"👨‍⚕️ **一般醫事診所**：`{static_target['Clinics']} 診所` *(權重 × 6)*")
        st.markdown(f"💊 **健保特約藥局**：`{static_target['Pharmacies']} 家` *(權重 × 2)*")
        
    with tab2:
        st.write(f"**交通機能評分：{trans_score} 分**")
        st.markdown(f"🚇 **捷運/輕軌站點**：`{static_target['MRT_Stations']} 站` *(權重 × 6)*") 
        st.markdown(f"🚄 **高鐵車站**：`{static_target['HSR_Stations']} 站` *(權重 × 16)*")
        st.markdown(f"🚆 **台鐵車站**：`{static_target['Train_Stations']} 站` *(權重 × 12)*") 
        st.markdown(f"🛣️ **高/快速道路交流道**：`{static_target.get('Interchanges', 0)} 處` *(權重 × 10)*")
        st.markdown(f"🚌 **公車站點**：`{static_target['Bus_Stations']} 處` *(權重 × 2)*")
        st.markdown(f"🚲 **YouBike 站點**：`{static_target['UBike_Stations']} 站` *(權重 × 1)*")
        st.markdown(f"✈️ **國際機場**：`{static_target['International_Airports']} 座` *(權重 × 18)*")
        st.markdown(f"🛫 **國內機場**：`{static_target['Domestic_Airports']} 座` *(權重 × 12)*")
        
    with tab3:
        st.write(f"**教育資源評分：{edu_score} 分**")
        st.markdown(f"🎒 **國民小學**：`{static_target['Elementary_Schools']} 所` *(權重 × 1)*")
        st.markdown(f"🏫 **國高中與職校**：`{static_target['High_Schools']} 所` *(權重 × 3)*")
        st.markdown(f"🎓 **大專院校/大學**：`{static_target['Universities']} 所` *(權重 × 15)*")
        st.markdown(f"📚 **公共圖書館**：`{static_target['Libraries']} 所` *(權重 × 8)*")
        
    with tab4:
        st.write(f"**生活機能評分：{life_score} 分**")
        st.markdown(f"🏪 **連鎖便利商店**：`{c_stores} 家` *(權重 × 3)*")
        st.markdown(f"🍏 **連鎖超級市場**：`{s_markets} 間` *(權重 × 6)*")
        st.markdown(f"🍔 **連鎖速食餐廳**：`{f_foods} 間` *(權重 × 5)*")
        st.markdown(f"🏢 **百貨商場/量販**：`{m_malls} 間` *(權重 × 15)*")
        st.markdown(f"🏮 **傳統市場/夜市**：`{t_markets} 處` *(權重 × 6)*")
        st.markdown(f"💰 **郵局與銀行櫃點**：`{b_banks} 處` *(權重 × 5)*")
        st.markdown(f"🌳 **公園與運動綠地**：`{p_parks} 處` *(權重 × 3)*")

with col_map:
    st.subheader("📍 行政區動態定位地圖")
    lat, lon = target_info['Center_Lat'], target_info['Center_Lon']
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB positron")
    folium.Marker(location=[lat, lon], popup=f"<b>{selected_county}{selected_town}</b>", icon=folium.Icon(color="blue", icon="info-sign")).add_to(m)
    st_folium(m, width="100%", height=480, key=f"map_{selected_county}_{selected_town}")

# --- 6. 六都經典基準區動態排行對照 ---
st.markdown("---")
st.header("🏆 六都生活便利性動態對照排行榜")

benchmark_towns = [
    ("臺北市", "大安區", 11.36, 1, 2, 1, 45, 18, 4, 0, 1, 2, 45, 25, 0, 14, 2, 1, 15, 12, 1, 1, 9, 8, 5),
    ("新北市", "板橋區", 23.14, 0, 1, 1, 38, 12, 2, 0, 1, 1, 32, 18, 0, 10, 1, 1, 12, 10, 0, 1, 8, 6, 4),
    ("桃園市", "桃園區", 34.80, 0, 1, 0, 24, 10, 1, 0, 0, 2, 18, 12, 0, 6, 0, 1, 8, 5, 0, 0, 6, 4, 3),
    ("臺中市", "西屯區", 39.85, 0, 1, 1, 28, 14, 2, 0, 1, 1, 25, 15, 0, 8, 1, 0, 9, 6, 0, 0, 7, 5, 3),
    ("臺南市", "東區", 13.44, 0, 0, 1, 18, 8, 1, 0, 0, 0, 14, 10, 0, 4, 0, 0, 5, 3, 0, 0, 4, 3, 2),
    ("高雄市", "三民區", 19.78, 0, 1, 1, 31, 11, 2, 0, 1, 1, 29, 16, 0, 9, 1, 0, 8, 5, 0, 0, 6, 4, 3),
]

leaderboard_list = []
leaderboard_list.append({
    "縣市": selected_county, "行政區": f"✨ {selected_town} (本區查詢)", "綜合便利性得分": final_score
})

for b_county, b_town, b_area, mc, rh, lh, cl, ph, mrt, hsr, tr, ic, bus_st, ub, ia, da, es, hs, un, lb, c, s, f, m, t in benchmark_towns:
    if b_county == selected_county and b_town == selected_town:
        continue
    
    b_med = (mc*18 + rh*14 + lh*10 + cl*6 + ph*2) / b_area
    b_med_s = 100 * (b_med / (b_med + 13))
    
    b_trans = (mrt*6 + hsr*16 + tr*12 + ic*10 + bus_st*2 + ub*1 + ia*18 + da*12) / b_area
    b_trans_s = 100 * (b_trans / (b_trans + 10))
    
    b_edu = (es*1 + hs*3 + un*15 + lb*8) / b_area
    b_edu_s = 100 * (b_edu / (b_edu + 1.5))
    
    b_life = (c*3 + s*6 + f*5 + m*15 + t*6 + 12*5 + 8*3) / b_area
    b_life_s = 100 * (b_life / (b_life + 8))
    
    b_final = b_life_s * (w_store/100) + b_trans_s * (w_transport/100) + b_med_s * (w_medical/100) + b_edu_s * (w_school/100)
    
    leaderboard_list.append({
        "縣市": b_county, "行政區": b_town, "綜合便利性得分": round(b_final, 1)
    })

df_lb = pd.DataFrame(leaderboard_list).sort_values(by="綜合便利性得分", ascending=False).reset_index(drop=True)
df_lb['排名'] = df_lb.index + 1

st.dataframe(
    df_lb[['排名', '縣市', '行政區', '綜合便利性得分']], 
    use_container_width=True, 
    hide_index=True
)

# --- 7. 快取管理介面 ---
st.sidebar.markdown("---")
st.sidebar.header("💾 快取管理")
if st.sidebar.button("🔄 清除所有快取"):
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
        st.success("✅ 快取已清除")
        st.rerun()

if st.sidebar.button("📊 查看快取統計"):
    st.sidebar.info(f"📦 快取數據條數：{len(cache_data.get('data', {}))}\n⏰ 最後更新：{cache_data.get('timestamp', 'N/A')}")
