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

st.set_page_config(page_title="Nayla Finance & Project", page_icon="👗", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI AUTH (Login/Register) ---
if not st.session_state['logged_in']:
    st.title("👗 Study Fashion x Nayla")
    tab1, tab2 = st.tabs(["Login", "Daftar Akun"])
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Masuk"):
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
        if st.button("Buat Akun"):
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
    st.sidebar.title(f"Halo, {st.session_state['user']}! 👋")
    menu = st.sidebar.radio("Pilih Menu:", ["💰 Personal Finance", "🎓 Study Fashion Admin"])
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- MENU 1: PERSONAL FINANCE ---
    if menu == "💰 Personal Finance":
        st.title("💸 Catatan Keuangan Nayla")
        
        conn = get_db_connection()
        query = f"SELECT type, amount, note, created_at FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC"
        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            ti = df[df['type'] == 'Income']['amount'].sum()
            te = df[df['type'] == 'Expense']['amount'].sum()
            saldo = ti - te
            st.metric("Sisa Saldo", f"Rp {saldo:,.0f}")
        
        with st.expander("➕ Tambah Catatan"):
            c1, c2 = st.columns(2)
            tipe = c1.selectbox("Tipe", ["Income", "Expense"])
            amt = c2.number_input("Nominal", min_value=0, step=1000)
            note = st.text_input("Keterangan")
            if st.button("Simpan Finance"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)", (st.session_state['user'], tipe, amt, note))
                conn.commit()
                st.rerun()

        st.subheader("📜 Riwayat")
        if not df.empty:
            df_view = df.copy()
            df_view['amount'] = df_view['amount'].apply(lambda x: f"Rp {x:,.0f}")
            st.table(df_view)

    # --- MENU 2: STUDY FASHION ADMIN (PROPER VERSION) ---
    elif menu == "🎓 Study Fashion Admin":
        st.title("🛠️ Study Fashion Management")
        st.info("Gunakan halaman ini untuk simulasi manajemen murid sesuai proposal P2MW.")

        conn = get_db_connection()
        df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
        conn.close()

        # Input Murid Baru
        with st.expander("👤 Tambah Murid Baru"):
            nc1, nc2 = st.columns(2)
            s_name = nc1.text_input("Nama Murid")
            s_course = nc2.selectbox("Pilih Kursus", ["Dasar Menjahit VR", "Rancang Busana Digital", "Tekstil & Bahan"])
            if st.button("Daftarkan Murid"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students (student_name, course_name, username) VALUES (%s, %s, %s)", (s_name, s_course, st.session_state['user']))
                conn.commit()
                st.success(f"{s_name} berhasil didaftarkan!")
                st.rerun()

        # List Murid & Progres
        st.subheader("📊 Progres Kursus Mahasiswa")
        if not df_stu.empty:
            for index, row in df_stu.iterrows():
                with st.container():
                    col_a, col_b, col_c = st.columns([2, 3, 1])
                    col_a.write(f"**{row['student_name']}**\n\n({row['course_name']})")
                    prog = col_b.slider(f"Update Progres {row['student_name']}", 0, 100, int(row['progress']), key=f"s_{row['id']}")
                    
                    if col_c.button("Update", key=f"btn_{row['id']}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE students SET progress=%s WHERE id=%s", (prog, row['id']))
                        conn.commit()
                        st.rerun()
                    
                    st.progress(prog / 100)
                    st.divider()
        else:
            st.write("Belum ada murid. Yuk tambah satu!")