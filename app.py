import streamlit as st
import mysql.connector
import pandas as pd
import requests
from streamlit_lottie import st_lottie

# --- GAYA JAVA: DATABASE MANAGER CLASS ---
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
                host=self.host,
                user=self.user,
                password=self.password,
                port=self.port,
                database=self.database,
                ssl_disabled=False 
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

if 'lottie_wallet' not in st.session_state:
    st.session_state.lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent; }
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

# --- UI LOGIN ---
if not st.session_state['logged_in']:
    _, col_auth, _ = st.columns([1, 1.5, 1])
    with col_auth:
        st.markdown("<h1 style='text-align: center;'>💎 Finance Project v2</h1>", unsafe_allow_html=True)
        if st.session_state.lottie_wallet: 
            st_lottie(st.session_state.lottie_wallet, height=150)
        
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
                    else: 
                        st.error("Username atau Password salah!")
                    conn.close()
        with tab2:
            new_u = st.text_input("Username Baru", key="reg_u")
            new_p = st.text_input("Password Baru", type="password", key="reg_p")
            if st.button("Buat Akun", use_container_width=True):
                if new_u and new_p:
                    conn = db.get_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_u, new_p))
                            conn.commit()
                            st.success("Akun berhasil dibuat! Silakan Login.")
                        except: st.error("Username sudah terdaftar!")
                        finally: conn.close()
                else:
                    st.warning("Isi semua data!")

# --- MAIN APP ---
else:
    st.sidebar.markdown(f"<h2 style='text-align: center;'>👑 {st.session_state['user']}</h2>", unsafe_allow_html=True)
    
    # HANYA SATU MENU
    st.sidebar.info("Dashboard Active: Money Tracker")
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = db.get_connection()
    if not conn: st.stop()

    # --- MONEY TRACKER ONLY ---
    st.title("💸 Financial Dashboard")
    query = "SELECT * FROM transactions WHERE username=%s ORDER BY created_at ASC"
    df_fin = pd.read_sql(query, conn, params=(st.session_state['user'],))
    
    # Hitung Metrik
    ti = df_fin[df_fin['type'] == 'Income']['amount'].sum() if not df_fin.empty else 0
    te = df_fin[df_fin['type'] == 'Expense']['amount'].sum() if not df_fin.empty else 0
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f"<div class='metric-card-dark'><p>Inflow</p><h2 class='card-value-income'>Rp {ti:,.0f}</h2></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='metric-card-dark'><p>Outflow</p><h2 class='card-value-expense'>Rp {te:,.0f}</h2></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='metric-card-dark'><p>Net Balance</p><h2 class='card-value-saldo'>Rp {ti-te:,.0f}</h2></div>", unsafe_allow_html=True)

    # --- KURVA DIAGRAM MONEY ---
    if not df_fin.empty:
        st.subheader("📈 Money Trend")
        # Menyiapkan data untuk chart
        df_fin['created_at'] = pd.to_datetime(df_fin['created_at'])
        chart_data = df_fin.pivot_table(index='created_at', columns='type', values='amount', aggfunc='sum').fillna(0)
        st.line_chart(chart_data)

    with st.expander("➕ Tambah Data Keuangan"):
        tipe = st.radio("Tipe Transaksi:", ["Income", "Expense"], horizontal=True)
        amt = st.number_input("Nominal (Rp)", min_value=0, step=1000)
        note = st.text_input("Keterangan")
        if st.button("Simpan Transaksi"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", 
                         (st.session_state['user'], tipe, amt, note))
            conn.commit()
            st.rerun()

    st.subheader("📜 Riwayat")
    if df_fin.empty:
        st.info("Belum ada transaksi.")
    else:
        # Sort desc untuk history (yang terbaru di atas)
        for _, row in df_fin.iloc[::-1].iterrows():
            c_icon, c_txt, c_del = st.columns([0.5, 4, 1])
            c_icon.write("💰" if row['type'] == 'Income' else "🔻")
            c_txt.write(f"**{row['note']}** - Rp {row['amount']:,.0f} ({row['created_at']})")
            if c_del.button("🗑️", key=f"del_fin_{row['id']}"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
                conn.commit()
                st.rerun()
            st.divider()

    conn.close()