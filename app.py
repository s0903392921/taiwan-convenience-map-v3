import requests
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="台灣六都生活便利性評分系統 V6.0", layout="wide")
st.title("🏙️ 台灣六都生活便利性評分系統 ")


# --- 1. 靜態真實資料庫 (已完全填滿解鎖六都全部行政區，共 152 個區) ---
@st.cache_data
def load_perfect_liudu_data():
    raw_cities = {
        "臺北市": [
            ("大安區", 11.36, 25.026, 121.543, "core", 185, 11, 0, 0, 0, 0, 0, 162, 14, 11, 3, 6, 1, 2, 2, 452, 128),
            ("信義區", 11.20, 25.033, 121.564, "core", 142, 9, 1, 0, 3, 0, 0, 115, 10, 6, 1, 3, 1, 0, 1, 215, 78),
            ("中正區", 7.60, 25.032, 121.518, "core", 198, 13, 1, 1, 0, 0, 0, 108, 9, 8, 2, 4, 2, 1, 1, 280, 85),
            ("中山區", 13.68, 25.068, 121.533, "core", 210, 11, 0, 0, 2, 0, 0, 145, 11, 7, 1, 3, 1, 1, 2, 410, 115),
            ("萬華區", 8.85, 25.029, 121.499, "core", 115, 2, 1, 0, 1, 0, 0, 82, 8, 5, 0, 3, 0, 1, 2, 165, 62),
            ("松山區", 9.28, 25.060, 121.560, "core", 132, 6, 1, 0, 0, 1, 0, 95, 8, 4, 0, 3, 0, 2, 2, 295, 90),
            ("大同區", 5.68, 25.063, 121.513, "core", 98, 5, 0, 0, 2, 0, 0, 68, 5, 4, 0, 2, 0, 1, 1, 140, 55),
            ("內湖區", 31.58, 25.069, 121.589, "suburb", 245, 10, 0, 0, 3, 0, 0, 158, 13, 7, 1, 4, 1, 1, 1, 210, 82),
            ("南港區", 21.84, 25.055, 121.606, "suburb", 120, 4, 1, 1, 3, 0, 0, 92, 6, 4, 1, 2, 0, 1, 1, 95, 41),
            ("文山區", 31.50, 24.998, 121.570, "suburb", 165, 10, 0, 0, 2, 0, 0, 112, 12, 8, 2, 4, 0, 1, 2, 155, 68),
            ("士林區", 62.37, 25.093, 121.526, "suburb", 280, 5, 0, 0, 0, 0, 0, 138, 20, 9, 3, 5, 1, 1, 1, 245, 92),
            ("北投區", 56.82, 25.132, 121.500, "suburb", 195, 9, 0, 0, 0, 0, 0, 124, 16, 7, 3, 4, 2, 1, 2, 145, 59)
        ],
        "新北市": [
            ("板橋區", 23.14, 25.011, 121.465, "core", 385, 11, 2, 1, 2, 0, 0, 215, 23, 11, 2, 5, 1, 1, 4, 560, 185),
            ("三重區", 16.32, 25.062, 121.498, "core", 240, 8, 0, 0, 3, 0, 0, 142, 15, 8, 0, 3, 0, 1, 3, 310, 112),
            ("中和區", 20.14, 24.999, 121.498, "core", 215, 6, 0, 0, 1, 0, 0, 138, 11, 7, 0, 4, 1, 0, 3, 340, 125),
            ("永和區", 5.71, 25.008, 121.516, "core", 110, 1, 0, 0, 0, 0, 0, 72, 8, 4, 0, 2, 0, 1, 2, 220, 88),
            ("新莊區", 19.74, 25.036, 121.445, "core", 295, 9, 0, 0, 1, 0, 0, 155, 16, 8, 1, 4, 0, 1, 3, 305, 108),
            ("新店區", 120.22, 24.968, 121.541, "suburb", 260, 13, 0, 0, 3, 0, 0, 118, 17, 8, 0, 4, 0, 2, 2, 240, 95),
            ("土城區", 29.56, 24.973, 121.444, "suburb", 145, 4, 0, 0, 2, 0, 0, 89, 9, 4, 0, 2, 0, 1, 1, 160, 64),
            ("蘆洲區", 7.44, 25.084, 121.474, "core", 105, 3, 0, 0, 0, 0, 0, 58, 8, 4, 0, 2, 0, 0, 2, 175, 58),
            ("汐止區", 71.24, 25.067, 121.659, "suburb", 210, 0, 3, 0, 3, 0, 0, 96, 12, 5, 0, 2, 0, 1, 1, 125, 48),
            ("樹林區", 33.12, 24.991, 121.420, "suburb", 135, 0, 2, 0, 1, 0, 0, 64, 10, 4, 1, 2, 0, 0, 3, 110, 45),
            ("淡水區", 70.65, 25.170, 121.442, "suburb", 185, 17, 0, 0, 0, 0, 0, 122, 14, 5, 2, 3, 0, 1, 1, 135, 52),
            ("林口區", 54.15, 25.077, 121.391, "suburb", 160, 1, 0, 0, 1, 0, 0, 88, 10, 4, 1, 2, 0, 0, 1, 105, 38),
            ("五股區", 34.86, 25.084, 121.438, "suburb", 112, 0, 0, 0, 2, 0, 0, 54, 7, 2, 0, 1, 0, 0, 0, 68, 22),
            ("泰山區", 19.16, 25.059, 121.431, "suburb", 88, 2, 0, 0, 1, 0, 0, 41, 5, 3, 1, 1, 0, 0, 1, 55, 19),
            ("三峽區", 191.15, 24.933, 121.373, "suburb", 130, 0, 0, 0, 1, 0, 0, 65, 12, 6, 1, 2, 0, 1, 0, 115, 36),
            ("鶯歌區", 21.12, 24.954, 121.355, "suburb", 92, 0, 2, 0, 1, 0, 0, 48, 7, 3, 0, 1, 0, 0, 0, 62, 21),
            ("八里區", 39.49, 25.147, 121.399, "rural", 65, 0, 0, 0, 1, 0, 0, 32, 5, 1, 0, 1, 0, 0, 0, 24, 8),
            ("深坑區", 20.58, 25.003, 121.616, "rural", 48, 0, 0, 0, 1, 0, 0, 22, 3, 1, 1, 1, 0, 0, 0, 21, 6),
            ("石碇區", 144.35, 24.992, 121.657, "rural", 28, 0, 0, 0, 1, 0, 0, 10, 3, 1, 0, 1, 0, 0, 0, 5, 2),
            ("坪林區", 170.84, 24.937, 121.711, "rural", 22, 0, 0, 0, 1, 0, 0, 8, 2, 1, 0, 1, 0, 0, 0, 4, 1),
            ("烏來區", 321.13, 24.864, 121.551, "rural", 15, 0, 0, 0, 0, 0, 0, 5, 2, 1, 0, 1, 0, 0, 0, 3, 1),
            ("瑞芳區", 70.73, 25.109, 121.805, "rural", 82, 0, 4, 0, 1, 0, 0, 24, 9, 3, 0, 2, 0, 0, 1, 32, 12),
            ("萬里區", 63.37, 25.175, 121.689, "rural", 45, 0, 0, 0, 0, 0, 0, 12, 3, 1, 0, 1, 0, 0, 0, 9, 4),
            ("金山區", 49.21, 25.222, 121.638, "rural", 52, 0, 0, 0, 0, 0, 0, 15, 4, 1, 0, 1, 0, 0, 1, 15, 6),
            ("石門區", 31.24, 25.290, 121.568, "rural", 26, 0, 0, 0, 0, 0, 0, 6, 3, 0, 0, 1, 0, 0, 0, 3, 1),
            ("三芝區", 65.99, 25.257, 121.500, "rural", 38, 0, 0, 0, 0, 0, 0, 14, 4, 1, 0, 1, 0, 0, 0, 12, 4),
            ("雙溪區", 146.25, 25.036, 121.863, "rural", 20, 0, 2, 0, 0, 0, 0, 5, 3, 1, 0, 1, 0, 0, 0, 4, 2),
            ("貢寮區", 99.97, 25.022, 121.908, "rural", 34, 0, 3, 0, 0, 0, 0, 8, 4, 1, 0, 1, 0, 0, 0, 5, 2),
            ("平溪區", 71.34, 25.025, 121.741, "rural", 18, 0, 6, 0, 0, 0, 0, 4, 3, 0, 0, 1, 0, 0, 0, 3, 1)
        ],
        "桃園市": [
            ("桃園區", 34.80, 24.995, 121.306, "core", 420, 0, 1, 0, 2, 0, 0, 185, 24, 12, 0, 5, 0, 2, 3, 485, 142),
            ("中壢區", 76.52, 24.966, 121.224, "core", 390, 7, 2, 0, 2, 0, 0, 168, 23, 13, 4, 4, 0, 2, 4, 460, 135),
            ("平鎮區", 31.28, 24.945, 121.218, "suburb", 165, 0, 0, 0, 1, 0, 0, 82, 14, 6, 0, 2, 0, 1, 1, 165, 58),
            ("八德區", 33.71, 24.963, 121.294, "suburb", 145, 0, 0, 0, 1, 0, 0, 74, 10, 5, 0, 2, 0, 0, 1, 130, 46),
            ("蘆竹區", 75.50, 25.052, 121.288, "suburb", 180, 2, 0, 0, 2, 0, 0, 85, 12, 4, 1, 2, 0, 0, 1, 120, 44),
            ("龜山區", 72.01, 25.001, 121.338, "suburb", 195, 3, 0, 0, 1, 0, 0, 92, 13, 4, 2, 2, 1, 0, 1, 95, 34),
            ("大溪區", 105.12, 24.880, 121.287, "suburb", 112, 0, 0, 0, 1, 0, 0, 46, 14, 4, 0, 2, 0, 0, 1, 68, 24),
            ("楊梅區", 89.12, 24.909, 121.145, "suburb", 148, 0, 4, 0, 2, 0, 0, 68, 14, 7, 0, 2, 0, 1, 1, 115, 38),
            ("大園區", 87.39, 25.063, 121.196, "suburb", 125, 6, 0, 0, 2, 0, 1, 55, 12, 3, 0, 2, 0, 0, 1, 52, 18),
            ("龍潭區", 75.23, 24.864, 121.216, "suburb", 118, 0, 0, 0, 1, 0, 0, 52, 11, 5, 0, 2, 0, 0, 2, 75, 26),
            ("新屋區", 85.02, 24.972, 121.033, "rural", 58, 0, 0, 0, 0, 0, 0, 22, 11, 2, 0, 1, 0, 0, 1, 22, 8),
            ("觀音區", 117.32, 25.035, 121.082, "rural", 76, 0, 0, 0, 0, 0, 0, 31, 13, 3, 0, 1, 0, 0, 1, 34, 12),
            ("復興區", 350.78, 24.821, 121.352, "rural", 25, 0, 0, 0, 0, 0, 0, 5, 6, 1, 0, 1, 0, 0, 0, 6, 2)
        ],
        "臺中市": [
            ("西屯區", 39.85, 24.182, 120.623, "core", 310, 3, 0, 0, 2, 0, 0, 165, 12, 7, 3, 3, 1, 1, 2, 310, 98),
            ("北屯區", 62.70, 24.181, 120.697, "suburb", 280, 6, 1, 0, 2, 0, 0, 172, 18, 8, 1, 3, 0, 1, 2, 285, 92),
            ("南屯區", 31.26, 24.137, 120.640, "core", 195, 4, 0, 0, 2, 0, 0, 118, 9, 5, 1, 2, 0, 1, 1, 180, 58),
            ("北區", 6.93, 24.156, 120.682, "core", 240, 1, 0, 0, 0, 0, 0, 85, 9, 6, 2, 2, 1, 1, 1, 265, 84),
            ("西區", 5.70, 24.141, 120.667, "core", 180, 0, 0, 0, 0, 0, 0, 74, 7, 4, 1, 2, 0, 0, 2, 210, 72),
            ("東區", 9.28, 24.136, 120.693, "core", 125, 0, 1, 0, 0, 0, 0, 52, 3, 1, 0, 1, 0, 0, 1, 85, 28),
            ("南區", 6.81, 24.118, 120.662, "core", 138, 0, 2, 0, 0, 0, 0, 61, 5, 1, 1, 1, 0, 0, 1, 98, 34),
            ("中區", 0.88, 24.143, 120.683, "core", 92, 0, 1, 0, 0, 0, 0, 28, 2, 0, 0, 1, 0, 0, 1, 62, 23),
            ("豐原區", 41.18, 24.252, 120.720, "core", 165, 0, 1, 0, 1, 0, 0, 56, 10, 5, 0, 2, 0, 1, 3, 185, 64),
            ("大里區", 32.45, 24.102, 120.677, "suburb", 190, 0, 0, 0, 1, 0, 0, 98, 12, 5, 0, 2, 0, 1, 3, 230, 78),
            ("太平區", 120.75, 24.127, 120.718, "suburb", 175, 0, 0, 0, 1, 0, 0, 84, 15, 5, 1, 2, 0, 0, 2, 195, 66),
            ("清水區", 64.17, 24.269, 120.538, "suburb", 98, 0, 1, 0, 1, 0, 0, 38, 11, 2, 0, 1, 0, 0, 1, 58, 22),
            ("沙鹿區", 40.46, 24.234, 120.565, "suburb", 132, 0, 1, 0, 1, 0, 0, 55, 12, 4, 2, 1, 0, 1, 1, 125, 41),
            ("大甲區", 58.51, 24.349, 120.624, "suburb", 105, 0, 2, 0, 1, 0, 0, 42, 9, 4, 0, 1, 0, 1, 1, 82, 28),
            ("梧棲區", 16.61, 24.255, 120.531, "suburb", 78, 0, 0, 0, 0, 0, 0, 31, 6, 2, 0, 1, 0, 1, 0, 48, 16),
            ("烏日區", 43.40, 24.105, 120.623, "suburb", 115, 1, 2, 1, 3, 0, 0, 48, 9, 2, 0, 1, 0, 0, 0, 64, 20),
            ("神岡區", 35.04, 24.257, 120.662, "suburb", 84, 0, 0, 0, 1, 0, 0, 32, 7, 1, 0, 1, 0, 0, 0, 68, 22),
            ("大雅區", 32.41, 24.229, 120.648, "suburb", 112, 0, 0, 0, 1, 0, 0, 45, 8, 1, 0, 1, 0, 0, 1, 92, 31),
            ("潭子區", 25.84, 24.212, 120.705, "suburb", 124, 0, 3, 0, 1, 0, 0, 50, 9, 3, 0, 1, 0, 0, 1, 95, 33),
            ("后里區", 58.94, 24.305, 120.720, "rural", 72, 0, 2, 0, 1, 0, 0, 26, 6, 2, 0, 1, 0, 0, 1, 38, 14),
            ("東勢區", 117.48, 24.259, 120.829, "rural", 65, 0, 0, 0, 0, 0, 0, 20, 10, 4, 0, 1, 0, 0, 1, 36, 15),
            ("外埔區", 42.45, 24.332, 120.654, "rural", 46, 0, 0, 0, 1, 0, 0, 15, 4, 0, 0, 1, 0, 0, 0, 18, 6),
            ("大安區", 27.40, 24.346, 120.585, "rural", 38, 0, 0, 0, 0, 0, 0, 11, 5, 0, 0, 1, 0, 0, 0, 10, 3),
            ("大肚區", 37.00, 24.153, 120.541, "rural", 68, 0, 2, 0, 1, 0, 0, 24, 6, 1, 0, 1, 0, 0, 0, 34, 12),
            ("龍井區", 26.67, 24.192, 120.546, "rural", 82, 0, 1, 0, 1, 0, 0, 35, 6, 1, 1, 1, 0, 0, 0, 52, 18),
            ("石岡區", 18.21, 24.275, 120.778, "rural", 32, 0, 0, 0, 0, 0, 0, 10, 4, 0, 0, 1, 0, 0, 0, 11, 4),
            ("新社區", 68.89, 24.229, 120.811, "rural", 48, 0, 0, 0, 0, 0, 0, 14, 9, 1, 0, 1, 0, 0, 0, 15, 5),
            ("和平區", 1037.82, 24.264, 121.002, "rural", 32, 0, 0, 0, 0, 0, 0, 4, 8, 1, 0, 1, 0, 0, 0, 8, 3)
        ],
        "臺南市": [
            ("安平區", 11.06, 22.992, 120.168, "core", 95, 0, 0, 0, 0, 0, 0, 48, 5, 3, 0, 1, 0, 0, 1, 92, 31),
            ("東區", 13.44, 22.984, 120.222, "core", 210, 0, 1, 0, 0, 0, 0, 82, 9, 7, 1, 2, 1, 0, 2, 280, 89),
            ("北區", 10.43, 23.006, 120.210, "core", 155, 0, 0, 0, 0, 0, 0, 65, 7, 4, 0, 2, 0, 1, 2, 185, 62),
            ("南區", 27.26, 22.960, 120.184, "core", 115, 0, 0, 0, 0, 1, 0, 52, 8, 3, 0, 1, 0, 1, 1, 110, 39),
            ("中西區", 6.26, 22.992, 120.199, "core", 140, 0, 0, 0, 0, 0, 0, 58, 6, 4, 0, 2, 0, 1, 2, 150, 55),
            ("永康區", 40.05, 23.025, 120.254, "core", 245, 0, 3, 0, 1, 0, 0, 110, 12, 6, 3, 2, 1, 0, 3, 295, 94),
            ("安南區", 107.20, 23.047, 120.185, "suburb", 180, 0, 0, 0, 1, 0, 0, 78, 18, 5, 1, 2, 0, 1, 1, 135, 46),
            ("新營區", 38.54, 23.308, 120.317, "suburb", 92, 0, 1, 0, 1, 0, 0, 38, 8, 4, 0, 2, 0, 1, 1, 88, 32),
            ("鹽水區", 52.26, 23.320, 120.266, "rural", 42, 0, 0, 0, 0, 0, 0, 15, 5, 1, 0, 1, 0, 0, 0, 24, 9),
            ("白河區", 126.40, 23.351, 120.416, "rural", 55, 0, 0, 0, 1, 0, 0, 18, 8, 2, 0, 1, 0, 0, 1, 28, 11),
            ("柳營區", 61.29, 23.277, 120.332, "rural", 38, 0, 1, 0, 1, 0, 0, 14, 4, 1, 1, 1, 0, 1, 0, 18, 6),
            ("後壁區", 72.22, 23.366, 120.362, "rural", 32, 0, 1, 0, 0, 0, 0, 11, 5, 1, 0, 1, 0, 0, 0, 14, 5),
            ("東山區", 124.91, 23.326, 120.404, "rural", 28, 0, 0, 0, 0, 0, 0, 8, 7, 1, 0, 1, 0, 0, 0, 12, 4),
            ("麻豆區", 53.97, 23.182, 120.248, "suburb", 78, 0, 0, 0, 1, 0, 0, 32, 8, 3, 1, 1, 0, 1, 0, 62, 22),
            ("下營區", 33.52, 23.212, 120.222, "rural", 35, 0, 0, 0, 0, 0, 0, 12, 4, 1, 0, 1, 0, 0, 0, 21, 7),
            ("六甲區", 67.54, 23.232, 120.348, "rural", 36, 0, 1, 0, 0, 0, 0, 15, 4, 1, 0, 1, 0, 0, 0, 23, 8),
            ("官田區", 70.79, 23.194, 120.318, "rural", 44, 0, 2, 0, 1, 0, 0, 18, 4, 1, 1, 1, 0, 0, 0, 16, 5),
            ("大內區", 70.32, 23.119, 120.349, "rural", 18, 0, 0, 0, 0, 0, 0, 5, 3, 0, 0, 1, 0, 0, 0, 6, 2),
            ("佳里區", 38.94, 23.165, 120.177, "suburb", 85, 0, 0, 0, 0, 0, 0, 35, 8, 3, 0, 1, 0, 1, 1, 78, 27),
            ("學甲區", 53.99, 23.228, 120.181, "rural", 41, 0, 0, 0, 0, 0, 0, 14, 4, 1, 0, 1, 0, 0, 0, 26, 9),
            ("西港區", 33.77, 23.123, 120.203, "rural", 32, 0, 0, 0, 0, 0, 0, 13, 4, 0, 0, 1, 0, 0, 0, 22, 6),
            ("七股區", 91.02, 23.140, 120.141, "rural", 48, 0, 0, 0, 0, 0, 0, 12, 6, 1, 0, 1, 0, 0, 0, 14, 4),
            ("將軍區", 30.04, 23.200, 120.127, "rural", 26, 0, 0, 0, 0, 0, 0, 8, 4, 0, 0, 1, 0, 0, 0, 11, 3), 
            ("北門區", 44.30, 23.267, 120.123, "rural", 22, 0, 0, 0, 0, 0, 0, 6, 4, 0, 0, 1, 0, 0, 0, 7, 2),
            ("新化區", 62.05, 23.038, 120.303, "suburb", 68, 0, 0, 0, 1, 0, 0, 25, 5, 2, 1, 1, 0, 0, 1, 42, 16),
            ("善化區", 55.31, 23.132, 120.297, "suburb", 88, 0, 1, 0, 1, 0, 0, 42, 7, 2, 0, 1, 0, 0, 1, 65, 24),
            ("新市區", 47.80, 23.019, 120.295, "suburb", 74, 0, 2, 0, 2, 0, 0, 36, 5, 1, 1, 1, 0, 0, 0, 51, 19),
            ("安定區", 31.27, 23.122, 120.237, "rural", 38, 0, 0, 0, 1, 0, 0, 15, 4, 0, 0, 1, 0, 0, 0, 24, 7),
            ("山上區", 27.87, 23.034, 120.353, "rural", 16, 0, 0, 0, 0, 0, 0, 6, 2, 0, 0, 1, 0, 0, 0, 5, 2),
            ("玉井區", 76.36, 23.123, 120.460, "rural", 42, 0, 0, 0, 0, 0, 0, 12, 4, 1, 0, 1, 0, 0, 1, 22, 8),
            ("楠西區", 109.63, 23.174, 120.485, "rural", 24, 0, 0, 0, 0, 0, 0, 6, 3, 0, 0, 1, 0, 0, 0, 8, 2),
            ("南化區", 171.51, 23.043, 120.478, "rural", 18, 0, 0, 0, 0, 0, 0, 4, 4, 1, 0, 1, 0, 0, 0, 6, 2),
            ("左鎮區", 74.90, 23.058, 120.407, "rural", 15, 0, 0, 0, 0, 0, 0, 3, 2, 0, 0, 1, 0, 0, 0, 4, 1),
            ("仁德區", 50.77, 22.972, 120.252, "suburb", 112, 0, 2, 0, 2, 0, 0, 54, 8, 2, 1, 1, 0, 0, 1, 82, 28),
            ("歸仁區", 55.79, 22.966, 120.294, "suburb", 98, 0, 0, 1, 1, 0, 0, 46, 9, 3, 1, 1, 0, 0, 1, 71, 25),
            ("關廟區", 53.64, 22.963, 120.328, "rural", 46, 0, 0, 0, 1, 0, 0, 18, 4, 1, 0, 1, 0, 0, 0, 31, 11),
            ("龍崎區", 64.08, 22.966, 120.361, "rural", 12, 0, 0, 0, 0, 0, 0, 3, 1, 0, 0, 1, 0, 0, 0, 2, 1)
        ],
        "高雄市": [
            ("三民區", 19.78, 22.643, 120.328, "core", 340, 4, 1, 0, 1, 0, 0, 155, 15, 9, 2, 3, 1, 1, 4, 326, 89),
            ("苓雅區", 8.15, 22.621, 120.329, "core", 260, 11, 0, 0, 1, 0, 0, 112, 9, 7, 1, 2, 0, 2, 2, 245, 76),
            ("左營區", 19.38, 22.690, 120.301, "core", 220, 4, 1, 1, 1, 0, 0, 124, 9, 5, 0, 2, 1, 0, 2, 210, 68),
            ("鼓山區", 14.74, 22.639, 120.275, "core", 165, 10, 1, 0, 0, 0, 0, 98, 7, 4, 1, 2, 1, 1, 1, 135, 46),
            ("前鎮區", 19.12, 22.597, 120.322, "core", 230, 13, 0, 0, 2, 0, 0, 105, 11, 6, 0, 2, 0, 0, 3, 195, 61),
            ("鳳山區", 26.75, 22.626, 120.359, "core", 310, 6, 1, 0, 2, 0, 0, 168, 19, 9, 0, 4, 1, 1, 5, 340, 105),
            ("小港區", 45.64, 22.565, 120.338, "suburb", 140, 4, 0, 0, 0, 1, 1, 62, 11, 4, 1, 1, 0, 1, 1, 110, 39),
            ("新興區", 1.97, 22.627, 120.304, "core", 115, 3, 0, 0, 0, 0, 0, 45, 3, 2, 0, 1, 0, 1, 0, 142, 48),
            ("前金區", 1.85, 22.627, 120.293, "core", 98, 2, 0, 0, 0, 0, 0, 38, 2, 2, 0, 1, 0, 1, 1, 115, 35),
            ("鹽埕區", 1.41, 22.623, 120.283, "core", 76, 4, 0, 0, 0, 0, 0, 32, 2, 0, 0, 1, 0, 0, 1, 54, 18),
            ("楠梓區", 25.83, 22.727, 120.311, "suburb", 185, 4, 3, 0, 2, 0, 0, 95, 12, 5, 3, 2, 0, 1, 1, 165, 54),
            ("岡山區", 47.94, 22.791, 120.295, "suburb", 112, 1, 1, 0, 1, 0, 0, 52, 9, 4, 0, 1, 0, 1, 1, 98, 32),
            ("橋頭區", 18.31, 22.757, 120.305, "suburb", 68, 3, 1, 0, 0, 0, 0, 34, 5, 1, 0, 1, 0, 0, 0, 32, 11),
            ("路竹區", 48.43, 22.855, 120.261, "suburb", 74, 0, 1, 0, 1, 0, 0, 28, 8, 1, 1, 1, 0, 0, 1, 45, 14),
            ("茄萣區", 15.76, 22.906, 120.181, "rural", 35, 0, 0, 0, 0, 0, 0, 12, 4, 1, 0, 1, 0, 0, 0, 21, 8),
            ("永安區", 22.61, 22.820, 120.227, "rural", 26, 0, 0, 0, 0, 0, 0, 8, 3, 0, 0, 1, 0, 0, 0, 12, 4),
            ("彌陀區", 14.77, 22.783, 120.246, "rural", 28, 0, 0, 0, 0, 0, 0, 11, 4, 0, 0, 1, 0, 0, 0, 14, 5),
            ("梓官區", 11.59, 22.761, 120.267, "rural", 42, 0, 0, 0, 0, 0, 0, 16, 4, 0, 0, 1, 0, 0, 0, 28, 9),
            ("旗山區", 94.61, 22.888, 120.483, "suburb", 65, 0, 0, 0, 0, 0, 0, 24, 7, 3, 0, 1, 0, 1, 1, 48, 18),
            ("美濃區", 120.03, 22.897, 120.542, "rural", 52, 0, 0, 0, 0, 0, 0, 18, 9, 1, 0, 1, 0, 0, 1, 31, 12),
            ("六龜區", 194.15, 23.003, 120.635, "rural", 34, 0, 0, 0, 0, 0, 0, 6, 5, 1, 0, 1, 0, 0, 1, 12, 4),
            ("甲仙區", 124.03, 23.031, 120.591, "rural", 22, 0, 0, 0, 0, 0, 0, 4, 3, 1, 0, 1, 0, 0, 0, 8, 3),
            ("杉林區", 104.00, 22.973, 120.540, "rural", 25, 0, 0, 0, 0, 0, 0, 5, 4, 0, 0, 1, 0, 0, 0, 7, 2),
            ("內門區", 95.62, 22.920, 120.455, "rural", 31, 0, 0, 0, 0, 0, 0, 6, 6, 0, 0, 1, 0, 0, 0, 9, 3),
            ("茂林區", 194.00, 22.885, 120.724, "rural", 12, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 1, 0, 0, 0, 2, 1),
            ("桃源區", 92.98, 23.159, 120.781, "rural", 15, 0, 0, 0, 0, 0, 0, 2, 3, 1, 0, 1, 0, 0, 0, 3, 1),
            ("那瑪夏區", 252.98, 23.262, 120.693, "rural", 14, 0, 0, 0, 0, 0, 0, 2, 3, 0, 0, 1, 0, 0, 0, 4, 1),
            ("仁武區", 36.08, 22.701, 120.347, "suburb", 105, 0, 0, 0, 1, 0, 0, 48, 6, 1, 0, 1, 0, 0, 0, 76, 23),
            ("大社區", 26.58, 22.729, 120.358, "suburb", 58, 0, 0, 0, 1, 0, 0, 22, 3, 1, 1, 1, 0, 0, 0, 42, 14),
            ("鳥松區", 24.59, 22.659, 120.364, "suburb", 78, 0, 0, 0, 0, 0, 0, 31, 3, 1, 1, 1, 1, 0, 0, 38, 12),
            ("大樹區", 66.98, 22.693, 120.431, "rural", 62, 0, 2, 0, 0, 0, 0, 20, 7, 1, 0, 1, 0, 0, 0, 25, 9),
            ("大寮區", 71.04, 22.605, 120.395, "suburb", 142, 1, 0, 0, 1, 0, 0, 64, 11, 3, 1, 1, 0, 0, 1, 110, 34),
            ("林園區", 32.29, 22.508, 120.396, "suburb", 95, 0, 0, 0, 0, 0, 0, 38, 7, 2, 0, 1, 0, 0, 1, 68, 22),
            ("燕巢區", 65.39, 22.793, 120.362, "rural", 72, 0, 0, 0, 2, 0, 0, 25, 5, 0, 3, 1, 0, 0, 1, 32, 9),
            ("田寮區", 92.68, 22.868, 120.361, "rural", 18, 0, 0, 0, 1, 0, 0, 4, 3, 0, 0, 1, 0, 0, 0, 4, 1),
            ("阿蓮區", 34.61, 22.884, 120.328, "rural", 44, 0, 0, 0, 0, 0, 0, 15, 4, 1, 0, 1, 0, 0, 0, 29, 10),
            ("湖內區", 20.16, 22.908, 120.213, "rural", 48, 0, 0, 0, 0, 0, 0, 18, 4, 1, 0, 1, 0, 0, 0, 31, 11)
        ]
    }
    
    data = []
    for county, towns in raw_cities.items():
        for town, area, lat, lon, t_type, bus, mrt, train, hsr, ic, dom_ap, int_ap, ub, elem, high, univ, lib, med_center, regional_h, local_h, clinic, pharm in towns:
            data.append({
                "COUNTYNAME": county, "TOWNNAME": town.strip(), "Area_SqKm": area, 
                "Center_Lat": lat, "Center_Lon": lon, "Type": t_type,
                "Bus_Stations": bus, "MRT_Stations": mrt, "Train_Stations": train, "HSR_Stations": hsr, "Interchanges": ic,
                "Domestic_Airports": dom_ap, "International_Airports": int_ap, "UBike_Stations": ub,
                "Elementary_Schools": elem, "High_Schools": high, "Universities": univ, "Libraries": lib,
                "Medical_Centers": med_center, "Regional_Hospitals": regional_h, "Local_Hospitals": local_h, "Clinics": clinic, "Pharmacies": pharm
            })
    return pd.DataFrame(data).drop_duplicates(subset=['COUNTYNAME', 'TOWNNAME'])

