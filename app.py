import streamlit as st
import mysql.connector
import pandas as pd
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
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- LOAD ANIMASI ---
lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")
lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_vwb8596u.json")

# --- CONFIG HALAMAN ---
st.set_page_config(page_title="Nayla Ultra Project", page_icon="💎", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent; }
    .main { background-color: #121212; color: #e0e0e0; }
    .metric-card-dark {
        background: linear-gradient(145deg, #1e1e1e, #161616);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        border: 1px solid #333;
        text-align: center;
    }
    .card-value-income { color: #00ff88 !important; font-weight: bold; }
    .card-value-expense { color: #ff4b4b !important; font-weight: bold; }
    .card-value-saldo { color: #00d4ff !important; font-weight: bold; }
    .student-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
    }
    .stButton>button { border-radius: 10px; transition: 0.3s; }
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
                user_data = cursor.fetchone()
                if user_data:
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

# --- MAIN APP (PENTING: SEMUA KODE DI SINI HARUS MASUK BLOK ELSE) ---
else:
    st.sidebar.markdown(f"<h2 style='text-align: center;'>👑 {st.session_state['user']}</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Pilih Dashboard:", ["💰 Money Tracker", "🎓 Student Admin", "📈 Growth Analytics"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    # Buka koneksi di awal blok aplikasi utama
    conn = get_db_connection()

    if menu == "💰 Money Tracker":
        st.title("💸 Financial Dashboard")
        df_fin = pd.read_sql(f"SELECT * FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC", conn)
        
        if not df_fin.empty:
            ti = df_fin[df_fin['type'] == 'Income']['amount'].sum()
            te = df_fin[df_fin['type'] == 'Expense']['amount'].sum()
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-card-dark'><p>Inflow</p><h2 class='card-value-income'>Rp {ti:,.0f}</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-card-dark'><p>Outflow</p><h2 class='card-value-expense'>Rp {te:,.0f}</h2></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-card-dark'><p>Net Balance</p><h2 class='card-value-saldo'>Rp {ti-te:,.0f}</h2></div>", unsafe_allow_html=True)
        
        with st.expander("➕ Tambah Data Keuangan"):
            cx, cy = st.columns(2)
            tipe = cx.radio("Tipe Transaksi:", ["Income", "Expense"], horizontal=True) # Pakai radio biar gak bisa dihapus
            amt = cy.number_input("Nominal (Rp)", min_value=0, step=1000)
            note = st.text_input("Keterangan")
            if st.button("Simpan Transaksi"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", (st.session_state['user'], tipe, amt, note))
                conn.commit()
                st.rerun()

    elif menu == "🎓 Student Admin":
        st.title("👩‍🏫 Student Management")
        with st.expander("➕ Tambah Murid Baru"):
            n, c = st.columns(2)
            s_name = n.text_input("Nama Murid")
            s_course = c.radio("Pilih Kursus:", ["Dasar Menjahit VR", "Rancang Busana Digital"]) #
            if st.button("Simpan Murid"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students (student_name, course_name, username, progress) VALUES (%s, %s, %s, 0)", (s_name, s_course, st.session_state['user']))
                conn.commit()
                st.rerun()

        df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
        for _, row in df_stu.iterrows():
            with st.container():
                st.markdown(f"<div class='student-card'><h3>👤 {row['student_name']}</h3><p>📚 {row['course_name']}</p></div>", unsafe_allow_html=True)
                stages = ["Tahap 1", "Tahap 2", "Tahap 3", "Tahap 4", "Tahap 5"] # Daftar tahapan lengkap lu ada di sini
                count = 0
                for i, s in enumerate(stages):
                    if st.checkbox(f"{s}", value=(int(row['progress']) >= (i+1)*20), key=f"ch_{row['id']}_{i}"):
                        count += 1
                new_p = count * 20
                st.progress(new_p / 100)
                if st.button("💾 Simpan", key=f"btn_{row['id']}"):
                    cursor = conn.cursor()
                    cursor.execute("UPDATE students SET progress=%s WHERE id=%s", (new_p, row['id']))
                    conn.commit()
                    st.rerun()

    elif menu == "📈 Growth Analytics":
        st.title("📈 Insight & Report")
        df_fin = pd.read_sql(f"SELECT * FROM transactions WHERE username='{st.session_state['user']}'", conn)
        if not df_fin.empty:
            st.bar_chart(df_fin.set_index('created_at')['amount'])

    # TUTUP KONEKSI DI SINI (PENTING: Harus sejajar dengan kode aplikasi utama)
    conn.close()