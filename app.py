import streamlit as st
import mysql.connector
import pandas as pd
import requests
from streamlit_lottie import st_lottie

# --- FUNGSI AMAN UNTUK KONEKSI ---
def get_db_connection():
    try:
        # Menghapus spasi atau tanda kutip sisa di Secrets
        raw_host = st.secrets["db_host"].strip().replace('"', '').replace("'", "")
        
        return mysql.connector.connect(
            host=raw_host,
            user=st.secrets["db_user"].strip(),
            password=st.secrets["db_password"].strip(),
            port=int(st.secrets["db_port"]),
            database=st.secrets["db_name"].strip(),
            ssl_disabled=False # Aiven butuh SSL aktif
        )
    except Exception as e:
        # Biar kita tau error aslinya apa kalau gagal
        st.error(f"Gagal konek ke Database: {e}")
        return None

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- SETUP HALAMAN ---
st.set_page_config(page_title="Nayla Ultra Project", page_icon="💎", layout="wide")
lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>💎 Nayla Project v2</h1>", unsafe_allow_html=True)
    if lottie_wallet: st_lottie(lottie_wallet, height=150)
    
    tab1, tab2 = st.tabs(["🔒 Login", "✍️ Register"])
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk Sekarang", use_container_width=True):
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
                if cursor.fetchone():
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
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_u, new_p))
                    conn.commit()
                    st.success("Berhasil! Silakan Login.")
                except: st.error("Username sudah dipakai!")
                finally: conn.close()

# --- APLIKASI UTAMA ---
else:
    st.sidebar.title(f"👑 {st.session_state['user']}")
    menu = st.sidebar.radio("Navigasi:", ["💰 Money Tracker", "🎓 Student Admin", "📈 Growth Analytics"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    # MENU 1: MONEY TRACKER
    if menu == "💰 Money Tracker":
        st.title("💸 Financial Dashboard")
        conn = get_db_connection()
        if conn:
            try:
                df = pd.read_sql(f"SELECT * FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC", conn)
                # Tampilkan metrik (Saldo, Inflow, Outflow)
                ti = df[df['type'] == 'Income']['amount'].sum()
                te = df[df['type'] == 'Expense']['amount'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Inflow", f"Rp {ti:,.0f}")
                c2.metric("Outflow", f"Rp {te:,.0f}")
                c3.metric("Balance", f"Rp {ti-te:,.0f}")
                
                with st.expander("➕ Tambah Transaksi"):
                    t_type = st.radio("Tipe:", ["Income", "Expense"], horizontal=True)
                    t_amt = st.number_input("Nominal", min_value=0)
                    t_note = st.text_input("Keterangan")
                    if st.button("Simpan"):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", 
                                     (st.session_state['user'], t_type, t_amt, t_note))
                        conn.commit()
                        st.rerun()
                st.dataframe(df, use_container_width=True)
            finally: conn.close()

    # MENU 2: STUDENT ADMIN
    elif menu == "🎓 Student Admin":
        st.title("👩‍🏫 Student Management")
        conn = get_db_connection()
        if conn:
            try:
                df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
                for _, row in df_stu.iterrows():
                    st.subheader(f"👤 {row['student_name']}")
                    st.info(f"Kursus: {row['course_name']}")
                    # Logika Checklist 5 Tahap
                    stages = ["Tahap 1", "Tahap 2", "Tahap 3", "Tahap 4", "Tahap 5"]
                    done = 0
                    for i, s in enumerate(stages):
                        if st.checkbox(f"{s}", value=(int(row['progress']) >= (i+1)*20), key=f"s_{row['id']}_{i}"):
                            done += 1
                    new_prog = done * 20
                    st.progress(new_prog / 100)
                    if st.button("Simpan Progres", key=f"save_{row['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE students SET progress=%s WHERE id=%s", (new_prog, row['id']))
                        conn.commit()
                        st.rerun()
            finally: conn.close()

    # MENU 3: ANALYTICS
    elif menu == "📈 Growth Analytics":
        st.title("📈 Insight")
        conn = get_db_connection()
        if conn:
            try:
                df_fin = pd.read_sql(f"SELECT * FROM transactions WHERE username='{st.session_state['user']}'", conn)
                if not df_fin.empty:
                    st.line_chart(df_fin.set_index('created_at')['amount'])
            finally: conn.close()