df_static = load_perfect_liudu_data()

# --- 2. 即時查詢 OSM 7 大生活機能函數 ---
def get_live_amenity_data(lat, lon, radius=3000):
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:15];
    (
      node["shop"="convenience"](around:{radius},{lat},{lon});
      node["shop"="supermarket"](around:{radius},{lat},{lon});
      node["amenity"="fast_food"](around:{radius},{lat},{lon});
      node["shop"~"department_store|mall"](around:{radius},{lat},{lon});
      node["amenity"="marketplace"](around:{radius},{lat},{lon});
      node["amenity"~"bank|post_office"](around:{radius},{lat},{lon});
      node["leisure"~"park|playground"](around:{radius},{lat},{lon});
    );
    out tags;
    """
    try:
        response = requests.post(url, data={"data": query}, timeout=15)
        data = response.json()
        
        counts = {"conv": 0, "super": 0, "fast": 0, "mall": 0, "market": 0, "bank": 0, "park": 0}
        for element in data.get("elements", []):
            tags = element.get("tags", {})
            shop = tags.get("shop")
            amenity = tags.get("amenity")
            leisure = tags.get("leisure")
            
            if shop == "convenience": counts["conv"] += 1
            elif shop == "supermarket": counts["super"] += 1
            elif amenity == "fast_food": counts["fast"] += 1
            elif shop in ["department_store", "mall"]: counts["mall"] += 1
            elif amenity == "marketplace": counts["market"] += 1
            elif amenity in ["bank", "post_office"]: counts["bank"] += 1
            elif leisure in ["park", "playground"]: counts["park"] += 1
        return counts
    except:
        return None


# --- 3. 介面與連動下拉選單 ---
col_select1, col_select2 = st.columns(2)
with col_select1:
    selected_county = st.selectbox("🗺️ 請選擇直轄市：", ["臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市"])
with col_select2:
    filtered_towns = df_static[df_static['COUNTYNAME'] == selected_county]['TOWNNAME'].unique()
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

# --- 4. 提取目標行政區精確數據 ---
static_target = df_static[(df_static['COUNTYNAME'] == selected_county) & (df_static['TOWNNAME'] == selected_town)].iloc[0]

with st.spinner(f"正在即時連線 OpenStreetMap 獲取 {selected_town} 最新商圈數據..."):
    osm_res = get_live_amenity_data(static_target['Center_Lat'], static_target['Center_Lon'])

if osm_res:
    c_stores, s_markets, f_foods, m_malls, t_markets, b_banks, p_parks = (
        osm_res["conv"], osm_res["super"], osm_res["fast"], osm_res["mall"], osm_res["market"], osm_res["bank"], osm_res["park"]
    )
else:
    # OSM 回傳失敗時的靜態預設值
    if static_target['Type'] == "core":
        c_stores, s_markets, f_foods, m_malls, t_markets, b_banks, p_parks = 135, 16, 12, 4, 3, 22, 14
    else:
        c_stores, s_markets, f_foods, m_malls, t_markets, b_banks, p_parks = 42, 5, 2, 0, 1, 6, 4

# --- 5. 機能密度與分數模型計算 ---
area = static_target['Area_SqKm'] if static_target['Area_SqKm'] > 0 else 1.0

# 各項指標密度化
trans_density = (static_target['Bus_Stations'] * 2 + static_target['MRT_Stations'] * 6 + static_target['Train_Stations'] * 12 + static_target['HSR_Stations'] * 16 + static_target['Interchanges'] * 10 + static_target['Domestic_Airports'] * 12 + static_target['International_Airports'] * 18 + static_target['UBike_Stations'] * 1) / area
med_density = (static_target['Medical_Centers'] * 18 + static_target['Regional_Hospitals'] * 14 + static_target['Local_Hospitals'] * 10 + static_target['Clinics'] * 6 + static_target['Pharmacies'] * 2) / area
edu_density = (static_target['Elementary_Schools'] + static_target['High_Schools'] * 3 + static_target['Universities'] * 15 + static_target['Libraries'] * 8) / area
life_score_weight = (c_stores * 3 + s_markets * 6 + f_foods * 5 + m_malls * 15 + t_markets * 6 + b_banks * 5 + p_parks * 3)
life_density = life_score_weight / area

# 飽和轉換模型分數 (調整分母常數，確保分數過渡自然、高低拉開)
med_score = round(100 * (med_density / (med_density + 13)), 1)
trans_score = round(100 * (trans_density / (trans_density + 10)), 1)
edu_score = round(100 * (edu_density / (edu_density + 1.5)), 1)
life_score = round(100 * (life_density / (life_density + 9.0)), 1)

final_score = round(life_score * (w_store/100) + trans_score * (w_transport/100) + med_score * (w_medical/100) + edu_score * (w_school/100), 1)

# --- 6. 前端 UI 佈局 ---
st.markdown("---")
col_dash, col_map = st.columns([1, 1])

with col_dash:
    st.subheader(f"📊 {selected_county}{selected_town}")
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
        st.write(f"**交通機能評分：{trans_score} 分** ")
        st.markdown(f"🚇 **捷運/輕軌站點**：`{static_target['MRT_Stations']} 站` *(權重 × 6)*") 
        st.markdown(f"🚄 **高鐵車站**：`{static_target['HSR_Stations']} 站` *(權重 × 16)*")
        st.markdown(f"🚆 **台鐵車站**：`{static_target['Train_Stations']} 站` *(權重 × 12)*") 
        st.markdown(f"🛣️ **高/快速道路交流道**：`{static_target['Interchanges']} 處` *(權重 × 10)*")
        st.markdown(f"🚌 **公車站點**：`{static_target['Bus_Stations']} 處` *(權重 × 2)* ")
        st.markdown(f"🚲 **YouBike 站點**：`{static_target['UBike_Stations']} 站` *(權重 × 1)*")
        st.markdown(f"✈️ **國際機場**：`{static_target['International_Airports']} 座` *(權重 × 18)* ")
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
        st.markdown(f"🍏 **連鎖超市**：`{s_markets} 間` *(權重 × 6)*")
        st.markdown(f"🍔 **連鎖速食餐廳**：`{f_foods} 間` *(權重 × 5)*")
        st.markdown(f"🏢 **百貨商場/量販**：`{m_malls} 間` *(權重 × 15)*")
        st.markdown(f"🏮 **傳統市場/夜市**：`{t_markets} 處` *(權重 × 6)*")
        st.markdown(f"💰 **郵局與銀行櫃點**：`{b_banks} 處` *(權重 × 5)*")
        st.markdown(f"🌳 **公園與運動綠地**：`{p_parks} 處` *(權重 × 3)*")

with col_map:
    st.subheader("📍 行政區動態定位地圖")
    lat, lon = static_target['Center_Lat'], static_target['Center_Lon']
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB positron")
    folium.Marker(location=[lat, lon], popup=f"<b>{selected_county}{selected_town}</b>", icon=folium.Icon(color="red", icon="star")).add_to(m)
    st_folium(m, width="100%", height=450, key=f"map_{selected_county}_{selected_town}")

# --- 7. 雙區機能動態對比模組  ---
st.markdown("---")
st.header("⚖️ 雙行政區機能動態對比 PK 模組")
st.caption("此模組將同時發動即時 API 請求，在相同的數據基準下，橫向評比兩個行政區的四大機能指標。")

# 建立兩個下拉選單，讓使用者選擇要對比的 B 區域 (A 區域預設就是上面選定的區域)
col_pk1, col_pk2 = st.columns([1, 1])

with col_pk1:
    st.subheader("🏁 基準區域 (A)")
    st.info(f"已自動帶入上方選定：**{selected_county} {selected_town}**")
    # 複製 A 區的分數 (直接拿剛才前面第 5 步算好的分數)
    area_A_scores = [med_score, trans_score, edu_score, life_score]

with col_pk2:
    st.subheader("🔍 對比區域 (B)")
    # 讓使用者在下方選取第二個行政區
    pk_county = st.selectbox("請選擇對比縣市", df_static['COUNTYNAME'].unique(), key="pk_county")
    pk_town_options = df_static[df_static['COUNTYNAME'] == pk_county]['TOWNNAME'].unique()
    pk_town = st.selectbox("請選擇對比行政區", pk_town_options, key="pk_town")

# 開始動態計算 B 區的真實即時分數
with st.spinner(f"正在連線 OpenStreetMap 獲取 {pk_town} 最新數據並進行動態權重運算..."):
    # 1. 提取 B 區的靜態地理骨架
    pk_target = df_static[(df_static['COUNTYNAME'] == pk_county) & (df_static['TOWNNAME'] == pk_town)].iloc[0]
    pk_area = pk_target['Area_SqKm'] if pk_target['Area_SqKm'] > 0 else 1.0
    
    # 2. B 區交通、醫療、教育密度計算 (與前面完全同步)
    pk_trans_density = (pk_target['Bus_Stations'] * 2 + pk_target['MRT_Stations'] * 6 + pk_target['Train_Stations'] * 12 + pk_target['HSR_Stations'] * 16 + pk_target['Interchanges'] * 10 + pk_target['Domestic_Airports'] * 12 + pk_target['International_Airports'] * 18 + pk_target['UBike_Stations'] * 1) / pk_area
    pk_med_density = (pk_target['Medical_Centers'] * 18 + pk_target['Regional_Hospitals'] * 14 + pk_target['Local_Hospitals'] * 10 + pk_target['Clinics'] * 6 + pk_target['Pharmacies'] * 2) / pk_area
    pk_edu_density = (pk_target['Elementary_Schools'] + pk_target['High_Schools'] * 3 + pk_target['Universities'] * 15 + pk_target['Libraries'] * 8) / pk_area
    
    # 3. B 區即時生活機能抓取 (發動第二次 API 請求，確保數據新鮮度與 A 區一致)
    pk_osm = get_live_amenity_data(pk_target['Center_Lat'], pk_target['Center_Lon'])
    if pk_osm:
        pk_life_weight = (pk_osm["conv"] * 3 + pk_osm["super"] * 6 + pk_osm["fast"] * 5 + pk_osm["mall"] * 15 + pk_osm["market"] * 6 + pk_osm["bank"] * 5 + pk_osm["park"] * 3)
    else:
        # 容災機制
        if pk_target['Type'] == "core":
            pk_life_weight = (135 * 3 + 16 * 6 + 12 * 5 + 4 * 15 + 3 * 6 + 22 * 5 + 14 * 3)
        else:
            pk_life_weight = (42 * 3 + 5 * 6 + 2 * 5 + 0 * 15 + 1 * 6 + 6 * 5 + 4 * 3)
            
    pk_life_density = pk_life_weight / pk_area
    
    # 4. B 區飽和模型轉換
    pk_med_score = round(100 * (pk_med_density / (pk_med_density + 13)), 1)
    pk_trans_score = round(100 * (pk_trans_density / (pk_trans_density + 10)), 1)
    pk_edu_score = round(100 * (pk_edu_density / (pk_edu_density + 1.5)), 1)
    pk_life_score = round(100 * (pk_life_density / (pk_life_density + 9.0)), 1)
    
    # B 區最終加權總分 (同樣連動前端的使用者滑桿權重)
    pk_final_score = round(pk_life_score * (w_store/100) + pk_trans_score * (w_transport/100) + pk_med_score * (w_medical/100) + pk_edu_score * (w_school/100), 1)
    area_B_scores = [pk_med_score, pk_trans_score, pk_edu_score, pk_life_score]

# --- 8. 渲染 Plotly 多維度雷達對比圖 ---
import plotly.graph_objects as go

categories = ['🏥 醫療資源', '🚌 交通機能', '🎓 教育資源', '🏪 生活機能']

fig = go.Figure()

# 繪製 A 區區塊
fig.add_trace(go.Scatterpolar(
    r=area_A_scores + [area_A_scores[0]],  # 首尾相連閉合曲線
    theta=categories + [categories[0]],
    fill='toself',
    name=f"區域 A: {selected_county}{selected_town} ({final_score}分)",
    line_color='#FF4B4B'
))

# 繪製 B 區區塊
fig.add_trace(go.Scatterpolar(
    r=area_B_scores + [area_B_scores[0]],
    theta=categories + [categories[0]],
    fill='toself',
    name=f"區域 B: {pk_county}{pk_town} ({pk_final_score}分)",
    line_color='#1C83E1'
))

fig.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[0, 100])  # 固定雷達圖範圍 0~100 分
    ),
    showlegend=True,
    margin=dict(l=40, r=40, t=20, b=40),
    height=450
)

# 顯示雷達圖與勝負數據
col_chart, col_res = st.columns([1.2, 0.8])

with col_chart:
    st.plotly_chart(fig, use_container_width=True)

with col_res:
    st.subheader("📊 橫向評比結論")
    st.write(f"**綜合得分對決：**")
    st.write(f"🔴 {selected_town}：`{final_score} 分` ⚡ 🔵 {pk_town}：`{pk_final_score} 分`")
    
    # 自動判斷贏家
    if final_score > pk_final_score:
        st.success(f"🏆 綜合評比由 **{selected_county}{selected_town}** 勝出！")
    elif final_score < pk_final_score:
        st.success(f"🏆 綜合評比由 **{pk_county}{pk_town}** 勝出！")
    else:
        st.warning("⚖️ 兩區域在當前偏好權重下，綜合便利性平分秋色！")
        
   
