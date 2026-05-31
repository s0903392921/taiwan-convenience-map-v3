import requests
import streamlit as st
import pandas as pd
import folium
from folium import GeoJson, GeoJsonTooltip
from streamlit_folium import st_folium
import numpy as np
import json

st.set_page_config(page_title="台灣六都生活便利性評分系統 V6", layout="wide")
st.title("🏙️ 台灣六都生活便利性精細評分系統")

# ─────────────────────────────────────────
# 1. OSM 生活機能抓取
# ─────────────────────────────────────────
def get_osm_amenity_count(lat, lon, radius=3000):
    url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:15];
    (
      node["shop"="convenience"](around:{radius},{lat},{lon});
      way["shop"="convenience"](around:{radius},{lat},{lon});
      node["shop"="supermarket"](around:{radius},{lat},{lon});
      way["shop"="supermarket"](around:{radius},{lat},{lon});
      node["shop"="department_store"](around:{radius},{lat},{lon});
      way["shop"="department_store"](around:{radius},{lat},{lon});
    );
    out tags;
    """
    try:
        response = requests.post(url, data={"data": query}, timeout=15)
        data = response.json()
        store_count = super_m_count = dept_count = 0
        for element in data.get("elements", []):
            shop_type = element.get("tags", {}).get("shop")
            if shop_type == "convenience":    store_count += 1
            elif shop_type == "supermarket":  super_m_count += 1
            elif shop_type == "department_store": dept_count += 1
        return store_count, super_m_count, dept_count
    except:
        return None, None, None


# ─────────────────────────────────────────
# 2. 資料庫
# ─────────────────────────────────────────
@st.cache_data
def load_liudu_data():
    raw_cities = {
        "臺北市": [
            ("大安區",11.36,25.026,121.543,"core",0,0,1,0,0,1,2,2,452,128),
            ("信義區",11.20,25.033,121.564,"core",0,0,1,0,0,1,0,1,215,78),
            ("中正區",7.60,25.032,121.518,"core",1,0,0,0,0,2,1,1,280,85),
            ("中山區",13.68,25.068,121.533,"core",0,0,3,0,0,1,1,2,410,115),
            ("萬華區",8.85,25.029,121.499,"core",1,0,2,0,0,0,1,2,165,62),
            ("松山區",9.28,25.060,121.560,"core",1,0,1,1,1,0,2,2,295,90),
            ("大同區",5.68,25.063,121.513,"core",1,0,2,0,0,0,1,1,140,55),
            ("內湖區",31.58,25.069,121.589,"suburb",0,0,4,0,0,1,1,1,210,82),
            ("南港區",21.84,25.055,121.606,"suburb",1,1,3,0,0,0,1,1,95,41),
            ("文山區",31.50,24.998,121.570,"suburb",0,0,2,0,0,0,1,2,155,68),
            ("士林區",62.37,25.093,121.526,"suburb",0,0,1,0,0,1,1,1,245,92),
            ("北投區",56.82,25.132,121.500,"suburb",0,0,0,0,0,2,1,2,145,59),
        ],
        "新北市": [
            ("板橋區",23.14,25.011,121.465,"core",2,1,3,0,0,1,1,4,560,185),
            ("三重區",16.32,25.062,121.498,"core",0,0,3,0,0,0,1,3,310,112),
            ("中和區",20.14,24.999,121.498,"core",0,0,2,0,0,1,0,3,340,125),
            ("永和區",5.71,25.008,121.516,"core",0,0,0,0,0,0,1,2,220,88),
            ("新莊區",19.74,25.036,121.445,"core",0,0,3,0,0,0,1,3,305,108),
            ("新店區",120.22,24.968,121.541,"suburb",0,0,3,0,0,0,2,2,240,95),
            ("土城區",29.56,24.973,121.444,"suburb",0,0,2,0,0,0,1,1,160,64),
            ("蘆洲區",7.44,25.084,121.474,"core",0,0,1,0,0,0,0,2,175,58),
            ("汐止區",71.24,25.067,121.659,"suburb",3,0,4,0,0,0,1,1,125,48),
            ("樹林區",33.12,24.991,121.420,"suburb",2,0,1,0,0,0,0,3,110,45),
            ("淡水區",70.65,25.170,121.442,"suburb",0,0,0,0,0,0,1,1,135,52),
            ("三峽區",191.15,24.933,121.371,"rural",0,0,1,0,0,0,1,0,85,32),
            ("鶯歌區",21.12,24.954,121.347,"suburb",1,0,2,0,0,0,0,1,55,24),
            ("五股區",34.86,25.084,121.438,"suburb",0,0,4,0,0,0,0,0,48,19),
            ("泰山區",19.22,25.057,121.431,"suburb",0,0,2,0,0,0,0,1,38,15),
            ("林口區",54.15,25.077,121.391,"suburb",0,0,2,0,0,0,0,1,105,38),
            ("瑞芳區",70.73,25.108,121.805,"rural",4,0,2,0,0,0,0,1,22,10),
            ("深坑區",20.58,25.002,121.616,"rural",0,0,1,0,0,0,0,0,18,8),
            ("石碇區",144.35,24.991,121.658,"rural",0,0,2,0,0,0,0,0,5,2),
            ("坪林區",170.83,24.937,121.711,"rural",0,0,1,0,0,0,0,0,4,2),
            ("烏來區",321.13,24.864,121.551,"rural",0,0,0,0,0,0,0,0,2,1),
            ("八里區",39.49,25.147,121.400,"rural",0,0,2,0,0,0,0,1,24,9),
            ("三芝區",65.99,25.257,121.500,"rural",0,0,0,0,0,0,0,0,15,7),
            ("石門區",51.26,25.290,121.568,"rural",0,0,0,0,0,0,0,0,4,2),
            ("金山區",49.21,25.221,121.637,"rural",0,0,0,0,0,0,0,1,14,6),
            ("萬里區",63.37,25.175,121.689,"rural",0,0,0,0,0,0,0,0,9,4),
            ("平溪區",71.33,25.025,121.739,"rural",4,0,0,0,0,0,0,0,3,2),
            ("雙溪區",146.24,25.034,121.838,"rural",2,0,0,0,0,0,0,0,4,2),
            ("貢寮區",99.97,25.022,121.908,"rural",5,0,0,0,0,0,0,0,6,3),
        ],
        "桃園市": [
            ("桃園區",34.80,24.995,121.306,"core",1,0,2,0,0,0,2,3,485,142),
            ("中壢區",76.52,24.966,121.224,"core",2,0,3,0,0,0,2,4,460,135),
            ("平鎮區",31.28,24.945,121.218,"suburb",0,0,2,0,0,0,1,1,165,58),
            ("八德區",33.71,24.963,121.294,"suburb",0,0,1,0,0,0,0,1,130,46),
            ("楊梅區",89.12,24.908,121.146,"suburb",4,0,3,0,0,0,1,2,115,42),
            ("蘆竹區",75.50,25.052,121.288,"suburb",0,0,3,0,0,0,0,1,120,44),
            ("大園區",87.39,25.063,121.215,"rural",0,0,4,0,1,0,0,1,45,18),
            ("龜山區",72.01,25.001,121.338,"suburb",0,0,1,0,0,1,0,1,95,34),
            ("大溪區",105.12,24.880,121.287,"rural",0,0,2,0,0,0,0,1,48,19),
            ("龍潭區",75.23,24.862,121.216,"suburb",0,0,2,0,0,0,1,1,78,29),
            ("新屋區",85.02,24.972,121.105,"rural",0,0,1,0,0,0,1,0,22,10),
            ("觀音區",87.12,25.036,121.077,"rural",0,0,2,0,0,0,0,1,32,13),
            ("復興區",350.78,24.821,121.352,"rural",0,0,0,0,0,0,0,0,6,2),
        ],
        "臺中市": [
            ("西屯區",39.85,24.182,120.623,"core",0,0,4,0,0,1,1,2,310,98),
            ("北屯區",62.70,24.181,120.697,"suburb",1,0,4,0,0,0,1,2,285,92),
            ("南屯區",31.26,24.137,120.640,"core",0,0,3,0,0,0,1,1,180,58),
            ("北區",6.93,24.156,120.682,"core",0,0,0,0,0,1,1,1,265,84),
            ("西區",5.70,24.141,120.667,"core",0,0,0,0,0,0,0,2,210,72),
            ("東區",9.28,24.136,120.693,"core",1,0,0,0,0,0,1,1,115,41),
            ("南區",6.81,24.118,120.662,"core",1,0,0,0,0,0,1,1,145,49),
            ("中區",0.88,24.143,120.683,"core",1,0,0,0,0,0,1,1,65,28),
            ("太平區",120.75,24.127,120.722,"suburb",0,0,2,0,0,0,1,1,170,56),
            ("大里區",32.45,24.102,120.677,"suburb",0,0,3,0,0,0,1,3,230,78),
            ("霧峰區",98.08,24.062,120.700,"rural",0,0,4,0,0,0,1,1,55,22),
            ("烏日區",43.40,24.105,120.623,"suburb",2,1,4,0,0,0,1,0,68,25),
            ("豐原區",41.18,24.252,120.720,"core",1,0,2,0,0,0,1,3,185,64),
            ("后里區",35.94,24.305,120.716,"rural",2,0,1,0,0,0,0,1,42,16),
            ("石岡區",18.21,24.275,120.778,"rural",0,0,0,0,0,0,0,0,12,6),
            ("東勢區",117.41,24.258,120.829,"rural",0,0,0,0,0,0,0,2,45,19),
            ("和平區",1037.82,24.264,121.002,"rural",0,0,0,0,0,0,0,0,8,3),
            ("新社區",68.89,24.229,120.785,"rural",0,0,0,0,0,0,0,0,18,8),
            ("潭子區",25.84,24.208,120.705,"suburb",3,0,2,0,0,0,1,0,110,39),
            ("大雅區",32.41,24.229,120.648,"suburb",0,0,2,0,0,0,0,1,95,33),
            ("神岡區",35.04,24.257,120.662,"rural",0,0,2,0,0,0,0,0,52,21),
            ("大肚區",37.00,24.152,120.541,"rural",3,0,1,0,0,0,0,0,38,15),
            ("沙鹿區",40.46,24.233,120.565,"suburb",1,0,2,1,0,0,2,1,140,51),
            ("龍井區",38.04,24.215,120.547,"rural",1,0,2,0,0,0,0,0,68,24),
            ("梧棲區",16.60,24.255,120.531,"rural",0,0,1,0,0,0,1,0,45,18),
            ("清水區",64.17,24.269,120.537,"rural",1,0,3,0,0,0,0,0,75,29),
            ("大甲區",58.51,24.348,120.624,"suburb",2,0,0,0,0,0,1,1,78,31),
            ("外埔區",42.75,24.332,120.654,"rural",0,0,2,0,0,0,0,0,16,8),
            ("大安區(中)",27.40,24.346,120.584,"rural",0,0,1,0,0,0,0,0,9,4),
        ],
        "臺南市": [
            ("安平區",11.06,22.992,120.168,"core",0,0,0,0,0,0,0,1,92,31),
            ("東區",13.44,22.984,120.222,"core",1,0,1,0,0,1,0,2,280,89),
            ("北區",10.43,23.006,120.210,"core",0,0,0,0,0,0,1,2,185,62),
            ("南區",27.26,22.960,120.184,"core",0,0,2,1,0,0,1,1,110,39),
            ("中西區",6.26,22.992,120.199,"core",0,0,0,0,0,0,1,2,150,55),
            ("安南區",107.20,23.047,120.185,"suburb",0,0,3,0,0,0,1,1,135,46),
            ("永康區",40.05,23.025,120.254,"core",3,0,3,0,0,1,0,3,295,94),
            ("新營區",38.54,23.307,120.317,"suburb",1,0,1,0,0,0,1,2,98,36),
            ("鹽水區",52.26,23.320,120.266,"rural",0,0,1,0,0,0,0,0,21,9),
            ("白河區",126.40,23.351,120.416,"rural",0,0,1,0,0,0,0,1,24,11),
            ("柳營區",61.20,23.275,120.332,"rural",2,0,1,0,0,0,1,0,18,8),
            ("後壁區",72.22,23.366,120.362,"rural",1,0,0,0,0,0,0,0,12,6),
            ("東山區",124.91,23.325,120.404,"rural",0,0,1,0,0,0,0,0,11,5),
            ("麻豆區",53.97,23.181,120.249,"suburb",0,0,2,0,0,0,1,1,62,24),
            ("下營區",33.52,23.232,120.264,"rural",0,0,0,0,0,0,0,0,19,9),
            ("六甲區",67.54,23.232,120.348,"rural",1,0,1,0,0,0,0,0,18,8),
            ("官田區",70.72,23.195,120.320,"rural",2,0,2,0,0,0,0,0,16,7),
            ("大內區",70.31,23.119,120.352,"rural",0,0,0,0,0,0,0,0,4,2),
            ("佳里區",38.94,23.165,120.177,"suburb",0,0,0,0,0,0,1,1,72,26),
            ("學甲區",53.99,23.230,120.181,"rural",0,0,1,0,0,0,0,0,22,10),
            ("西港區",33.77,23.123,120.203,"rural",0,0,0,0,0,0,0,0,15,7),
            ("七股區",91.66,23.141,120.141,"rural",0,0,1,0,0,0,0,0,9,4),
            ("將軍區",30.04,23.204,120.127,"rural",0,0,0,0,0,0,0,0,8,4),
            ("北門區",44.10,23.267,120.125,"rural",0,0,2,0,0,0,0,0,5,2),
            ("新化區",62.05,23.038,120.342,"suburb",0,0,2,0,0,0,0,1,41,17),
            ("善化區",55.30,23.131,120.291,"suburb",1,0,1,0,0,0,0,1,58,22),
            ("新市區",47.80,23.018,120.295,"suburb",2,0,2,0,0,0,0,0,45,16),
            ("安定區",31.27,23.060,120.237,"rural",0,0,3,0,0,0,0,0,22,9),
            ("山上區",27.87,23.045,120.353,"rural",0,0,0,0,0,0,0,0,6,3),
            ("玉井區",76.36,23.123,120.463,"rural",0,0,0,0,0,0,0,1,18,8),
            ("楠西區",109.63,23.173,120.485,"rural",0,0,0,0,0,0,0,0,7,3),
            ("南化區",171.51,23.043,120.480,"rural",0,0,0,0,0,0,0,0,4,2),
            ("左鎮區",74.90,23.057,120.407,"rural",0,0,0,0,0,0,0,0,3,1),
            ("仁德區",50.77,22.972,120.252,"suburb",2,0,4,0,0,0,0,1,85,29),
            ("歸仁區",55.79,22.954,120.294,"suburb",0,1,2,0,0,0,0,1,76,25),
            ("關廟區",53.64,22.962,120.328,"rural",0,0,2,0,0,0,0,0,31,13),
            ("龍崎區",64.08,22.966,120.361,"rural",0,0,1,0,0,0,0,0,2,1),
        ],
        "高雄市": [
            ("三民區",19.78,22.643,120.328,"core",1,0,1,0,0,1,1,4,326,89),
            ("苓雅區",8.15,22.621,120.329,"core",0,0,2,0,0,0,2,2,245,76),
            ("左營區",19.38,22.690,120.301,"core",1,1,3,0,0,1,0,2,210,68),
            ("新興區",1.97,22.627,120.304,"core",0,0,0,0,0,0,0,3,115,42),
            ("前金區",1.85,22.627,120.296,"core",0,0,0,0,0,0,1,1,88,33),
            ("鹽埕區",1.41,22.625,120.284,"core",0,0,0,0,0,0,0,1,45,19),
            ("鼓山區",14.74,22.639,120.275,"core",1,0,0,0,0,0,1,1,135,46),
            ("前鎮區",19.12,22.597,120.322,"core",0,0,3,0,0,0,0,3,195,61),
            ("小港區",45.64,22.565,120.338,"suburb",0,0,1,1,1,0,1,1,110,39),
            ("鳳山區",26.75,22.626,120.359,"core",1,0,1,0,0,0,1,5,340,105),
            ("鳥松區",24.59,22.659,120.364,"suburb",0,0,0,0,0,1,0,0,42,16),
            ("大樹區",66.98,22.693,120.425,"rural",2,0,1,0,0,0,0,0,28,12),
            ("大社區",26.58,22.730,120.347,"rural",0,0,2,0,0,0,0,1,35,15),
            ("仁武區",36.08,22.699,120.348,"suburb",0,0,3,0,0,0,0,0,85,31),
            ("岡山區",47.94,22.785,120.295,"suburb",1,0,3,0,0,0,1,3,125,45),
            ("燕巢區",65.39,22.793,120.362,"rural",0,0,4,0,0,0,2,0,22,10),
            ("橋頭區",25.86,22.758,120.312,"suburb",1,0,0,0,0,0,0,0,48,18),
            ("梓官區",11.60,22.761,120.267,"rural",0,0,0,0,0,0,0,0,32,14),
            ("彌陀區",14.78,22.782,120.247,"rural",0,0,0,0,0,0,0,0,15,7),
            ("永安區",22.61,22.818,120.226,"rural",0,0,1,0,0,0,0,0,11,5),
            ("茄萣區",15.76,22.906,120.181,"rural",0,0,0,0,0,0,0,0,24,11),
            ("湖內區",20.16,22.874,120.213,"rural",1,0,0,0,0,0,0,0,26,12),
            ("路竹區",48.43,22.856,120.261,"suburb",1,0,2,0,0,0,0,2,52,21),
            ("阿蓮區",34.61,22.885,120.328,"rural",0,0,1,0,0,0,0,0,25,11),
            ("田寮區",92.68,22.868,120.361,"rural",0,0,2,0,0,0,0,0,4,2),
            ("旗山區",94.61,22.888,120.482,"rural",0,0,2,0,0,0,1,1,42,19),
            ("美濃區",120.03,22.898,120.542,"rural",0,0,0,0,0,0,0,1,35,16),
            ("內門區",95.62,22.919,120.455,"rural",0,0,0,0,0,0,0,0,8,4),
            ("杉林區",104.00,22.971,120.540,"rural",0,0,0,0,0,0,0,0,7,4),
            ("甲仙區",124.03,23.085,120.591,"rural",0,0,0,0,0,0,0,0,8,3),
            ("六龜區",194.15,23.003,120.632,"rural",0,0,0,0,0,0,0,0,11,5),
            ("茂林區",194.00,22.885,120.662,"rural",0,0,0,0,0,0,0,0,2,1),
            ("桃源區",928.98,23.159,120.781,"rural",0,0,0,0,0,0,0,0,3,1),
            ("那瑪夏區",252.98,23.262,120.692,"rural",0,0,0,0,0,0,0,0,3,1),
            ("林園區",32.29,22.508,120.396,"rural",0,0,0,0,0,0,0,2,65,24),
            ("大寮區",71.04,22.605,120.395,"suburb",1,0,2,0,0,0,0,2,105,38),
        ],
    }

    data = []
    for county, towns in raw_cities.items():
        for town, area, lat, lon, t_type, train, hsr, ic, dom_ap, int_ap, med_center, regional_h, local_h, clinic, pharm in towns:
            if t_type == "core":
                bus = int(area*8+15); mrt = int(area*0.5+2); ub = int(area*5+10)
                elem = int(area*0.8+3); high = int(area*0.5+2); univ = int(area*0.1+1)
                store = int(area*6+25); sup = int(area*1.2+5); dept = int(area*0.1+1); cafe = int(area*4+10)
            elif t_type == "suburb":
                bus = int(area*3+10); mrt = int(area*0.1); ub = int(area*2+5)
                elem = int(area*0.4+2); high = int(area*0.2+1); univ = 0
                store = int(area*2.5+10); sup = int(area*0.4+2); dept = 0; cafe = int(area*1+2)
            else:
                bus = max(int(area*0.5),5); mrt = 0; ub = max(int(area*0.1),1)
                elem = max(int(area*0.05),1); high = 0; univ = 0
                store = max(int(area*0.15),2); sup = max(int(area*0.02),1); dept = 0; cafe = max(int(area*0.05),1)

            real_s, real_sup, real_dept = get_osm_amenity_count(lat, lon, radius=3000)
            if real_s is not None:
                store = real_s; sup = real_sup; dept = real_dept

            data.append({
                "COUNTYNAME": county, "TOWNNAME": town.strip(),
                "Area_SqKm": area, "Center_Lat": lat, "Center_Lon": lon,
                "Bus_Stations": bus, "MRT_Stations": mrt, "Train_Stations": train,
                "HSR_Stations": hsr, "Interchanges": ic,
                "Domestic_Airports": dom_ap, "International_Airports": int_ap,
                "UBike_Stations": ub, "Elementary_Schools": elem,
                "High_Schools": high, "Universities": univ,
                "Convenience_Stores": store, "Supermarkets": sup,
                "Department_Stores": dept, "Coffee_Shops": cafe,
                "Medical_Centers": med_center, "Regional_Hospitals": regional_h,
                "Local_Hospitals": local_h, "Clinics": clinic, "Pharmacies": pharm,
            })

    df = pd.DataFrame(data)
    df['trans_density'] = (df['Bus_Stations']*3 + df['MRT_Stations']*6 + df['Train_Stations']*12 +
        df['HSR_Stations']*16 + df['Interchanges']*10 + df['Domestic_Airports']*12 +
        df['International_Airports']*20 + df['UBike_Stations']*2) / df['Area_SqKm']
    df['med_density']  = (df['Medical_Centers']*18 + df['Regional_Hospitals']*14 +
        df['Local_Hospitals']*10 + df['Clinics']*6 + df['Pharmacies']*2) / df['Area_SqKm']
    df['edu_density']  = (df['Elementary_Schools'] + df['High_Schools']*3 + df['Universities']*15) / df['Area_SqKm']
    df['life_density'] = (df['Convenience_Stores'] + df['Supermarkets']*8 +
        df['Department_Stores']*40 + df['Coffee_Shops']*2) / df['Area_SqKm']
    df['trans_density_score'] = (100*(df['trans_density']/(df['trans_density']+35))).round(1)
    df['med_density_score']   = (100*(df['med_density']/(df['med_density']+15))).round(1)
    df['edu_density_score']   = (100*(df['edu_density']/(df['edu_density']+1.5))).round(1)
    df['life_density_score']  = (100*(df['life_density']/(df['life_density']+15))).round(1)
    return df


# ─────────────────────────────────────────
# 3. 載入 GeoJSON（從 CDN，cache 起來）
# ─────────────────────────────────────────
@st.cache_data(show_spinner="載入台灣地圖中…")
def load_geojson():
    url = "https://cdn.jsdelivr.net/npm/taiwan-atlas@0.0.3/towns-10t.json"
    try:
        import topojson as tp
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        topo = tp.Topology(resp.json(), object_name="towns")
        gdf = topo.to_geodataframe()
        return json.loads(gdf.to_json())
    except Exception as e:
        st.warning(f"地圖邊界載入失敗（{e}），將使用標記模式顯示")
        return None


# ─────────────────────────────────────────
# 4. 顏色工具
# ─────────────────────────────────────────
def score_color(s):
    if s is None: return "#cccccc"
    if s >= 75:   return "#1db954"
    if s >= 60:   return "#4a9eff"
    if s >= 45:   return "#f5c842"
    if s >= 30:   return "#f07030"
    return "#e8445a"


# ─────────────────────────────────────────
# 5. Session state 初始化
# ─────────────────────────────────────────
if "sel_county" not in st.session_state:
    st.session_state["sel_county"] = "臺北市"
if "sel_town" not in st.session_state:
    st.session_state["sel_town"] = "大安區"


# ─────────────────────────────────────────
# 6. 載入資料
# ─────────────────────────────────────────
df_all = load_liudu_data()

# ─────────────────────────────────────────
# 7. 側邊欄權重
# ─────────────────────────────────────────
st.sidebar.header("🔧 便利性指標權重配置")
w_store     = st.sidebar.slider("🏪 生活機能",   0, 100, 30)
w_transport = st.sidebar.slider("🚌 交通便利性", 0, 100, 30)
w_medical   = st.sidebar.slider("🏥 醫療資源",   0, 100, 20)
w_school    = st.sidebar.slider("🎓 教育資源",   0, 100, 20)
if (w_store + w_transport + w_medical + w_school) != 100:
    st.sidebar.error("❌ 權重總和必須等於 100%")
    st.stop()

df_all['綜合便利性得分'] = (
    df_all['life_density_score']  * (w_store/100) +
    df_all['trans_density_score'] * (w_transport/100) +
    df_all['med_density_score']   * (w_medical/100) +
    df_all['edu_density_score']   * (w_school/100)
).round(1)


# ─────────────────────────────────────────
# 8. 上方選單（連動 + session_state）
# ─────────────────────────────────────────
col_s1, col_s2 = st.columns(2)
available_counties = ["臺北市","新北市","桃園市","臺中市","臺南市","高雄市"]

with col_s1:
    county_idx = available_counties.index(st.session_state["sel_county"]) \
        if st.session_state["sel_county"] in available_counties else 0
    selected_county = st.selectbox("🗺️ 請選擇直轄市：", available_counties,
                                    index=county_idx, key="county_box")
    st.session_state["sel_county"] = selected_county

with col_s2:
    towns_list = sorted(df_all[df_all['COUNTYNAME']==selected_county]['TOWNNAME'].unique())
    town_idx = towns_list.index(st.session_state["sel_town"]) \
        if st.session_state["sel_town"] in towns_list else 0
    selected_town = st.selectbox("📍 請選擇鄉鎮市區：", towns_list,
                                  index=town_idx, key="town_box")
    st.session_state["sel_town"] = selected_town

target_data = df_all[
    (df_all['COUNTYNAME']==selected_county) &
    (df_all['TOWNNAME']==selected_town)
].iloc[0]

st.markdown("---")


# ─────────────────────────────────────────
# 9. 主版面：詳細資料（左）+ 地圖（右）
# ─────────────────────────────────────────
col_dash, col_map = st.columns([1, 1])

# ── 左：詳細資料 ──────────────────────────
with col_dash:
    st.subheader(f"📊 {selected_county} {selected_town} · 詳細機能指標")
    st.metric("🏆 綜合生活便利性得分", f"{target_data['綜合便利性得分']} / 100 分")

    tab1, tab2, tab3, tab4 = st.tabs(["🏥 醫療資源","🚌 交通機能","🎓 教育資源","🏪 生活機能"])

    with tab1:
        score = target_data['med_density_score']
        st.write(f"**醫療評分：{score} 分**")
        st.progress(int(score))
        st.markdown(f"🩺 **醫學中心**：`{target_data['Medical_Centers']} 間` *(×18)*")
        st.markdown(f"🏥 **區域醫院**：`{target_data['Regional_Hospitals']} 間` *(×14)*")
        st.markdown(f"🏢 **地區醫院**：`{target_data['Local_Hospitals']} 間` *(×10)*")
        st.markdown(f"👨‍⚕️ **診所**：`{target_data['Clinics']} 間` *(×6)*")
        st.markdown(f"💊 **藥局**：`{target_data['Pharmacies']} 家` *(×2)*")

    with tab2:
        score = target_data['trans_density_score']
        st.write(f"**交通評分：{score} 分**")
        st.progress(int(score))
        st.markdown(f"✈️ 國際機場：`{target_data['International_Airports']}` *(×20)*　🛫 國內機場：`{target_data['Domestic_Airports']}` *(×12)*")
        st.markdown(f"🚄 高鐵：`{target_data['HSR_Stations']}` *(×16)*　🚂 台鐵：`{target_data['Train_Stations']}` *(×12)*")
        st.markdown(f"🚗 交流道：`{target_data['Interchanges']}` *(×10)*")
        st.markdown(f"🚇 捷運/輕軌：`{target_data['MRT_Stations']}` *(×6)*　🚌 公車：`{target_data['Bus_Stations']}` *(×3)*")
        st.markdown(f"🚲 YouBike：`{target_data['UBike_Stations']}` *(×2)*")

    with tab3:
        score = target_data['edu_density_score']
        st.write(f"**教育評分：{score} 分**")
        st.progress(int(score))
        st.markdown(f"🎒 國民小學：`{target_data['Elementary_Schools']} 所`")
        st.markdown(f"🏫 國高中職：`{target_data['High_Schools']} 所`")
        st.markdown(f"🎓 大專院校：`{target_data['Universities']} 所`")

    with tab4:
        score = target_data['life_density_score']
        st.write(f"**生活機能評分：{score} 分**")
        st.progress(int(score))
        st.markdown(f"🏪 便利商店：`{target_data['Convenience_Stores']} 家`")
        st.markdown(f"🍏 連鎖超市：`{target_data['Supermarkets']} 間`")
        st.markdown(f"🏢 百貨/量販：`{target_data['Department_Stores']} 間`")
        st.markdown(f"☕ 咖啡廳：`{target_data['Coffee_Shops']} 間`")


# ── 右：地圖 ──────────────────────────────
with col_map:
    st.subheader("🗺️ 行政區評分地圖")
    st.caption("顏色 = 綜合分數　點擊色塊可查詢該行政區")

    geojson = load_geojson()

    # 縣市中心座標
    COUNTY_CENTER = {
        "臺北市":[25.05,121.55],"新北市":[25.01,121.46],
        "桃園市":[24.99,121.30],"臺中市":[24.16,120.65],
        "臺南市":[23.00,120.21],"高雄市":[22.63,120.30],
    }
    # 縣市別名（TopoJSON 可能用台/臺）
    COUNTY_ALIAS = {
        "臺北市":["臺北市","台北市"], "新北市":["新北市"],
        "桃園市":["桃園市"],          "臺中市":["臺中市","台中市"],
        "臺南市":["臺南市","台南市"], "高雄市":["高雄市"],
    }
    six_aliases = {alias: std for std, lst in COUNTY_ALIAS.items() for alias in lst}

    # 建立分數查找表
    score_lookup = {
        (r["COUNTYNAME"], r["TOWNNAME"]): r["綜合便利性得分"]
        for _, r in df_all.iterrows()
    }

    center = COUNTY_CENTER.get(selected_county, [23.8, 120.9])
    m = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron", control_scale=True)

    if geojson:
        # 把分數注入 GeoJSON properties
        for feat in geojson["features"]:
            p = feat["properties"]
            raw_county = p.get("COUNTYNAME","")
            town = p.get("TOWNNAME","").strip()
            std = six_aliases.get(raw_county)
            if std:
                p["score"] = score_lookup.get((std, town))
                p["std_county"] = std
                p["in_six"] = True
            else:
                p["score"] = None
                p["std_county"] = raw_county
                p["in_six"] = False

        def style_fn(feat):
            p = feat["properties"]
            s = p.get("score")
            is_sel = (p.get("std_county")==selected_county and
                      p.get("TOWNNAME","").strip()==selected_town)
            if not p.get("in_six"):
                return {"fillColor":"#e0e0e0","color":"#ccc","weight":0.3,"fillOpacity":0.25}
            return {
                "fillColor": score_color(s),
                "color": "#ffffff" if is_sel else "#666666",
                "weight": 3 if is_sel else 0.6,
                "fillOpacity": 0.82,
            }

        GeoJson(
            geojson,
            style_function=style_fn,
            highlight_function=lambda f: {"weight":2.5,"color":"#fff","fillOpacity":0.95},
            tooltip=GeoJsonTooltip(
                fields=["std_county","TOWNNAME","score"],
                aliases=["縣市：","行政區：","分數："],
                localize=True,
                style=("background:white;padding:6px 10px;"
                       "border-radius:5px;font-size:13px;"),
            ),
            popup=folium.GeoJsonPopup(
                fields=["std_county","TOWNNAME","score"],
                aliases=["縣市","行政區","分數"],
            ),
        ).add_to(m)

    else:
        # fallback：圓形標記
        county_df = df_all[df_all['COUNTYNAME']==selected_county]
        for _, row in county_df.iterrows():
            s = row["綜合便利性得分"]
            folium.CircleMarker(
                location=[row["Center_Lat"], row["Center_Lon"]],
                radius=6 + s/20,
                fill=True, fill_color=score_color(s), color="white",
                weight=1, fill_opacity=0.85,
                tooltip=f"{row['TOWNNAME']}　{s}分",
                popup=folium.Popup(f"<b>{row['COUNTYNAME']} {row['TOWNNAME']}</b><br>分數：{s}",max_width=160),
            ).add_to(m)

    # 目前選取的行政區加星形標記
    folium.Marker(
        location=[target_data["Center_Lat"], target_data["Center_Lon"]],
        tooltip=f"▶ {selected_town}　{target_data['綜合便利性得分']}分",
        icon=folium.Icon(color="red", icon="star"),
    ).add_to(m)

    # 圖例
    legend = """
    <div style="position:fixed;bottom:28px;right:18px;z-index:999;
                background:white;border-radius:8px;padding:10px 14px;
                border:1px solid #ddd;font-size:12px;box-shadow:0 2px 6px rgba(0,0,0,.15)">
      <b style="display:block;margin-bottom:5px">分數等級</b>
      <span style="background:#1db954;display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px"></span>優質 75+<br>
      <span style="background:#4a9eff;display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px"></span>良好 60–74<br>
      <span style="background:#f5c842;display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px"></span>普通 45–59<br>
      <span style="background:#f07030;display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px"></span>偏低 30–44<br>
      <span style="background:#e8445a;display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:5px"></span>不足 &lt;30
    </div>"""
    m.get_root().html.add_child(folium.Element(legend))

    # 顯示地圖，並接收點擊事件
    map_result = st_folium(m, width="100%", height=500,
                           returned_objects=["last_object_clicked_popup"],
                           key=f"map_{selected_county}_{selected_town}")

    # 點擊色塊 → 更新選單
    clicked = map_result.get("last_object_clicked_popup") if map_result else None
    if clicked:
        import re
        raw = str(clicked)
        c_match = re.search(r"(臺北市|台北市|新北市|桃園市|臺中市|台中市|臺南市|台南市|高雄市)", raw)
        t_match = re.search(r"行政區\s*[\|\s]+([^\s\|<]+[區鎮鄉])", raw)
        if c_match and t_match:
            clicked_county_raw = c_match.group(1)
            clicked_county = {"台北市":"臺北市","台中市":"臺中市","台南市":"臺南市"}.get(
                clicked_county_raw, clicked_county_raw)
            clicked_town = t_match.group(1).strip()
            if (clicked_county != st.session_state["sel_county"] or
                    clicked_town != st.session_state["sel_town"]):
                st.session_state["sel_county"] = clicked_county
                st.session_state["sel_town"]   = clicked_town
                st.rerun()


# ─────────────────────────────────────────
# 10. 排行榜
# ─────────────────────────────────────────
st.markdown("---")
st.subheader("🏆 六都生活便利性總排行榜（前 15 名）")
df_rank = (df_all[['COUNTYNAME','TOWNNAME','綜合便利性得分']]
           .sort_values('綜合便利性得分', ascending=False)
           .reset_index(drop=True))
df_rank.index += 1
st.dataframe(df_rank.head(15), use_container_width=True)
