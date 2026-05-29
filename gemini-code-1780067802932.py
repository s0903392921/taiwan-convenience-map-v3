import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json

# 1. 網頁基本設定 (網頁標題與排版)
st.set_page_config(
    page_title="台灣生活便利性評分地圖系統", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. 準備內建數據 (這樣你就不用另外下載 CSV 檔了，直接就能跑！)
@st.cache_data
def get_taiwan_data():
    # 這裡包含了全台主要縣市的行政區、面積與各項設施數量（基礎示範數據）
    data = [
        # 台北市
        {"COUNTYNAME": "臺北市", "TOWNNAME": "大安區", "Area": 11.36, "Store": 150, "Transport": 45, "Medical": 120, "School": 30},
        {"COUNTYNAME": "臺北市", "TOWNNAME": "信義區", "Area": 11.20, "Store": 130, "Transport": 38, "Medical": 85, "School": 22},
        {"COUNTYNAME": "臺北市", "TOWNNAME": "內湖區", "Area": 31.58, "Store": 110, "Transport": 25, "Medical": 70, "School": 25},
        {"COUNTYNAME": "臺北市", "TOWNNAME": "文山區", "Area": 31.50, "Store": 85, "Transport": 20, "Medical": 60, "School": 28},
        # 新北市
        {"COUNTYNAME": "新北市", "TOWNNAME": "板橋區", "Area": 23.14, "Store": 180, "Transport": 55, "Medical": 140, "School": 35},
        {"COUNTYNAME": "新北市", "TOWNNAME": "三重區", "Area": 16.32, "Store": 140, "Transport": 40, "Medical": 110, "School": 24},
        {"COUNTYNAME": "新北市", "TOWNNAME": "淡水區", "Area": 70.65, "Store": 95, "Transport": 15, "Medical": 50, "School": 18},
        # 台中市
        {"COUNTYNAME": "臺中市", "TOWNNAME": "西屯區", "Area": 39.85, "Store": 145, "Transport": 30, "Medical": 90, "School": 26},
        {"COUNTYNAME": "臺中市", "TOWNNAME": "北屯區", "Area": 62.70, "Store": 135, "Transport": 22, "Medical": 80, "School": 28},
        # 高雄市
        {"COUNTYNAME": "高雄市", "TOWNNAME": "三民區", "Area": 19.78, "Store": 160, "Transport": 48, "Medical": 130, "School": 32},
        {"COUNTYNAME": "高雄市", "TOWNNAME": "苓雅區", "Area": 8.15, "Store": 105, "Transport": 35, "Medical": 95, "School": 20},
        {"COUNTYNAME": "高雄市", "TOWNNAME": "左營區", "Area": 19.38, "Store": 120, "Transport": 42, "Medical": 88, "School": 21},
    ]
    return pd.DataFrame(data)

df_base = get_taiwan_data()

# 3. 網站頂部標題區
st.title("🗺️ 台灣生活便利性評分地圖系統")
st.markdown("歡迎使用本系統！你可以透過左側控制面板調整各項生活指標的**權重**，網站會即時計算全台各行政區的便利性得分並刷新地圖。")
st.markdown("---")

# 4. 側邊欄控制面板 (讓使用者互動的地方)
st.sidebar.header("🔧 便利性指標權重配置")
st.sidebar.markdown("請分配各指標的比例（總和必須為 100%）：")

w_store = st.sidebar.slider("🏪 生活機能 (超商/超市)", 0, 100, 30)
w_transport = st.sidebar.slider("🚌 交通便利性 (捷運/公車)", 0, 100, 30)
w_medical = st.sidebar.slider("🏥 醫療資源 (醫院/診所)", 0, 100, 20)
w_school = st.sidebar.slider("🎓 教育資源 (各級學校)", 0, 100, 20)

total_weight = w_store + w_transport + w_medical + w_school
st.sidebar.write(f"📊 當前權重總和: **{total_weight}%**")

# 檢查權重是否正確
if total_weight != 100:
    st.sidebar.error("❌ 錯誤：權重總和必須等於 100%，請重新調整！")
    st.stop()

# 5. 後端核心演算法：計算「每平方公里密度」與「標準化得分」
df_calc = df_base.copy()

# 計算密度
df_calc['store_density'] = df_calc['Store'] / df_calc['Area']
df_calc['transport_density'] = df_calc['Transport'] / df_calc['Area']
df_calc['medical_density'] = df_calc['Medical'] / df_calc['Area']
df_calc['school_density'] = df_calc['School'] / df_calc['Area']

# 將密度標準化為 0~100 的相對分數 (Min-Max Scaling)
for col in ['store_density', 'transport_density', 'medical_density', 'school_density']:
    max_val = df_calc[col].max()
    min_val = df_calc[col].min()
    if max_val != min_val:
        df_calc[f'{col}_score'] = ((df_calc[col] - min_val) / (max_val - min_val)) * 100
    else:
        df_calc[f'{col}_score'] = 0

# 計算最終加權總分
df_calc['綜合便利性得分'] = (
    df_calc['store_density_score'] * (w_store / 100) +
    df_calc['transport_density_score'] * (w_transport / 100) +
    df_calc['medical_density_score'] * (w_medical / 100) +
    df_calc['school_density_score'] * (w_school / 100)
).round(1)

# 6. 網頁前端排版：左右雙欄 (左邊地圖，右邊數據榜)
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 台灣行政區便利性分布圖")
    
    # 建立地圖物件 (以台灣為中心)
    # 這裡使用簡單的標記點(Marker)來展示，如果之後你有 GeoJSON 檔案可以升級成面量圖
    m = folium.Map(location=[24.5, 121.2], zoom_start=8, tiles="CartoDB positron")
    
    # 地圖座標對照表 (模擬經緯度)
    geo_coords = {
        "大安區": [25.026, 121.543], "信義區": [25.033, 121.564], "內湖區": [25.069, 121.589], "文山區": [24.998, 121.570],
        "板橋區": [25.011, 121.465], "三重區": [25.062, 121.498], "淡水區": [25.170, 121.442],
        "西屯區": [24.182, 120.623], "北屯區": [24.181, 120.697],
        "三民區": [22.643, 120.328], "苓雅區": [22.621, 120.329], "左營區": [22.690, 120.301]
    }
    
    # 在地圖上畫出每個行政區的圓圈，分數越高，圓圈越大、顏色越紅
    for idx, row in df_calc.iterrows():
        town = row['TOWNNAME']
        score = row['綜合便利性得分']
        if town in geo_coords:
            color = "red" if score > 75 else "orange" if score > 50 else "blue"
            folium.CircleMarker(
                location=geo_coords[town],
                radius=10 + (score / 10), # 讓圓圈大小隨分數變化
                popup=f"<b>{row['COUNTYNAME']}{town}</b><br>綜合得分: {score} 分",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.6
            ).add_to(m)
            
    # 將地圖渲染到網頁上
    st_folium(m, width="100%", height=550)

with col2:
    st.subheader("🏆 便利性排行名次")
    # 排序並顯示前幾名
    df_rank = df_calc[['COUNTYNAME', 'TOWNNAME', '綜合便利性得分']].sort_values(by='綜合便利性得分', ascending=False).reset_index(drop=True)
    df_rank.index = df_rank.index + 1 # 讓排名從 1 開始
    st.dataframe(df_rank, use_container_width=True, height=500)