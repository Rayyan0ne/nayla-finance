import streamlit as st
import mysql.connector
import pandas as pd
import json
import requests
from streamlit_lottie import st_lottie

# --- FUNGSI HELPER ---
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["db_host"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        port=st.secrets["db_port"],
        database=st.secrets["db_name"]
    )

def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

# --- LOAD ANIMASI ---
lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")
lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_vwb8596u.json")
lottie_chart = load_lottieurl("https://assets9.lottiefiles.com/packages/lf20_qp1q7mct.json")

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="Nayla Ultra Project", page_icon="💎", layout="wide")

# --- CUSTOM CSS (Neon Dark Luxury) ---
st.markdown("""
    <style>
    .main { background-color: #121212; color: #e0e0e0; }
    
    @keyframes popIn {
        0% { opacity: 0; transform: scale(0.9); }
        100% { opacity: 1; transform: scale(1); }
    }

    .metric-card-dark {
        background: linear-gradient(145deg, #1e1e1e, #161616);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        border: 1px solid #333;
        text-align: center;
        animation: popIn 0.5s ease-out;
    }
    .card-label { color: #aaaaaa !important; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
    .card-value-income { color: #00ff88 !important; font-weight: bold; text-shadow: 0 0 15px rgba(0,255,136,0.3); }
    .card-value-expense { color: #ff4b4b !important; font-weight: bold; text-shadow: 0 0 15px rgba(255,75,75,0.3); }
    .card-value-saldo { color: #00d4ff !important; font-weight: bold; text-shadow: 0 0 15px rgba(0,212,255,0.3); }

    .student-stats-card {
        background-color: #1e1e1e;
        padding: 15px 30px;
        border-radius: 100px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 1px solid #ff4b4b;
        display: inline-block;
        margin-bottom: 25px;
    }
    .student-label { color: #ffffff !important; font-size: 16px; }
    .student-count { color: #ff4b4b !important; font-size: 20px; font-weight: bold; }

    .stButton>button { border-radius: 10px; transition: 0.3s; }
    .stButton>button:hover { background-color: #ff4b4b !important; color: white !important; transform: translateY(-2px); }
    
    /* Input Styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input { background-color: #252525; color: white; border-radius: 10px; border: 1px solid #444; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI LOGIN ---
if not st.session_state['logged_in']:
    _, col_auth, _ = st.columns([1, 1.5, 1])
    with col_auth:
        st.markdown("<h1 style='text-align: center;'>💎 Nayla Project v2</h1>", unsafe_allow_html=True)
        if lottie_wallet: st_lottie(lottie_wallet, height=150)
        
        tab1, tab2 = st.tabs(["🔒 Login", "✍️ Register"])
        with tab1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Masuk Sekarang", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
                if cursor.fetchone():
                    st.session_state['logged_in'] = True
                    st.session_state['user'] = u
                    st.rerun()
                else: st.error("Akses Ditolak!")
                conn.close()
        with tab2:
            new_u = st.text_input("Username Baru", key="reg_u")
            new_p = st.text_input("Password Baru", type="password", key="reg_p")
            if st.button("Buat Akun", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_u, new_p))
                    conn.commit()
                    st.success("Selesai! Silakan Login.")
                except: st.error("User sudah ada!")
                conn.close()

# --- MAIN APP ---
else:
    st.sidebar.markdown(f"<h2 style='text-align: center;'>👑 {st.session_state['user']}</h2>", unsafe_allow_html=True)
    menu = st.sidebar.selectbox("Pilih Dashboard:", ["💰 Money Tracker", "🎓 Student Admin", "📈 Growth Analytics"])
    st.sidebar.divider()
    if st.sidebar.button("🚪 Keluar Sistem", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_db_connection()
    df_fin = pd.read_sql(f"SELECT * FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC", conn)
    df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
    conn.close()
    
    # --- PROTEKSI HALAMAN ---
if not st.session_state['logged_in']:
    _, col_auth, _ = st.columns([1, 1.5, 1])
    with col_auth:
        st.title("🔒 Restricted Access")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk", use_container_width=True):
            # Logika login lu di sini...
            if u == "admin" and p == "admin": # Contoh simpel
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Siapa lu? Jangan iseng ya!")
else:
    # HALAMAN UTAMA HANYA MUNCUL JIKA SUDAH LOGIN
    st.sidebar.title(f"Halo, {st.session_state.get('user', 'Admin')}")
    menu = st.sidebar.selectbox("Navigasi", ["Money Tracker", "Student Admin", "Growth Analytics"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    if menu == "Money Tracker":
        st.subheader("💰 Catatan Keuangan")
        # Copy-paste kode fitur Money Tracker lu di sini

    # --- MENU 1: MONEY TRACKER ---
    if menu == "💰 Money Tracker":
        st.title("💸 Financial Dashboard")
        if not df_fin.empty:
            ti = df_fin[df_fin['type'] == 'Income']['amount'].sum()
            te = df_fin[df_fin['type'] == 'Expense']['amount'].sum()
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-card-dark'><p class='card-label'>Inflow</p><h2 class='card-value-income'>Rp {ti:,.0f}</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-card-dark'><p class='card-label'>Outflow</p><h2 class='card-value-expense'>Rp {te:,.0f}</h2></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-card-dark'><p class='card-label'>Net Balance</p><h2 class='card-value-saldo'>Rp {ti-te:,.0f}</h2></div>", unsafe_allow_html=True)
        
        st.write("")
        with st.expander("➕ Tambah Data Keuangan"):
            cx, cy = st.columns(2)
            tipe = cx.selectbox("Tipe", ["Income", "Expense"])
            amt = cy.number_input("Nominal", min_value=0, step=1000)
            note = st.text_input("Keterangan")
            if st.button("Simpan Transaksi", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", (st.session_state['user'], tipe, amt, note))
                conn.commit()
                conn.close()
                st.rerun()

        st.subheader("📜 Riwayat")
        for index, row in df_fin.iterrows():
            with st.container():
                c_icon, c_txt, c_del = st.columns([1, 4, 1])
                c_icon.write("💰" if row['type'] == 'Income' else "🔻")
                c_txt.write(f"**{row['note']}** - Rp {row['amount']:,.0f}")
                if c_del.button("🗑️", key=f"del_{row['id']}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
                st.divider()

    # --- MENU 2: STUDENT ADMIN ---
    elif menu == "🎓 Student Admin":
        st.title("👩‍🏫 Student Management")
        if not df_stu.empty:
            st.markdown(f"<div class='student-stats-card'><span class='student-label'>Murid Terdaftar: </span><span class='student-count'>{len(df_stu)} Orang</span></div>", unsafe_allow_html=True)
        
        with st.expander("👤 Daftar Murid Baru"):
            nx, ny = st.columns(2)
            s_name = nx.text_input("Nama Murid")
            s_course = ny.selectbox("Kursus", ["Dasar Menjahit VR", "Rancang Busana Digital", "Tekstil & Bahan"])
            if st.button("Daftarkan Murid", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students (student_name, course_name, username, progress) VALUES (%s, %s, %s, 0)", (s_name, s_course, st.session_state['user']))
                conn.commit()
                conn.close()
                st.rerun()

        for index, row in df_stu.iterrows():
            with st.container():
                st.write(f"### {row['student_name']}")
                if st.button("🗑️ Hapus Murid", key=f"dels_{row['id']}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM students WHERE id=%s", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()
                st.divider()

    # --- MENU 3: GROWTH ANALYTICS ---
    elif menu == "📈 Growth Analytics":
        st.title("📈 Insight & Report")
        if not df_fin.empty:
            st.bar_chart(df_fin.set_index('created_at')['amount'])
            st.write(f"Total Aktivitas: **{len(df_fin)} Transaksi**")
            if lottie_chart: st_lottie(lottie_chart, height=200)
        else:
            st.info("Belum ada data untuk dianalisis.")