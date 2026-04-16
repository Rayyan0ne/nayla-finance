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
        
        conn = mysql.connector.connect(
            host=raw_host,
            user=st.secrets["db_user"].strip(),
            password=st.secrets["db_password"].strip(),
            port=int(st.secrets["db_port"]),
            database=st.secrets["db_name"].strip(),
            ssl_disabled=False 
        )
        return conn
    except Exception as e:
        st.error(f"Gagal konek ke Database: {e}")
        return None

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- CONFIG ---
st.set_page_config(page_title="Finance Project", page_icon="💎", layout="wide")

# Cache animasi agar tidak reload terus
if 'lottie_wallet' not in st.session_state:
    st.session_state.lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")
if 'lottie_success' not in st.session_state:
    st.session_state.lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_vwb8596u.json")

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
    .student-card {
        background-color: #1e1e1e; padding: 20px; border-radius: 15px;
        border-left: 5px solid #ff4b4b; margin-bottom: 10px;
    }
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
                conn = get_db_connection()
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
                    conn = get_db_connection()
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
    menu = st.sidebar.radio("Pilih Dashboard:", ["💰 Money Tracker", "🎓 Student Admin", "🥗 Healthy Kitchen"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_db_connection()
    if not conn: st.stop()

    # MENU 1: MONEY TRACKER
    if menu == "💰 Money Tracker":
        st.title("💸 Financial Dashboard")
        
        # Menggunakan query yang aman
        query = "SELECT * FROM transactions WHERE username=%s ORDER BY created_at DESC"
        df_fin = pd.read_sql(query, conn, params=(st.session_state['user'],))
        
        ti = df_fin[df_fin['type'] == 'Income']['amount'].sum() if not df_fin.empty else 0
        te = df_fin[df_fin['type'] == 'Expense']['amount'].sum() if not df_fin.empty else 0
        
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card-dark'><p>Inflow</p><h2 class='card-value-income'>Rp {ti:,.0f}</h2></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card-dark'><p>Outflow</p><h2 class='card-value-expense'>Rp {te:,.0f}</h2></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='metric-card-dark'><p>Net Balance</p><h2 class='card-value-saldo'>Rp {ti-te:,.0f}</h2></div>", unsafe_allow_html=True)
        
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
            for _, row in df_fin.iterrows():
                c_icon, c_txt, c_del = st.columns([0.5, 4, 1])
                c_icon.write("💰" if row['type'] == 'Income' else "🔻")
                c_txt.write(f"**{row['note']}** - Rp {row['amount']:,.0f}")
                if c_del.button("🗑️", key=f"del_fin_{row['id']}"):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
                    conn.commit()
                    st.rerun()
                st.divider()

    # MENU 2: STUDENT ADMIN
    elif menu == "🎓 Student Admin":
        st.title("👩‍🏫 Student Management")
        with st.expander("➕ Tambah Murid Baru"):
            n, c = st.columns(2)
            s_name = n.text_input("Nama Murid")
            s_course = c.radio("Pilih Kursus:", ["Dasar Menjahit VR", "Rancang Busana Digital"])
            if st.button("Simpan Murid"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students (student_name, course_name, username, progress) VALUES (%s, %s, %s, 0)", 
                             (s_name, s_course, st.session_state['user']))
                conn.commit()
                st.rerun()

        df_stu = pd.read_sql("SELECT * FROM students WHERE username=%s", conn, params=(st.session_state['user'],))
        for _, row in df_stu.iterrows():
            st.markdown(f"<div class='student-card'><h3>👤 {row['student_name']}</h3><p>📚 {row['course_name']}</p></div>", unsafe_allow_html=True)
            
            # Logika Progress
            stages = ["Tahap 1", "Tahap 2", "Tahap 3", "Tahap 4", "Tahap 5"]
            cols = st.columns(5)
            checked_count = 0
            for i in range(5):
                # Menentukan status awal checkbox berdasarkan progress di DB
                is_checked = cols[i].checkbox(f"T{i+1}", value=(int(row['progress']) >= (i+1)*20), key=f"ch_{row['id']}_{i}")
                if is_checked:
                    checked_count += 1
            
            new_prog = checked_count * 20
            st.progress(new_prog / 100)
            
            if new_prog == 100: 
                st.success("🎉 Ahli dalam bidangnya!")
                if st.session_state.lottie_success:
                    st_lottie(st.session_state.lottie_success, height=100, key=f"l_{row['id']}")
            
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("💾", key=f"s_{row['id']}", help="Simpan Progress"):
                cursor = conn.cursor()
                cursor.execute("UPDATE students SET progress=%s WHERE id=%s", (new_prog, row['id']))
                conn.commit()
                st.toast("Progress disimpan!")
            if c2.button("🗑️", key=f"d_{row['id']}", help="Hapus Murid"):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM students WHERE id=%s", (row['id'],))
                conn.commit()
                st.rerun()

    # MENU 3: HEALTHY KITCHEN
    elif menu == "🥗 Healthy Kitchen":
        st.title("🥗 Healthy Recipe Guide")
        recipes = {
            "Es Teh Lemon Madu": {"ing": ["Teh Celup", "Lemon", "Madu"], "steps": ["Seduh teh", "Campur madu & lemon"], "msg": "Segar! 🍋"},
            "Orak Arik Telur": {"ing": ["2 Telur", "Wortel", "Kol"], "steps": ["Tumis sayur", "Orak-arik telur"], "msg": "Protein! 🍳"}
        }
        choice = st.selectbox("Pilih Resep:", list(recipes.keys()))
        res = recipes[choice]
        st.subheader("🛒 Bahan")
        for i in res["ing"]: st.write(f"- {i}")
        st.subheader("👨‍🍳 Langkah")
        for s in res["steps"]: st.checkbox(s, key=f"step_{choice}_{s}")

    conn.close()