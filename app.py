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

# --- UI AUTH ---
if not st.session_state['logged_in']:
    st.title("Project Nayla")
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
        query = f"SELECT id, type, amount, note, created_at FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC"
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
                st.success("Data disimpan!")
                st.rerun()

        st.subheader("📜 Riwayat & Hapus Data")
        if not df.empty:
            for index, row in df.iterrows():
                col_data, col_del = st.columns([5, 1])
                with col_data:
                    st.write(f"**{row['note']}** | {row['type']} | **Rp {row['amount']:,.0f}**")
                    st.caption(f"Tanggal: {row['created_at']}")
                with col_del:
                    if st.button("Hapus", key=f"del_fin_{row['id']}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM transactions WHERE id=%s", (row['id'],))
                        conn.commit()
                        st.warning("Terhapus!")
                        st.rerun()
                st.divider()
        else:
            st.write("Belum ada riwayat.")

    # --- MENU 2: STUDY FASHION ADMIN ---
    elif menu == "🎓 Study Fashion Admin":
        st.title("🛠️ Study Fashion Management")
        st.info("Otomatisasi: Checklist modul akan langsung meng-update progress bar murid.")

        conn = get_db_connection()
        df_stu = pd.read_sql(f"SELECT * FROM students WHERE username='{st.session_state['user']}'", conn)
        conn.close()

        with st.expander("👤 Tambah Murid Baru"):
            nc1, nc2 = st.columns(2)
            s_name = nc1.text_input("Nama Murid")
            s_course = nc2.selectbox("Pilih Kursus", ["Dasar Menjahit VR", "Rancang Busana Digital", "Tekstil & Bahan"])
            if st.button("Daftarkan Murid"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students (student_name, course_name, username, progress) VALUES (%s, %s, %s, 0)", (s_name, s_course, st.session_state['user']))
                conn.commit()
                st.success(f"{s_name} terdaftar!")
                st.rerun()

        st.subheader("📊 Progres Kursus Mahasiswa")
        if not df_stu.empty:
            for index, row in df_stu.iterrows():
                with st.container():
                    c_info, c_check, c_del_stu = st.columns([2, 3, 1])
                    c_info.write(f"**{row['student_name']}**\n\n({row['course_name']})")
                    
                    # Logika Checklist Otomatis (4 Modul = 25% per modul)
                    st.write("Ceklis Modul Selesai:")
                    m1 = st.checkbox("Modul 1: Pengenalan", key=f"m1_{row['id']}")
                    m2 = st.checkbox("Modul 2: Pola Dasar", key=f"m2_{row['id']}")
                    m3 = st.checkbox("Modul 3: Teknik Jahit", key=f"m3_{row['id']}")
                    m4 = st.checkbox("Modul 4: Finishing", key=f"m4_{row['id']}")
                    
                    current_prog = sum([m1, m2, m3, m4]) * 25
                    st.progress(current_prog / 100)
                    st.write(f"Progres: {current_prog}%")

                    if c_del_stu.button("Hapus Murid", key=f"del_stu_{row['id']}"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM students WHERE id=%s", (row['id'],))
                        conn.commit()
                        st.rerun()
                    st.divider()
        else:
            st.write("Belum ada murid.")