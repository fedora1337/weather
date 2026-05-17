import streamlit as st
import requests
import sqlite3
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Weather App VN", page_icon="🌤️", layout="wide")
API_KEY = "fea69cfc8faa321e7b8bf3ae77bc33d2"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

DB_PATH = r"weather/weather_history.db"  # tránh OneDrive

# -----------------------------
# Khởi tạo DB
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            temperature REAL,
            feels_like REAL,
            humidity INTEGER,
            pressure INTEGER,
            wind_speed REAL,
            description TEXT,
            sunrise TEXT,
            sunset TEXT,
            time TEXT,
            lat REAL,
            lon REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# Hàm ghi dữ liệu vào DB
# -----------------------------
def save_weather(city, temp, feels_like, humidity, pressure, wind_speed, desc, sunrise, sunset, lat, lon):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
        INSERT INTO history (city, temperature, feels_like, humidity, pressure, wind_speed, description, sunrise, sunset, time, lat, lon)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (city, temp, feels_like, humidity, pressure, wind_speed, desc, sunrise, sunset,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S"), lat, lon))
    conn.commit()
    conn.close()

# -----------------------------
# Cache dữ liệu đọc
# -----------------------------
@st.cache_data
def get_history(city):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    rows = c.execute("SELECT city, temperature, time FROM history WHERE city=? ORDER BY id DESC LIMIT 20", (city,)).fetchall()
    conn.close()
    return rows

# -----------------------------
# Giao diện chính
# -----------------------------
st.title("🌤️ Ứng dụng dự đoán thời tiết Việt Nam")
if "citytextinput" not in st.session_state:
    st.session_state.citytextinput = ""

# Hàm reset text_input khi selectbox thay đổi
def on_select_change():
    st.session_state.citytextinput = ""   # reset về rỗng
citytextinput = st.text_input("Nhập tên thành phố:", "", key="citytextinput")
cities = ["Hà Nội", "Đà Nẵng", "Thành phố Hồ Chí Minh", "Huế", "Cần Thơ","Hải Phòng"]
cityselectbox = st.selectbox("Thành phố đề xuất:", cities,on_change=on_select_change)

# Sử dụng thành phố từ input hoặc selectbox
city = citytextinput if citytextinput.strip()!="" else cityselectbox

if st.button("🔍 Xem thời tiết"):
    params = {"q": f"{city},VN", "appid": API_KEY, "units": "metric", "lang": "vi"}
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind_speed = data["wind"]["speed"]
        desc = data["weather"][0]["description"]
        sunrise = datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%H:%M:%S")
        sunset = datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%H:%M:%S")
        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]

        # Hiển thị thông tin
        col1, col2, col3 = st.columns(3)
        col1.metric("🌡️ Nhiệt độ", f"{temp}°C", f"Cảm giác {feels_like}°C")
        col2.metric("💧 Độ ẩm", f"{humidity}%")
        col3.metric("🌬️ Gió", f"{wind_speed} m/s")
        col1.metric("🔽 Áp suất", f"{pressure} hPa")
        col2.metric("🌅 Mặt trời mọc", sunrise)
        col3.metric("🌇 Mặt trời lặn", sunset)
        st.info(f"Tình trạng thời tiết: **{desc.capitalize()}**")

        # Lưu vào DB
        save_weather(city, temp, feels_like, humidity, pressure, wind_speed, desc, sunrise, sunset, lat, lon)

        # Biểu đồ nhiệt độ lịch sử
        st.subheader("📊 Biểu đồ nhiệt độ lịch sử")
        rows = get_history(city)
        if rows:
            df = [{"city": r[0], "temperature": r[1], "time": r[2]} for r in rows]
            fig = px.line(df, x="time", y="temperature", title=f"Nhiệt độ tại {city} theo thời gian")
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("❌ Không tìm thấy dữ liệu cho thành phố này.")
