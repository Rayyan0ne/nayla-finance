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
# Icon Dompet Goyang buat Login
lottie_wallet = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_yM949E.json")
# Icon Sukses buat Progres 100%
lottie_success = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_vwb8596u.json")

# --- CONFIG HALAMAN (Biar Aesthetic) ---
st.set_page_config(page_title="Nayla Finance & Project", page_icon="📊", layout="wide")

# --- CUSTOM CSS (Rahasia Animasi & Desain Premium) ---
st.markdown("""
    <style>
    /* 1. Animasi Fade-In Global */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    .main .block-container {
        animation: fadeIn 0.5s ease-in-out;
    }

    /* 2. Styling Card & Hover Effect */
    .metric-card {
        background-color: white;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        border: 1px solid #f0f0f0;
        text-align: center;
        transition: 0.3s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        border-color: #ff4b4b;
    }

    /* 3. Styling Tombol biar "Kenyal" */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        transition: 0.2s ease;
    }
    .stButton>button:hover {
        transform: scale(1.03);
    }
    /* Khusus tombol Hapus jadi merah pas di-hover */
    .stButton>button[key^="del_"]:hover {
        background-color: #ffcccc !important;
        color: #ff4b4b !important;
    }

    /* 4. Styling Teks & Input */
    h1, h2, h3 { color: #333; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stTextInput>div>div>input { border-radius: 10px; }
    
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI AUTH (LOGIN/REGISTER) ---
if not st.session_state['logged_in']:
    # Tengahin Box Login
    _, col_auth, _ = st.columns([1, 1.5, 1])
    with col_auth:
        st.markdown("<h1 style='text-align: center;'> Project Nayla</h1>", unsafe_allow_html=True)
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
        st.title("💸 Catatan Keuangan Nayla")
        
        conn = get_db_connection()
        query = f"SELECT id, type, amount, note, created_at FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC"
        df = pd.read_sql(query, conn)
        conn.close()

        # Statistik Header (Pake CSS Card & Animasi Hover)
        if not df.empty:
            ti = df[df['type'] == 'Income']['amount'].sum()
            te = df[df['type'] == 'Expense']['amount'].sum()
            saldo = ti - te
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='metric-card'><p style='color:#888; margin-bottom:0;'>Pemasukan</p><h2 style='color:#2ecc71; margin-top:0;'>Rp {ti:,.0f}</h2></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-card'><p style='color:#888; margin-bottom:0;'>Pengeluaran</p><h2 style='color:#e74c3c; margin-top:0;'>Rp {te:,.0f}</h2></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='metric-card'><p style='color:#888; margin-bottom:0;'>Sisa Saldo</p><h2 style='color:#3498db; margin-top:0;'>Rp {saldo:,.0f}</h2></div>", unsafe_allow_html=True)
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
                # Bikin Container Transaksi biar Rapi
                with st.container():
                    col_icon, col_data, col_del = st.columns([0.6, 5, 1.2])
                    
                    # Icon Visual
                    icon = "💹" if row['type'] == 'Income' else "🔻"
                    col_icon.markdown(f"<h2 style='text-align:center; margin-top:10px;'>{icon}</h2>", unsafe_allow_html=True)
                    
                    # Data Teks
                    with col_data:
                        st.markdown(f"<p style='margin-bottom:0;'><b>{row['note']}</b></p>", unsafe_allow_html=True)
                        st.markdown(f"<h4 style='margin-top:0;'>Rp {row['amount']:,.0f}</h4>", unsafe_allow_html=True)
                        st.caption(f"📅 {row['created_at']}")
                    
                    # Tombol Hapus (Hover jadi Merah lewat CSS)
                    with col_del:
                        st.write("") # Spasi
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

        # Statistik Murid (Pake CSS Card)
        if not df_stu.empty:
            st.markdown(f"<div class='metric-card' style='padding:15px;'><h4>Total Murid Aktif: <span style='color:#ff4b4b;'>{len(df_stu)}</span></h4></div>", unsafe_allow_html=True)
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
                # Container untuk tiap murid
                with st.container():
                    st.markdown(f"### 👤 {row['student_name']}")
                    st.markdown(f"<p style='color:#888; margin-top:-10px;'>Kursus: <i>{row['course_name']}</i></p>", unsafe_allow_html=True)
                    
                    c_check, c_prog, c_del_stu = st.columns([2, 3, 1.2])
                    
                    with c_check:
                        st.write("Ceklis Modul Selesai:")
                        # Pake Columns di dalem Checklist biar Rapi
                        cc1, cc2 = st.columns(2)
                        m1 = cc1.checkbox("Intro", key=f"m1_{row['id']}")
                        m2 = cc1.checkbox("Pola", key=f"m2_{row['id']}")
                        m3 = cc2.checkbox("Jahit", key=f"m3_{row['id']}")
                        m4 = cc2.checkbox("Final", key=f"m4_{row['id']}")
                    
                    with c_prog:
                        # Logika Checklist Otomatis (Masih Pake Logika Lu)
                        current_prog = sum([m1, m2, m3, m4]) * 25
                        st.write(f"Status Belajar: **{current_prog}%**")
                        st.progress(current_prog / 100)
                        
                        # Animasi Sukses Lottie kalau 100%
                        if current_prog == 100:
                            col_confetti, col_text = st.columns([1, 3])
                            with col_confetti:
                                if lottie_success:
                                    st_lottie(lottie_success, height=50, key=f"success_{row['id']}")
                            with col_text:
                                st.success("🎉 Murid Lulus!")

                    with c_del_stu:
                        st.write("") # Spasi
                        st.write("") # Spasi
                        if st.button("🗑️ Hapus Murid", key=f"del_stu_{row['id']}", use_container_width=True):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM students WHERE id=%s", (row['id'],))
                            conn.commit()
                            st.rerun()
                    st.divider()
        else:
            st.info("Belum ada murid. Yuk tambah satu!")