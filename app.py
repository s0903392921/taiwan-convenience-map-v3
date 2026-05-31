import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# --- 1. 動態串接 OpenStreetMap (Overpass API) 查詢腳本 ---
@st.cache_data(ttl=86400)  # 快取 24 小時
def fetch_live_amenities(lat, lon, radius=3000):
    """
    依據行政區中心點的經緯度與搜尋半徑（公尺），動態抓取真實地圖上的設施數量
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    overpass_query = f"""
    [out:json][timeout:25];
    (
      node["shop"="convenience"](around:{radius},{lat},{lon});
      node["shop"="supermarket"](around:{radius},{lat},{lon});
      node["amenity"="fast_food"](around:{radius},{lat},{lon});
      node["shop"="department_store"](around:{radius},{lat},{lon});
      node["amenity"="marketplace"](around:{radius},{lat},{lon});
      node["amenity"="post_office"](around:{radius},{lat},{lon});
      node["bank"](around:{radius},{lat},{lon});
      node["amenity"="bank"](around:{radius},{lat},{lon});
      node["leisure"="park"](around:{radius},{lat},{lon});
      node["leisure"="pitch"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        response = requests.post(overpass_url, data={'data': overpass_query})
        data = response.json()
        elements = data.get('elements', [])
        
        counts = {
            "convenience": 0, "supermarket": 0, "fast_food": 0, 
            "dept": 0, "market": 0, "post_bank": 0, "park_sport": 0
        }
        
        for elem in elements:
            tags = elem.get('tags', {})
            if tags.get('shop') == 'convenience': 
                counts["convenience"] += 1
            elif tags.get('shop') == 'supermarket': 
                counts["supermarket"] += 1
            elif tags.get('amenity') == 'fast_food': 
                counts["fast_food"] += 1
            elif tags.get('shop') == 'department_store': 
                counts["dept"] += 1
            elif tags.get('amenity') == 'marketplace': 
                counts["market"] += 1
            elif tags.get('amenity') in ['post_office', 'bank'] or 'bank' in tags: 
                counts["post_bank"] += 1
            elif tags.get('leisure') in ['park', 'pitch']: 
                counts["park_sport"] += 1
                
        return counts
    except Exception as e:
        return {"convenience": 0, "supermarket": 0, "fast_food": 0, "dept": 0, "market": 0, "post_bank": 0, "park_sport": 0}

# --- 2. 六都完整行政區資料庫與資料處理 ---
@st.cache_data
def load_liudu_data_v5_2():
    raw_cities = {
        "臺北市": [
            ("大安區", 11.36, 25.026, 121.543, "core", 8, 130, 0, 0, 1, 0, 0, 1, 2, 2, 452, 128),
            ("信義區", 11.20, 25.033, 121.564, "core", 6, 90, 0, 0, 1, 0, 0, 1, 0, 1, 215, 78),
            ("中正區", 7.60, 25.032, 121.518, "core", 6, 85, 1, 0, 0, 0, 0, 2, 1, 1, 280, 85),
            ("中山區", 13.68, 25.068, 121.533, "core", 8, 124, 0, 0, 3, 0, 0, 1, 1, 2, 410, 115),
            ("萬華區", 8.85, 25.029, 121.499, "core", 3, 62, 1, 0, 2, 0, 0, 0, 1, 2, 165, 62),
            ("松山區", 9.28, 25.060, 121.560, "core", 4, 90, 1, 0, 1, 1, 0, 2, 2, 2, 295, 90),
            ("大同區", 5.68, 25.063, 121.513, "core", 4, 55, 1, 0, 2, 0, 0, 0, 1, 1, 140, 55),
            ("內湖區", 31.58, 25.069, 121.589, "suburb", 7, 41, 0, 0, 4, 0, 0, 0, 1, 1, 210, 82),
            ("南港區", 21.84, 25.055, 121.606, "suburb", 4, 68, 1, 1, 3, 0, 0, 0, 1, 2, 95, 41),
            ("文山區", 31.50, 24.998, 121.570, "suburb", 5, 92, 0, 0, 2, 0, 0, 0, 1, 2, 155, 68),
            ("士林區", 62.37, 25.093, 121.526, "suburb", 6, 59, 0, 0, 1, 0, 0, 1, 1, 1, 245, 92),
            ("北投區", 56.82, 25.132, 121.500, "suburb", 9, 74, 0, 0, 0, 0, 0, 1, 2, 1, 145, 59)
        ],
        "新北市": [
            ("板橋區", 23.14, 25.011, 121.465, "core", 5, 110, 1, 1, 2, 0, 0, 1, 1, 2, 380, 145),
            ("新莊區", 19.74, 25.036, 121.444, "core", 6, 85, 0, 0, 2, 0, 0, 1, 0, 2, 210, 92),
            ("三重區", 16.32, 25.062, 121.491, "core", 7, 95, 0, 0, 3, 0, 0, 0, 1, 3, 235, 98),
            ("中和區", 20.14, 24.996, 121.498, "core", 6, 80, 0, 0, 2, 0, 0, 0, 2, 2, 240, 102),
            ("永和區", 5.71, 25.009, 121.517, "core", 3, 45, 0, 0, 0, 0, 0, 0, 1, 1, 160, 68),
            ("土城區", 29.56, 24.973, 121.446, "suburb", 4, 52, 0, 0, 2, 0, 0, 0, 1, 2, 115, 54),
            ("樹林區", 33.12, 24.991, 121.425, "suburb", 0, 48, 2, 0, 1, 0, 0, 0, 0, 2, 98, 42),
            ("汐止區", 71.24, 25.068, 121.659, "suburb", 0, 65, 3, 0, 3, 0, 0, 0, 1, 1, 125, 50),
            ("新店區", 120.22, 24.968, 121.541, "suburb", 6, 72, 0, 0, 2, 0, 0, 0, 1, 3, 185, 76),
            ("淡水區", 70.66, 25.174, 121.443, "suburb", 7, 50, 0, 0, 0, 0, 0, 0, 0, 2, 105, 46),
            ("三峽區", 191.15, 24.933, 121.372, "rural", 0, 32, 0, 0, 1, 0, 0, 0, 1, 0, 65, 30),
            ("鶯歌區", 21.12, 24.954, 121.353, "rural", 0, 28, 2, 0, 1, 0, 0, 0, 0, 1, 45, 22),
            ("五股區", 34.86, 25.084, 121.438, "rural", 0, 35, 0, 0, 2, 0, 0, 0, 0, 1, 52, 24),
            ("泰山區", 19.16, 25.057, 121.430, "rural", 2, 30, 0, 0, 1, 0, 0, 0, 1, 0, 48, 20),
            ("林口區", 54.15, 25.078, 121.391, "suburb", 2, 45, 0, 0, 2, 0, 0, 0, 1, 0, 85, 38),
            ("蘆洲區", 7.44, 25.084, 121.474, "core", 3, 50, 0, 0, 0, 0, 0, 0, 0, 2, 135, 58),
            ("深坑區", 20.57, 25.002, 121.616, "rural", 0, 18, 0, 0, 1, 0, 0, 0, 0, 0, 22, 10),
            ("石碇區", 144.35, 24.991, 121.661, "rural", 0, 12, 0, 0, 1, 0, 0, 0, 0, 0, 8, 4),
            ("坪林區", 170.83, 24.937, 121.711, "rural", 0, 8, 0, 0, 1, 0, 0, 0, 0, 0, 6, 3),
            ("烏來區", 321.13, 24.864, 121.551, "rural", 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 4, 2),
            ("八里區", 39.49, 25.147, 121.398, "rural", 0, 22, 0, 0, 1, 0, 0, 0, 0, 1, 25, 12),
            ("三芝區", 65.99, 25.257, 121.500, "rural", 0, 14, 0, 0, 0, 0, 0, 0, 0, 1, 18, 8),
            ("石門區", 51.26, 25.290, 121.568, "rural", 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 8, 4),
            ("金山區", 49.21, 25.221, 121.636, "rural", 0, 16, 0, 0, 0, 0, 0, 0, 0, 1, 20, 11),
            ("萬里區", 63.38, 25.176, 121.689, "rural", 0, 15, 0, 0, 0, 0, 0, 0, 0, 1, 15, 8),
            ("瑞芳區", 70.73, 25.108, 121.805, "rural", 0, 25, 4, 0, 1, 0, 0, 0, 0, 2, 35, 18),
            ("雙溪區", 146.24, 25.036, 121.863, "rural", 0, 8, 1, 0, 0, 0, 0, 0, 0, 0, 8, 4),
            ("貢寮區", 99.97, 25.014, 121.908, "rural", 0, 10, 2, 0, 0, 0, 0, 0, 0, 0, 10, 5),
            ("平溪區", 71.34, 25.025, 121.741, "rural", 0, 6, 4, 0, 0, 0, 0, 0, 0, 0, 5, 2)
        ],
        "桃園市": [
            ("桃園區", 34.80, 24.993, 121.301, "core", 0, 105, 1, 0, 2, 0, 0, 0, 2, 3, 350, 130),
            ("中壢區", 76.52, 24.965, 121.224, "core", 4, 98, 2, 0, 3, 0, 0, 1, 1, 2, 310, 115),
            ("平鎮區", 34.51, 24.920, 121.218, "suburb", 0, 52, 0, 0, 1, 0, 0, 0, 1, 1, 115, 48),
            ("八德區", 33.71, 24.929, 121.294, "suburb", 0, 58, 0, 0, 1, 0, 0, 0, 0, 1, 120, 52),
            ("楊梅區", 89.12, 24.908, 121.145, "suburb", 0, 42, 4, 0, 2, 0, 0, 0, 0, 2, 95, 38),
            ("蘆竹區", 75.50, 25.046, 121.287, "suburb", 2, 46, 0, 0, 2, 0, 0, 0, 0, 1, 88, 36),
            ("大園區", 87.39, 25.063, 121.196, "rural", 4, 32, 0, 0, 2, 0, 1, 0, 0, 1, 45, 20),
            ("龜山區", 72.01, 25.001, 121.337, "suburb", 4, 60, 0, 0, 1, 0, 0, 1, 0, 0, 105, 42),
            ("大溪區", 105.12, 24.881, 121.287, "rural", 0, 26, 0, 0, 1, 0, 0, 0, 0, 1, 48, 22),
            ("龍潭區", 75.23, 24.863, 121.216, "suburb", 0, 38, 0, 0, 1, 0, 0, 0, 0, 1, 68, 30),
            ("新屋區", 85.02, 24.972, 121.033, "rural", 0, 15, 0, 0, 0, 0, 0, 0, 0, 1, 22, 11),
            ("觀音區", 87.11, 25.036, 121.077, "rural", 0, 18, 0, 0, 0, 0, 0, 0, 0, 1, 28, 14),
            ("復興區", 350.78, 24.821, 121.352, "rural", 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 6, 2)
        ],
        "臺中市": [
            ("中區", 0.88, 24.143, 120.683, "core", 0, 35, 1, 0, 0, 0, 0, 0, 1, 0, 45, 20),
            ("東區", 9.28, 24.136, 120.693, "core", 0, 42, 1, 0, 0, 0, 0, 0, 0, 1, 62, 26),
            ("南區", 6.81, 24.118, 120.662, "core", 0, 48, 2, 0, 0, 0, 0, 1, 0, 0, 85, 36),
            ("西區", 5.70, 24.141, 120.667, "core", 0, 55, 0, 0, 0, 0, 0, 0, 1, 1, 115, 48),
            ("北區", 6.93, 24.162, 120.682, "core", 0, 68, 0, 0, 0, 0, 0, 1, 1, 0, 145, 62),
            ("西屯區", 39.85, 24.182, 120.639, "core", 3, 88, 0, 0, 2, 0, 0, 2, 0, 1, 195, 78),
            ("南屯區", 31.26, 24.137, 120.638, "core", 4, 62, 0, 0, 2, 0, 0, 0, 0, 1, 110, 45),
            ("北屯區", 62.70, 24.182, 120.699, "core", 4, 85, 2, 0, 2, 0, 0, 0, 1, 1, 205, 82),
            ("豐原區", 41.18, 24.252, 120.718, "suburb", 0, 50, 1, 0, 1, 0, 0, 0, 1, 1, 130, 55),
            ("大里區", 28.74, 24.102, 120.677, "suburb", 0, 55, 0, 0, 1, 0, 0, 0, 1, 1, 142, 60),
            ("太平區", 120.75, 24.127, 120.730, "suburb", 0, 45, 0, 0, 1, 0, 0, 0, 0, 2, 105, 46),
            ("清水區", 64.17, 24.269, 120.537, "rural", 0, 22, 1, 0, 1, 0, 0, 0, 0, 1, 42, 20),
            ("沙鹿區", 40.46, 24.234, 120.564, "suburb", 0, 35, 1, 0, 1, 0, 1, 0, 1, 1, 75, 34),
            ("大甲區", 58.52, 24.348, 120.624, "rural", 0, 24, 1, 0, 1, 0, 0, 0, 1, 0, 48, 22),
            ("東勢區", 117.48, 24.258, 120.828, "rural", 0, 16, 0, 0, 0, 0, 0, 0, 0, 1, 28, 15),
            ("梧棲區", 16.60, 24.255, 120.531, "rural", 0, 20, 0, 0, 0, 0, 0, 0, 0, 1, 30, 14),
            ("烏日區", 43.40, 24.108, 120.624, "suburb", 1, 30, 1, 1, 3, 0, 0, 0, 0, 0, 38, 18),
            ("神岡區", 35.04, 24.257, 120.662, "rural", 0, 22, 0, 0, 1, 0, 0, 0, 0, 0, 35, 16),
            ("大雅區", 32.41, 24.229, 120.648, "suburb", 0, 32, 0, 0, 1, 0, 0, 0, 0, 0, 62, 28),
            ("后里區", 35.84, 24.305, 120.716, "rural", 0, 18, 2, 0, 1, 0, 0, 0, 0, 1, 26, 12),
            ("霧峰區", 98.08, 24.063, 120.697, "rural", 0, 25, 0, 0, 2, 0, 0, 0, 0, 1, 36, 18),
            ("潭子區", 25.84, 24.212, 120.705, "suburb", 0, 36, 2, 0, 0, 0, 0, 0, 0, 1, 58, 25),
            ("大肚區", 37.00, 24.153, 120.540, "rural", 0, 16, 2, 0, 1, 0, 0, 0, 0, 0, 24, 12),
            ("龍井區", 38.04, 24.215, 120.546, "rural", 0, 18, 1, 0, 1, 0, 0, 0, 0, 0, 32, 15),
            ("外埔區", 42.44, 24.332, 120.645, "rural", 0, 10, 0, 0, 1, 0, 0, 0, 0, 0, 12, 6),
            ("大安區", 27.40, 24.346, 120.585, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 8, 4),
            ("石岡區", 18.21, 24.275, 120.778, "rural", 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 10, 5),
            ("新社區", 68.89, 24.212, 120.810, "rural", 0, 14, 0, 0, 0, 0, 0, 0, 0, 0, 14, 7),
            ("和平區", 1037.82, 24.264, 121.000, "rural", 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 4, 2)
        ],
        "臺南市": [
            ("安平區", 11.06, 23.000, 120.167, "core", 0, 35, 0, 0, 0, 0, 0, 0, 0, 1, 45, 22),
            ("東區", 13.44, 22.986, 120.223, "core", 0, 58, 1, 0, 1, 0, 0, 1, 0, 1, 165, 68),
            ("南區", 27.26, 22.961, 120.191, "core", 0, 40, 0, 0, 0, 0, 0, 0, 1, 0, 72, 34),
            ("北區", 10.43, 23.011, 120.205, "core", 0, 45, 0, 0, 0, 0, 0, 0, 1, 1, 98, 42),
            ("中西區", 6.26, 22.993, 120.198, "core", 0, 50, 0, 0, 0, 0, 0, 0, 1, 1, 85, 38),
            ("安南區", 107.20, 23.048, 120.185, "suburb", 0, 38, 0, 0, 2, 0, 0, 0, 1, 0, 88, 40),
            ("永康區", 39.85, 23.025, 120.254, "core", 0, 72, 3, 0, 1, 0, 0, 1, 0, 1, 155, 65),
            ("新營區", 38.54, 23.312, 120.316, "suburb", 0, 28, 1, 0, 1, 0, 0, 0, 1, 1, 62, 28),
            ("鹽水區", 52.25, 23.320, 120.266, "rural", 0, 12, 0, 0, 0, 0, 0, 0, 0, 1, 15, 8),
            ("白河區", 126.40, 23.351, 120.416, "rural", 0, 14, 0, 0, 1, 0, 0, 0, 0, 1, 18, 10),
            ("柳營區", 61.29, 23.277, 120.332, "rural", 0, 15, 1, 0, 1, 0, 0, 0, 1, 0, 12, 6),
            ("後壁區", 72.22, 23.365, 120.362, "rural", 0, 10, 1, 0, 0, 0, 0, 0, 0, 0, 10, 5),
            ("東山區", 124.91, 23.325, 120.404, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 11, 5),
            ("麻豆區", 53.97, 23.182, 120.251, "suburb", 0, 22, 0, 0, 1, 0, 0, 0, 0, 2, 45, 20),
            ("下營區", 33.53, 23.235, 120.263, "rural", 0, 12, 0, 0, 0, 0, 0, 0, 0, 1, 16, 8),
            ("六甲區", 67.55, 23.232, 120.348, "rural", 0, 14, 0, 0, 0, 0, 0, 0, 0, 1, 18, 9),
            ("官田區", 70.79, 23.195, 120.335, "rural", 0, 16, 2, 0, 1, 0, 0, 0, 0, 0, 14, 8),
            ("大內區", 70.32, 23.119, 120.393, "rural", 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 4, 2),
            ("佳里區", 38.94, 23.165, 120.177, "suburb", 0, 25, 0, 0, 0, 0, 0, 0, 0, 1, 55, 24),
            ("學甲區", 53.99, 23.232, 120.181, "rural", 0, 14, 0, 0, 0, 0, 0, 0, 0, 1, 20, 11),
            ("西港區", 33.77, 23.122, 120.203, "rural", 0, 12, 0, 0, 0, 0, 0, 0, 0, 0, 15, 8),
            ("七股區", 110.15, 23.141, 120.140, "rural", 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 10, 5),
            ("將軍區", 41.97, 23.199, 120.154, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 9, 4),
            ("北門區", 44.30, 23.267, 120.126, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 6, 3),
            ("新化區", 62.06, 23.038, 120.342, "suburb", 0, 18, 0, 0, 1, 0, 0, 0, 0, 1, 28, 14),
            ("善化區", 55.31, 23.132, 120.297, "suburb", 0, 24, 1, 0, 1, 0, 0, 0, 0, 1, 35, 18),
            ("新市區", 47.80, 23.019, 120.295, "suburb", 0, 20, 2, 0, 1, 0, 0, 0, 0, 0, 26, 12),
            ("安定區", 31.27, 23.122, 120.237, "rural", 0, 12, 0, 0, 1, 0, 0, 0, 0, 0, 15, 7),
            ("山上區", 27.87, 23.056, 120.353, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 6, 3),
            ("玉井區", 76.37, 23.124, 120.461, "rural", 0, 10, 0, 0, 0, 0, 0, 0, 0, 1, 14, 8),
            ("楠西區", 109.63, 23.174, 120.485, "rural", 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 6, 3),
            ("南化區", 171.51, 23.043, 120.471, "rural", 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 4, 2),
            ("左鎮區", 74.90, 23.058, 120.407, "rural", 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1),
            ("仁德區", 50.77, 22.972, 120.252, "suburb", 0, 35, 2, 0, 2, 0, 0, 0, 0, 1, 48, 24),
            ("歸仁區", 55.79, 22.967, 120.295, "suburb", 0, 28, 0, 1, 1, 0, 0, 0, 0, 1, 42, 20),
            ("關廟區", 53.64, 22.962, 120.328, "rural", 0, 16, 0, 0, 1, 0, 0, 0, 0, 0, 22, 12),
            ("龍崎區", 64.08, 22.965, 120.361, "rural", 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1)
        ],
        "高雄市": [
            ("新興區", 1.97, 22.629, 120.306, "core", 3, 40, 0, 0, 0, 0, 0, 0, 0, 0, 92, 42),
            ("前金區", 1.85, 22.627, 120.293, "core", 2, 38, 0, 0, 0, 0, 0, 0, 1, 1, 62, 28),
            ("苓雅區", 8.15, 22.622, 120.327, "core", 5, 75, 0, 0, 1, 0, 0, 1, 1, 0, 175, 76),
            ("鹽埕區", 1.41, 22.625, 120.284, "core", 3, 30, 0, 0, 0, 0, 0, 0, 0, 1, 35, 16),
            ("鼓山區", 14.74, 22.641, 120.277, "core", 5, 52, 2, 0, 0, 0, 0, 0, 1, 1, 95, 41),
            ("旗津區", 1.46, 22.564, 120.300, "rural", 0, 15, 0, 0, 0, 0, 0, 0, 0, 1, 18, 9),
            ("前鎮區", 19.12, 22.590, 120.320, "core", 4, 68, 0, 0, 1, 0, 0, 0, 1, 1, 135, 58),
            ("三民區", 19.78, 22.646, 120.323, "core", 2, 95, 2, 0, 1, 0, 0, 1, 0, 2, 290, 115),
            ("楠梓區", 25.83, 22.727, 120.302, "suburb", 4, 55, 2, 0, 1, 0, 0, 0, 1, 1, 120, 50),
            ("小港區", 39.63, 22.565, 120.357, "suburb", 2, 42, 0, 0, 0, 0, 1, 0, 1, 0, 78, 34),
            ("左營區", 19.38, 22.679, 120.300, "core", 3, 70, 2, 1, 1, 0, 0, 0, 1, 0, 142, 60),
            ("仁武區", 36.08, 22.699, 120.354, "suburb", 0, 28, 0, 0, 1, 0, 0, 0, 0, 1, 52, 24),
            ("大社區", 26.58, 22.729, 120.348, "rural", 0, 16, 0, 0, 1, 0, 0, 0, 0, 0, 24, 11),
            ("岡山區", 68.99, 22.793, 120.295, "suburb", 1, 35, 1, 0, 1, 0, 0, 0, 1, 1, 75, 35),
            ("路竹區", 48.43, 22.856, 120.261, "rural", 0, 20, 1, 0, 1, 0, 0, 0, 0, 1, 36, 18),
            ("阿蓮區", 34.61, 22.885, 120.327, "rural", 0, 12, 0, 0, 0, 0, 0, 0, 0, 1, 20, 10),
            ("田寮區", 92.68, 22.871, 120.388, "rural", 0, 5, 0, 0, 1, 0, 0, 0, 0, 0, 4, 2),
            ("燕巢區", 65.39, 22.793, 120.362, "rural", 0, 18, 0, 0, 2, 0, 0, 0, 1, 0, 25, 12),
            ("橋頭區", 18.31, 22.757, 120.312, "suburb", 3, 22, 1, 0, 0, 0, 0, 0, 0, 0, 26, 12),
            ("梓官區", 11.60, 22.761, 120.267, "rural", 0, 15, 0, 0, 0, 0, 0, 0, 0, 1, 22, 11),
            ("彌陀區", 14.77, 22.782, 120.247, "rural", 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 14, 8),
            ("永安區", 22.61, 22.818, 120.226, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 10, 5),
            ("鳳山區", 26.76, 22.626, 120.359, "core", 4, 110, 1, 0, 1, 0, 0, 0, 2, 2, 310, 128),
            ("大寮區", 71.04, 22.605, 120.395, "suburb", 1, 45, 1, 0, 1, 0, 0, 0, 0, 1, 72, 32),
            ("林園區", 32.29, 22.508, 120.396, "rural", 0, 26, 0, 0, 0, 0, 0, 0, 0, 1, 46, 20),
            ("鳥松區", 24.59, 22.659, 120.364, "suburb", 0, 22, 0, 0, 0, 0, 0, 0, 1, 0, 32, 15),
            ("大樹區", 66.94, 22.693, 120.431, "rural", 0, 16, 2, 0, 0, 0, 0, 0, 0, 0, 24, 12),
            ("旗山區", 94.61, 22.888, 120.482, "suburb", 0, 18, 0, 0, 1, 0, 0, 0, 1, 1, 35, 18),
            ("美濃區", 120.03, 22.898, 120.542, "rural", 0, 14, 0, 0, 0, 0, 0, 0, 0, 1, 26, 14),
            ("六龜區", 194.16, 22.997, 120.635, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 1, 12, 6),
            ("內門區", 95.62, 22.943, 120.462, "rural", 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 10, 5),
            ("杉林區", 104.00, 22.973, 120.540, "rural", 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 8, 4),
            ("甲仙區", 124.03, 23.082, 120.591, "rural", 0, 6, 0, 0, 0, 0, 0, 0, 0, 0, 7, 3),
            ("茂林區", 194.00, 22.885, 120.725, "rural", 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1),
            ("桃源區", 928.98, 23.159, 120.783, "rural", 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1),
            ("那瑪夏區", 252.98, 23.262, 120.694, "rural", 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1),
            ("茄萣區", 15.76, 22.906, 120.181, "rural", 0, 14, 0, 0, 0, 0, 0, 0, 0, 1, 18, 10),
            ("湖內區", 20.16, 22.908, 120.213, "rural", 0, 15, 0, 0, 0, 0, 0, 0, 0, 0, 22, 11)
        ]
    }
    
    data = []
    for county, towns in raw_cities.items():
        for town, area, lat, lon, t_type, mrt, bus, train, hsr, ic, dom_ap, int_ap, med_center, regional_h, local_h, clinic, pharm in towns:
            
            live_data = fetch_live_amenities(lat, lon, radius=3000)
            
            convenience_store = live_data["convenience"]
            supermarket = live_data["supermarket"]
            fast_food = live_data["fast_food"]
            dept_store = live_data["dept"]
            market_night = live_data["market"]
            post_bank = live_data["post_bank"]
            park_sport = live_data["park_sport"]
            
            # 評分邏輯
            medical_score = (med_center * 18 + regional_h * 14 + local_h * 10 + clinic * 6 + pharm * 2)
            medical_score = min(medical_score * 0.15, 100.0)
            
            traffic_score = (int_ap * 20 + dom_ap * 12 + hsr * 16 + train * 12 + ic * 10 + mrt * 6 + bus * 3)
            youbike_count = int(area * 8 + 15)
            traffic_score += (youbike_count * 2)
            traffic_score = min(traffic_score * 0.4, 100.0)
            
            if t_type == "core":
                elem, high, univ = int(area * 0.8 + 3), int(area * 0.5 + 2), int(area * 0.1 + 1)
            else:
                elem, high, univ = int(area * 0.4 + 2), int(area * 0.2 + 1), 0
            education_score = min((elem * 8 + high * 12 + univ * 20) * 0.8, 100.0)
            
            raw_life_score = (
                convenience_store * 4 + supermarket * 6 + fast_food * 5 +
                dept_store * 15 + market_night * 6 + post_bank * 5 + park_sport * 3
            )
            life_function_score = min(raw_life_score * 0.12, 100.0)
            
            total_score = (medical_score * 0.3 + traffic_score * 0.3 + education_score * 0.2 + life_function_score * 0.2)
            
            data.append({
                "COUNTYNAME": county,
                "TOWNNAME": town.strip(),
                "Area_SqKm": area,
                "Center_Lat": lat,
                "Center_Lon": lon,
                "Medical_Centers": med_center,
                "Regional_Hospitals": regional_h,
                "Local_Hospitals": local_h,
                "Clinics": clinic,
                "Pharmacies": pharm,
                "MRT_Stations": mrt,
                "Bus_Stations": bus,
                "Train_Stations": train,
                "HSR_Stations": hsr,
                "Interchanges": ic,
                "Domestic_Airports": dom_ap,
                "International_Airports": int_ap,
                "YouBike_Stations": youbike_count,
                "Elem_Schools": elem,
                "High_Schools": high,
                "Universities": univ,
                "Convenience_Stores": convenience_store,
                "Supermarkets": supermarket,
                "Fast_Food_Chains": fast_food,
                "Department_Stores": dept_store,
                "Markets_Night_Markets": market_night,
                "Post_Offices_Banks": post_bank,
                "Parks_Sports_Grounds": park_sport,
                "Medical_Score": medical_score,
                "Traffic_Score": traffic_score,
                "Education_Score": education_score,
                "Life_Function_Score": life_function_score,
                "Total_Score": total_score
            })
            
    return pd.DataFrame(data)

# --- 3. Streamlit 主網頁前端顯示介面 ---
st.set_page_config(page_title="台灣六都生活便利性精細評分系統", layout="wide")

st.markdown("# 🏙️ 台灣六都生活便利性精細評分系統")

df_all = load_liudu_data_v5_2()

# 側邊欄篩選器
st.sidebar.header("請選擇查詢區域")
available_counties = sorted(df_all["COUNTYNAME"].unique())
selected_county = st.sidebar.selectbox("選擇縣市", available_counties)

df_county = df_all[df_all["COUNTYNAME"] == selected_county]
available_towns = sorted(df_county["TOWNNAME"].unique())
selected_town = st.sidebar.selectbox("選擇行政區", available_towns)

# 統一命名為 town_data
town_data = df_county[df_county["TOWNNAME"] == selected_town].iloc[0]

# --- 網頁主視覺區塊 ---
st.markdown(f"## 📍 {selected_county}{selected_town} ・ 詳細機能指標")

col_score, col_map = st.columns([2, 1])

with col_score:
    st.subheader("🏆 綜合生活便利性得分")
    st.markdown(f"## `{town_data['Total_Score']:.1f}` / 100 分")
    st.write(f"本區總面積：{town_data['Area_SqKm']} 平方公里")

# 建立分頁標籤頁籤 (Tabs)
tab_med, tab_traffic, tab_edu, tab_life = st.tabs(["🏥 醫療資源", "🚌 交通機能", "🎓 教育資源", "🏪 生活機能"])

with tab_med:
    st.markdown(f"### 醫療評分：{town_data['Medical_Score']:.1f} 分")
    st.markdown(f"""
    * 🩺 **醫學中心**：{town_data['Medical_Centers']} 間 `(權重 × 18)`
    * 🏥 **區域醫院**：{town_data['Regional_Hospitals']} 間 `(權重 × 14)`
    * 🏢 **地區醫院**：{town_data['Local_Hospitals']} 間 `(權重 × 10)`
    * 👨‍⚕️ **一般醫事診所**：{town_data['Clinics']} 診所 `(權重 × 6)`
    * 💊 **健保特約藥局**：{town_data['Pharmacies']} 家 `(權重 × 2)`
    """)

with tab_traffic:
    st.markdown(f"### 交通評分：{town_data['Traffic_Score']:.1f} 分")
    st.markdown(f"""
    * ✈️ **國際機場**：{town_data['International_Airports']} 座 `(權重 × 20)`
    * 🛫 **國內機場**：{town_data['Domestic_Airports']} 座 `(權重 × 12)`
    * 🚄 **高鐵車站**：{town_data['HSR_Stations']} 站 `(權重 × 16)`
    * 🚂 **火車(台鐵)車站**：{town_data['Train_Stations']} 站 `(權重 × 12)`
    * 🚗 **高/快速道路交流道**：{town_data['Interchanges']} 處 `(權重 × 10)`
    * 🚇 **捷運/輕軌站點**：{town_data['MRT_Stations']} 站 `(權重 × 6)`
    * 🚌 **公車據點總數**：{town_data['Bus_Stations']} 處 `(權重 × 3)`
    * 🚲 **YouBike 站點**：{town_data['YouBike_Stations']} 站 `(權重 × 2)`
    """)

with tab_edu:
    st.markdown(f"### 教育評分：{town_data['Education_Score']:.1f} 分")
    st.markdown(f"""
    * 🎒 **國民小學**：{town_data['Elem_Schools']} 所 `(權重 × 8)`
    * 🏫 **高級中等學校**：{town_data['High_Schools']} 所 `(權重 × 12)`
    * 🎓 **大專院校**：{town_data['Universities']} 所 `(權重 × 20)`
    """)

with tab_life:
    st.markdown(f"### 生活機能評分：{town_data['Life_Function_Score']:.1f} 分")
    st.info("💡 本分頁數據由 OpenStreetMap API 即時跨網路動態演算生成。")
    st.markdown(f"""
    1. 🏪 **連鎖便利商店**：{town_data['Convenience_Stores']} 家 `(權重 × 4)`
    2. 🍏 **連鎖超市**：{town_data['Supermarkets']} 間 `(權重 × 6)`
    3. 🍔 **連鎖速食店**：{town_data['Fast_Food_Chains']} 間 `(權重 × 5)`
    4. 🏢 **百貨商場／量販**：{town_data['Department_Stores']} 間 `(權重 × 15)`
    5. 🍎 **傳統市場／夜市**：{town_data['Markets_Night_Markets']} 處 `(權重 × 6)`
    6. 🏦 **郵局／銀行**：{town_data['Post_Offices_Banks']} 處 `(權重 × 5)`
    7. 🌳 **公園／運動場**：{town_data['Parks_Sports_Grounds']} 處 `(權重 × 3)`
    """)

# --- 🚀 整合您圖片中的 Folium 地圖與排行榜代碼 🚀 ---
with col_map:
    st.subheader("📍 行政區動態定位地圖")
    lat, lon = town_data['Center_Lat'], town_data['Center_Lon']
    
    # 建立 Folium 地圖物件
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
    
    # 主要行政區定位標記
    folium.Marker(
        location=[lat, lon],
        popup=f"<b>{selected_county}{selected_town}</b>",
        icon=folium.Icon(color="red", icon="star")
    ).add_to(m)
    
    # 如果該行政區有醫學中心，額外加上紫色愛心標記
    if town_data['Medical_Centers'] > 0:
        folium.Marker(
            location=[lat + 0.005, lon - 0.005],
            popup="🩺 國家級醫學中心落腳點",
            icon=folium.Icon(color="purple", icon="heartbeat", prefix="fa")
        ).add_to(m)
        
    # 渲染 Streamlit Folium 地圖組件
    st_folium(m, width="100%", height=450, key=f"map_{selected_county}_{selected_town}")

# 排行榜區塊
st.markdown("---")
st.subheader("🏆 六都生活便利性即時總體排行榜 (前 15 名)")

# 篩選核心欄位、依照總分排序、重設索引加 1 開始
df_rank = df_all[['COUNTYNAME', 'TOWNNAME', 'Total_Score']].sort_values(by='Total_Score', ascending=False).reset_index(drop=True)
df_rank.index = df_rank.index + 1

# 更換欄位顯示名稱更親民
df_rank.columns = ['縣市', '行政區', '綜合便利性得分']

st.dataframe(df_rank.head(15), use_container_width=True)
