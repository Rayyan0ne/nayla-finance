import streamlit as st
import mysql.connector
import pandas as pd

# Fungsi Koneksi
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["db_host"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        port=st.secrets["db_port"],
        database=st.secrets["db_name"]
    )

# --- CONFIG HALAMAN (Biar lebih estetik) ---
st.set_page_config(page_title="Nayla Finance & Project", page_icon="👗", layout="wide")

# --- CUSTOM CSS (Rahasia biar web kelihatan mahal) ---
st.markdown("""
    <style>
    /* Mengubah font dan background */
    .main { background-color: #fcfcfc; }
    /* Desain Card untuk statistik */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        border: 1px solid #eee;
        text-align: center;
    }
    /* Efek hover tombol */
    .stButton>button {
        border-radius: 10px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_stdio=True)

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI AUTH ---
if not st.session_state['logged_in']:
    # Bikin tampilan login di tengah
    _, col_auth, _ = st.columns([1, 2, 1])
    with col_auth:
        st.markdown("<h1 style='text-align: center;'>👗 Project Nayla</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Daftar Akun"])
        with tab1:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Masuk", use_container_width=True):
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
            new_u = st.text_input("Username Baru")
            new_p = st.text_input("Password Baru", type="password")
            if st.button("Buat Akun", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_u, new_p))
                    conn.commit()
                    st.success("Selesai! Silakan Login.")
                except: st.error("User sudah ada!")
                conn.close()

# --- DASHBOARD UTAMA ---
else:
    st.sidebar.markdown(f"### 👤 Halo, **{st.session_state['user']}**!")
    menu = st.sidebar.radio("Pilih Menu:", ["💰 Personal Finance", "🎓 Study Fashion Admin"])
    
    st.sidebar.divider()
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- MENU 1: PERSONAL FINANCE ---
    if menu == "💰 Personal Finance":
        st.title("💸 Catatan Keuangan Nayla")
        
        conn = get_db_connection()
        query = f"SELECT id, type, amount, note, created_at FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC"
        df = pd.read_sql(query, conn)
        conn.close()

        # Statistik Header
        if not df.empty:
            ti = df[df['type'] == 'Income']['amount'].sum()
            te = df[df['type'] == 'Expense']['amount'].sum()
            saldo = ti - te
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='metric-card'><p>Pemasukan</p><h3 style='color:green;'>Rp {ti:,.0f}</h3></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div class='metric-card'><p>Pengeluaran</p><h3 style='color:red;'>Rp {te:,.0f}</h3></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div class='metric-card'><p>Sisa Saldo</p><h3 style='color:blue;'>Rp {saldo:,.0f}</h3></div>", unsafe_allow_html=True)
            st.divider()
        
        with st.expander("➕ Tambah Catatan Baru"):
            c1, c2 = st.columns(2)
            tipe = c1.selectbox("Tipe", ["Income", "Expense"])
            amt = c2.number_input("Nominal", min_value=0, step=1000)
            note = st.text_input("Keterangan")
            if st.button("Simpan Keuangan", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", (st.session_state['user'], tipe, amt, note))
                conn.commit()
                st.success("Data disimpan!")
                st.rerun()

        st.subheader("📜 Riwayat & Hapus Data")
        if not df.empty:
            for index, row in df.iterrows():
                with st.container():
                    col_icon, col_data, col_del = st.columns([0.5, 4.5, 1])
                    icon = "➕" if row['type'] == 'Income' else "➖"
                    col_icon.markdown(f"### {icon}")
                    with col_data:
                        st.write(f"**{row['note']}** | **Rp {row['amount']:,.0f}**")
                        st.caption(f"📅 {row['created_at']}")
                    with col_del:
                        if st.button("Hapus", key=f"del_fin_{row['id']}"):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
                            conn.commit()
                            st.rerun()
                    st.divider()
        else:
            st.info("Belum ada riwayat transaksi.")

    # --- MENU 2: STUDY FASHION ADMIN ---
    elif menu == "🎓 Study Fashion Admin":
        st.title("🛠️ Study Fashion Management")
        st.info("Otomatisasi: Checklist modul akan langsung meng-update progress bar murid.")

        conn = get_db_connection()
        df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
        conn.close()

        # Statistik Murid
        if not df_stu.empty:
            st.markdown(f"<div class='metric-card'><h4>Total Murid Aktif: {len(df_stu)}</h4></div>", unsafe_allow_html=True)
            st.write("")

        with st.expander("👤 Daftarkan Murid Baru"):
            nc1, nc2 = st.columns(2)
            s_name = nc1.text_input("Nama Murid")
            s_course = nc2.selectbox("Pilih Kursus", ["Dasar Menjahit VR", "Rancang Busana Digital", "Tekstil & Bahan"])
            if st.button("Proses Pendaftaran", use_container_width=True):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students (student_name, course_name, username, progress) VALUES (%s, %s, %s, 0)", (s_name, s_course, st.session_state['user']))
                conn.commit()
                st.success(f"{s_name} berhasil terdaftar!")
                st.rerun()

        st.subheader("📊 Progres Kursus Mahasiswa")
        if not df_stu.empty:
            for index, row in df_stu.iterrows():
                with st.container():
                    # Card style sederhana untuk tiap murid
                    st.markdown(f"**Nama: {row['student_name']}** | Kursus: *{row['course_name']}*")
                    c_check, c_prog, c_del_stu = st.columns([2, 3, 1])
                    
                    with c_check:
                        st.write("Ceklis Modul:")
                        m1 = st.checkbox("Modul 1: Intro", key=f"m1_{row['id']}")
                        m2 = st.checkbox("Modul 2: Pola", key=f"m2_{row['id']}")
                        m3 = st.checkbox("Modul 3: Jahit", key=f"m3_{row['id']}")
                        m4 = st.checkbox("Modul 4: Final", key=f"m4_{row['id']}")
                    
                    with c_prog:
                        current_prog = sum([m1, m2, m3, m4]) * 25
                        st.write(f"Status Belajar: **{current_prog}%**")
                        st.progress(current_prog / 100)
                        if current_prog == 100:
                            st.success("🎉 Murid Lulus!")

                    with c_del_stu:
                        st.write("") # Spasi
                        if st.button("Hapus Murid", key=f"del_stu_{row['id']}", type="secondary"):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM students WHERE id=%s", (row['id'],))
                            conn.commit()
                            st.rerun()
                    st.divider()
        else:
            st.info("Belum ada murid yang terdaftar.")