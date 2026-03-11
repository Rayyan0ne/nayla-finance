import streamlit as st
import mysql.connector
import pandas as pd
import json
import requests
from streamlit_lottie import st_lottie

# --- FUNGSI HELPER (Biar Gak Ngerubah Kodingan Lu) ---
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

# --- LOAD ANIMASI LOTTIE ---
lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")
lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_vwb8596u.json")

# --- CONFIG HALAMAN (Aesthetic Dark) ---
st.set_page_config(page_title="Nayla Finance & Project", page_icon="📊", layout="wide")

# --- CUSTOM CSS (Neon Dark Luxury Update) ---
st.markdown("""
    <style>
    /* 1. Background Global & Reset */
    .main { background-color: #121212; color: #e0e0e0; }
    
    /* 2. Animasi Muncul (Pop In) */
    @keyframes popIn {
        0% { opacity: 0; transform: scale(0.9); }
        70% { transform: scale(1.02); }
        100% { opacity: 1; transform: scale(1); }
    }

    /* 3. Styling Kotak Saldo (GAMBAR 1) - BOLD & DARK */
    .metric-card-dark {
        background-color: #1e1e1e; /* Abu-abu gelap */
        padding: 25px;
        border-radius: 20px;
        # Bikin seakan-akan muncul (Bold Shadow)
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); 
        border: 1px solid #333; /* Border tipis biar kelihatan bentuknya */
        text-align: center;
        transition: 0.3s ease-in-out;
        animation: popIn 0.5s ease-out; /* Pake animasi muncul */
    }
    .metric-card-dark:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.7);
        border-color: #ff4b4b; /* Highlight merah pas di-hover */
    }
    /* Styling teks di dalem kotak agar tidak nyaru */
    .card-label { color: #aaaaaa !important; font-size: 16px; margin-bottom: 5px; }
    .card-value-income { color: #2ecc71 !important; font-weight: bold; text-shadow: 0 0 10px rgba(46,204,113,0.5); }
    .card-value-expense { color: #e74c3c !important; font-weight: bold; text-shadow: 0 0 10px rgba(231,76,60,0.5); }
    .card-value-saldo { color: #3498db !important; font-weight: bold; text-shadow: 0 0 10px rgba(52,152,219,0.5); }

    /* 4. Styling Kotak Murid (GAMBAR 2) - FIXING INVISIBLE TEXT */
    .student-stats-card {
        background-color: #1e1e1e; /* Gelap juga */
        padding: 20px;
        border-radius: 50px; /* Lonjong kayak di SS lu */
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        border: 1px solid #333;
        text-align: center;
        margin-bottom: 20px;
        animation: popIn 0.5s ease-out;
    }
    # Teks label (yang tadi ilang) kita bikin putih terang
    .student-label { color: #ffffff !important; font-size: 18px; font-weight: 500; }
    # Angkanya kita bikin merah neon biar kontras
    .student-count { color: #ff4b4b !important; font-size: 24px; font-weight: bold; text-shadow: 0 0 10px rgba(255,75,75,0.7); }

    /* 5. Styling Elemen Streamlit Lainnya */
    .stButton>button { border-radius: 12px; font-weight: 600; }
    .stTextInput>div>div>input { background-color: #252525; color: white; border-radius: 10px; border: 1px solid #444; }
    .stSelectbox>div>div>div { background-color: #252525; color: white; border-radius: 10px; border: 1px solid #444; }
    h1, h2, h3 { color: #ffffff; text-shadow: 0 0 5px rgba(255,255,255,0.2); }
    
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI AUTH (LOGIN/REGISTER) ---
if not st.session_state['logged_in']:
    # Tengahin Box Login
    _, col_auth, _ = st.columns([1, 1.5, 1])
    with col_auth:
        st.markdown("<h1 style='text-align: center;'>📊 Project Nayla</h1>", unsafe_allow_html=True)
        # Tampilkan Animasi Dompet Lottie
        if lottie_wallet:
            st_lottie(lottie_wallet, height=150, key="login_lottie")
            
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar Akun"])
        with tab1:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            if st.button("Masuk", use_container_width=True, key="login_btn"):
                # Animasi Loading Sederhana
                with st.spinner("Mengecek Kredensial..."):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
                    if cursor.fetchone():
                        st.session_state['logged_in'] = True
                        st.session_state['user'] = u
                        st.rerun()
                    else: st.error("Salah password/user!")
                    conn.close()
        with tab2:
            new_u = st.text_input("Username Baru", key="reg_u")
            new_p = st.text_input("Password Baru", type="password", key="reg_p")
            if st.button("Buat Akun", use_container_width=True, key="reg_btn"):
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_u, new_p))
                    conn.commit()
                    st.success("Selesai! Silakan Login.")
                except: st.error("User sudah ada!")
                conn.close()

# --- DASHBOARD UTAMA (SETELAH LOGIN) ---
else:
    # Sidebar Modern
    st.sidebar.markdown(f"<h3 style='text-align: center;'>👑 Welcome, <br><span style='color:#ff4b4b;'>{st.session_state['user']}</span></h3>", unsafe_allow_html=True)
    st.sidebar.write("")
    menu = st.sidebar.radio("Navigasi Utama:", ["💰 Personal Finance", "🎓 Study Fashion Admin"])
    
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True, key="logout_btn"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- MENU 1: PERSONAL FINANCE ---
    if menu == "💰 Personal Finance":
        st.title("💸 Catatan Keuangan 💸")
        
        conn = get_db_connection()
        query = f"SELECT id, type, amount, note, created_at FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC"
        df = pd.read_sql(query, conn)
        conn.close()

        # Statistik Header (Pake CSS Card Dark & Neon Text)
        if not df.empty:
            ti = df[df['type'] == 'Income']['amount'].sum()
            te = df[df['type'] == 'Expense']['amount'].sum()
            saldo = ti - te
            
            c1, c2, c3 = st.columns(3)
            # Pake class CSS baru (metric-card-dark) dan class warna neon (card-value-...)
            with c1:
                st.markdown(f"""<div class='metric-card-dark'>
                                <p class='card-label'>Pemasukan</p>
                                <h2 class='card-value-income'>Rp {ti:,.0f}</h2>
                            </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class='metric-card-dark'>
                                <p class='card-label'>Pengeluaran</p>
                                <h2 class='card-value-expense'>Rp {te:,.0f}</h2>
                            </div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class='metric-card-dark'>
                                <p class='card-label'>Sisa Saldo</p>
                                <h2 class='card-value-saldo'>Rp {saldo:,.0f}</h2>
                            </div>""", unsafe_allow_html=True)
            st.write("")
            st.divider()
        
        with st.expander("➕ Tambah Catatan Keuangan Baru"):
            c1, c2 = st.columns(2)
            tipe = c1.selectbox("Tipe Transaksi", ["Income", "Expense"])
            amt = c2.number_input("Nominal (Rp)", min_value=0, step=1000)
            note = st.text_input("Keterangan (Contoh: Jajan Boba)")
            if st.button("Simpan Data Keuangan", use_container_width=True, key="save_fin_btn"):
                with st.spinner("Menyimpan..."):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", (st.session_state['user'], tipe, amt, note))
                    conn.commit()
                    st.success("Data berhasil disimpan!")
                    st.rerun()

        st.subheader("📜 Riwayat & Manajemen Data")
        if not df.empty:
            for index, row in df.iterrows():
                with st.container():
                    col_icon, col_data, col_del = st.columns([0.6, 5, 1.2])
                    
                    icon = "💹" if row['type'] == 'Income' else "🔻"
                    col_icon.markdown(f"<h2 style='text-align:center; margin-top:10px;'>{icon}</h2>", unsafe_allow_html=True)
                    
                    with col_data:
                        # Styling teks di riwayat biar kelihatan di dark mode
                        st.markdown(f"<p style='margin-bottom:0; color:#fff;'><b>{row['note']}</b></p>", unsafe_allow_html=True)
                        amt_color = "#2ecc71" if row['type'] == 'Income' else "#e74c3c"
                        st.markdown(f"<h4 style='margin-top:0; color:{amt_color};'>Rp {row['amount']:,.0f}</h4>", unsafe_allow_html=True)
                        st.caption(f"📅 {row['created_at']}")
                    
                    with col_del:
                        st.write("") 
                        if st.button("🗑️ Hapus", key=f"del_fin_{row['id']}", use_container_width=True):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
                            conn.commit()
                            st.rerun()
                    st.divider()
        else:
            st.info("Belum ada riwayat transaksi. Yuk mulai catat!")

    # --- MENU 2: STUDY FASHION ADMIN ---
    elif menu == "🎓 Study Fashion Admin":
        st.title("🛠️ Study Fashion Management")
        st.info("Otomatisasi: Checklist modul akan langsung meng-update progress bar murid.")

        conn = get_db_connection()
        df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
        conn.close()

        # Statistik Murid (FIX GAMBAR 2 - Pake CSS Card Gelap + Teks Putih)
        if not df_stu.empty:
            # Pake class CSS baru (student-stats-card) dan warna teks baru (student-label, student-count)
            st.markdown(f"""<div class='student-stats-card'>
                                <span class='student-label'>Total Murid Aktif: </span>
                                <span class='student-count'>{len(df_stu)}</span>
                            </div>""", unsafe_allow_html=True)
            st.write("")

        with st.expander("👤 Daftarkan Murid Baru (VR Class)"):
            nc1, nc2 = st.columns(2)
            s_name = nc1.text_input("Nama Lengkap Murid")
            s_course = nc2.selectbox("Pilih Kursus VR", ["Dasar Menjahit VR", "Rancang Busana Digital", "Tekstil & Bahan"])
            if st.button("Proses Pendaftaran", use_container_width=True, key="add_stu_btn"):
                with st.spinner("Mendaftarkan..."):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO students (student_name, course_name, username, progress) VALUES (%s, %s, %s, 0)", (s_name, s_course, st.session_state['user']))
                    conn.commit()
                    st.success(f"{s_name} berhasil terdaftar!")
                    st.rerun()

        st.subheader("📊 Progres Kursus Mahasiswa")
        if not df_stu.empty:
            for index, row in df_stu.iterrows():
                # Bikin container murid agak gelap juga biar kontras
                with st.container():
                    st.markdown(f"### 👤 {row['student_name']}")
                    st.markdown(f"<p style='color:#aaa; margin-top:-10px;'>Kursus: <i>{row['course_name']}</i></p>", unsafe_allow_html=True)
                    
                    c_check, c_prog, c_del_stu = st.columns([2, 3, 1.2])
                    
                    with c_check:
                        st.write("Ceklis Modul Selesai:")
                        cc1, cc2 = st.columns(2)
                        m1 = cc1.checkbox("Intro", key=f"m1_{row['id']}")
                        m2 = cc1.checkbox("Pola", key=f"m2_{row['id']}")
                        m3 = cc2.checkbox("Jahit", key=f"m3_{row['id']}")
                        m4 = cc2.checkbox("Final", key=f"m4_{row['id']}")
                    
                    with c_prog:
                        current_prog = sum([m1, m2, m3, m4]) * 25
                        st.write(f"Status Belajar: **{current_prog}%**")
                        st.progress(current_prog / 100)
                        
                        if current_prog == 100:
                            col_confetti, col_text = st.columns([1, 3])
                            with col_confetti:
                                if lottie_success:
                                    st_lottie(lottie_success, height=50, key=f"success_{row['id']}")
                            with col_text:
                                st.success("🎉 Murid Lulus!")

                    with c_del_stu:
                        st.write("") 
                        st.write("") 
                        if st.button("🗑️ Hapus Murid", key=f"del_stu_{row['id']}", use_container_width=True):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM students WHERE id=%s", (row['id'],))
                            conn.commit()
                            st.rerun()
                    st.divider()
        else:
            st.info("Belum ada murid. Yuk tambah satu!")