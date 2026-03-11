import streamlit as st
import mysql.connector
import pandas as pd
import requests
from streamlit_lottie import st_lottie

# --- FUNGSI AMAN UNTUK KONEKSI (FIX PORT & SSL) ---
def get_db_connection():
    try:
        # Menghapus spasi atau tanda kutip sisa di Secrets biar gak error host
        raw_host = st.secrets["db_host"].strip().replace('"', '').replace("'", "")
        
        return mysql.connector.connect(
            host=raw_host,
            user=st.secrets["db_user"].strip(),
            password=st.secrets["db_password"].strip(),
            port=int(st.secrets["db_port"]), # Pastiin port 15167 di secrets
            database=st.secrets["db_name"].strip(),
            ssl_disabled=False # Aiven butuh ini tetap False (SSL Aktif)
        )
    except Exception as e:
        st.error(f"Gagal konek ke Database: {e}")
        return None

def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- LOAD ANIMASI & CONFIG ---
st.set_page_config(page_title="Nayla Ultra Project", page_icon="💎", layout="wide")
lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")
lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_vwb8596u.json")

# --- CUSTOM CSS AWAL LU ---
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
    }
    .card-value-income { color: #00ff88 !important; font-weight: bold; }
    .card-value-expense { color: #ff4b4b !important; font-weight: bold; }
    .card-value-saldo { color: #00d4ff !important; font-weight: bold; }
    .student-card {
        background-color: #1e1e1e; padding: 20px; border-radius: 15px;
        border-left: 5px solid #ff4b4b; margin-bottom: 10px;
    }
    .stButton>button { border-radius: 10px; transition: 0.3s; }
    .stButton>button:hover { background-color: #ff4b4b !important; color: white !important; }
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
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
                    if cursor.fetchone():
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = u
                        conn.close()
                        st.rerun()
                    else: st.error("Akses Ditolak!")
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
                        st.success("Selesai! Silakan Login.")
                    except: st.error("User sudah ada!")
                    finally: conn.close()

# --- MAIN APP ---
else:
    st.sidebar.markdown(f"<h2 style='text-align: center;'>👑 {st.session_state['user']}</h2>", unsafe_allow_html=True)
    menu = st.sidebar.radio("Pilih Dashboard:", ["💰 Money Tracker", "🎓 Student Admin", "📈 Growth Analytics", "🥗 Healthy Kitchen"])
    
    if st.sidebar.button("🚪 Log Out", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    conn = get_db_connection()
    if not conn: st.stop()

    # MENU 1: MONEY TRACKER
    if menu == "💰 Money Tracker":
        st.title("💸 Financial Dashboard")
        df_fin = pd.read_sql(f"SELECT * FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC", conn)
        
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
                cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", (st.session_state['user'], tipe, amt, note))
                conn.commit()
                st.rerun()

        st.subheader("📜 Riwayat")
        for _, row in df_fin.iterrows():
            c_icon, c_txt, c_del = st.columns([1, 4, 1])
            c_icon.write("💰" if row['type'] == 'Income' else "🔻")
            c_txt.write(f"**{row['note']}** - Rp {row['amount']:,.0f}")
            if c_del.button("🗑️", key=f"del_fin_{row['id']}"):
                cursor = conn.cursor(); cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
                conn.commit(); st.rerun()
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
                cursor.execute("INSERT INTO students (student_name, course_name, username, progress) VALUES (%s, %s, %s, 0)", (s_name, s_course, st.session_state['user']))
                conn.commit(); st.rerun()

        df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
        for _, row in df_stu.iterrows():
            st.markdown(f"<div class='student-card'><h3>👤 {row['student_name']}</h3><p>📚 {row['course_name']}</p></div>", unsafe_allow_html=True)
            stages = ["Tahap 1", "Tahap 2", "Tahap 3", "Tahap 4", "Tahap 5"]
            count = 0
            cols = st.columns(5)
            for i, s in enumerate(stages):
                if cols[i].checkbox(f"T{i+1}", value=(int(row['progress']) >= (i+1)*20), key=f"ch_{row['id']}_{i}"): count += 1
            
            new_prog = count * 20
            st.progress(new_prog / 100)
            if new_prog == 100: 
                st.success("🎉 Ahli dalam bidangnya!"); st_lottie(lottie_success, height=100, key=f"l_{row['id']}")
            
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("💾", key=f"s_{row['id']}"):
                cursor = conn.cursor(); cursor.execute("UPDATE students SET progress=%s WHERE id=%s", (new_prog, row['id']))
                conn.commit(); st.rerun()
            if c2.button("🗑️", key=f"d_{row['id']}"):
                cursor = conn.cursor(); cursor.execute("DELETE FROM students WHERE id=%s", (row['id'],))
                conn.commit(); st.rerun()

    # MENU 4: HEALTHY KITCHEN (LU MINTA INI BALIK KAN?)
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