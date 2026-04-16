import streamlit as st
import mysql.connector
import pandas as pd
import requests
from streamlit_lottie import st_lottie

# --- DATABASE MANAGER ---
class DatabaseManager:
    def __init__(self):
        self.host = st.secrets["db_host"].strip().replace('"', '').replace("'", "")
        self.user = st.secrets["db_user"].strip()
        self.password = st.secrets["db_password"].strip()
        self.port = int(st.secrets["db_port"])
        self.database = st.secrets["db_name"].strip()

    def get_connection(self):
        try:
            conn = mysql.connector.connect(
                host=self.host, user=self.user, password=self.password,
                port=self.port, database=self.database, ssl_disabled=False 
            )
            return conn
        except Exception as e:
            st.error(f"Gagal konek ke Database: {e}")
            return None

db = DatabaseManager()

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- CONFIG ---
st.set_page_config(page_title="Finance Project", page_icon="💎", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #121212; color: #e0e0e0; }
    .metric-card-dark {
        background: linear-gradient(145deg, #1e1e1e, #161616);
        padding: 25px; border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #333; text-align: center;
        margin-bottom: 20px;
    }
    .card-value-income { color: #00ff88 !important; }
    .card-value-expense { color: #ff4b4b !important; }
    .card-value-saldo { color: #00d4ff !important; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI LOGIN & REGISTER (Sama seperti sebelumnya) ---
if not st.session_state['logged_in']:
    _, col_auth, _ = st.columns([1, 1.5, 1])
    with col_auth:
        st.markdown("<h1 style='text-align: center;'>💎 Finance Project v2</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔒 Login", "✍️ Register"])
        with tab1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Masuk Sekarang", use_container_width=True):
                conn = db.get_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
                    user = cursor.fetchone()
                    if user:
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = u
                        conn.close()
                        st.rerun()
                    else: st.error("Username atau Password salah!")
                    conn.close()
        with tab2:
            new_u = st.text_input("Username Baru", key="reg_u")
            new_p = st.text_input("Password Baru", type="password", key="reg_p")
            if st.button("Buat Akun", use_container_width=True):
                conn = db.get_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_u, new_p))
                        conn.commit()
                        st.success("Akun berhasil dibuat!")
                    except: st.error("Gagal buat akun!")
                    finally: conn.close()

# --- MAIN APP ---
else:
    st.sidebar.markdown(f"<h2 style='text-align: center;'>👑 {st.session_state['user']}</h2>", unsafe_allow_html=True)
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = db.get_connection()
    if not conn: st.stop()

    # Get Data
    df_fin = pd.read_sql("SELECT * FROM transactions WHERE username=%s ORDER BY created_at ASC", conn, params=(st.session_state['user'],))
    
    st.title("💸 Financial Dashboard")

    if not df_fin.empty:
        df_fin['created_at'] = pd.to_datetime(df_fin['created_at'])
        df_fin['tanggal'] = df_fin['created_at'].dt.date
        
        # Metrik
        ti = df_fin[df_fin['type'] == 'Income']['amount'].sum()
        te = df_fin[df_fin['type'] == 'Expense']['amount'].sum()
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card-dark'><p>Inflow</p><h2 class='card-value-income'>Rp {ti:,.0f}</h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card-dark'><p>Outflow</p><h2 class='card-value-expense'>Rp {te:,.0f}</h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card-dark'><p>Net Balance</p><h2 class='card-value-saldo'>Rp {ti-te:,.0f}</h2></div>", unsafe_allow_html=True)

        # --- DIAGRAM BATANG DENGAN WARNA CUSTOM ---
        st.subheader("📊 Analisis Bulanan (Hijau = Income, Merah = Expense)")
        
        # Group data
        chart_data = df_fin.groupby(['tanggal', 'type'])['amount'].sum().reset_index()
        
        # Kita gunakan color parameter untuk membedakan warna
        # Mapping: Expense -> Merah (#FF4B4B), Income -> Hijau (#00FF88)
        st.bar_chart(
            chart_data, 
            x="tanggal", 
            y="amount", 
            color="type", 
            color_config={
                "Income": "#00FF88", 
                "Expense": "#FF4B4B"
            }
        )

    # Form Input
    with st.expander("➕ Tambah Data Keuangan"):
        tipe = st.radio("Tipe:", ["Income", "Expense"], horizontal=True)
        amt = st.number_input("Nominal", min_value=0, step=1000)
        note = st.text_input("Keterangan")
        tgl = st.date_input("Tanggal")
        if st.button("Simpan"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (username, type, amount, note, created_at) VALUES (%s, %s, %s, %s, %s)", 
                         (st.session_state['user'], tipe, amt, note, tgl))
            conn.commit()
            st.rerun()

    # Riwayat
    st.subheader("📜 Riwayat Transaksi")
    for _, row in df_fin.iloc[::-1].iterrows():
        col_icon, col_txt, col_del = st.columns([0.5, 4, 1])
        col_icon.write("💰" if row['type'] == 'Income' else "🔻")
        col_txt.markdown(f"**{row['note']}** (Rp {row['amount']:,.0f})")
        col_txt.caption(f"Tanggal: {row['created_at'].strftime('%d %b %Y')}")
        if col_del.button("🗑️", key=f"del_{row['id']}"):
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
            conn.commit()
            st.rerun()
        st.divider()

    conn.close()