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

st.set_page_config(page_title="Nayla Project", page_icon="💰")

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- UI AUTH (Login/Register) ---
if not st.session_state['logged_in']:
    st.title("💰 Nayla Project")
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
    st.title(f"💰 Nayla Project (Finance)")
    st.sidebar.write(f"Halo, **{st.session_state['user']}**! 👋")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # Ambil Data
    conn = get_db_connection()
    query = f"SELECT type, amount, note, created_at FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC"
    df = pd.read_sql(query, conn)
    conn.close()

    # --- HITUNG SALDO ---
    if not df.empty:
        total_income = df[df['type'] == 'Income']['amount'].sum()
        total_expense = df[df['type'] == 'Expense']['amount'].sum()
        saldo_akhir = total_income - total_expense
        
        # Tampilan Saldo yang Wah
        st.metric(label="Sisa Saldo Saat Ini", value=f"Rp {saldo_akhir:,.0f}")
        
        col1, col2 = st.columns(2)
        col1.info(f"Total Masuk: Rp {total_income:,.0f}")
        col2.warning(f"Total Keluar: Rp {total_expense:,.0f}")
    else:
        st.info("Belum ada data. Saldo: Rp 0")

    st.divider()

    # --- INPUT DATA ---
    with st.expander("➕ Tambah Transaksi"):
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            tipe = st.selectbox("Tipe", ["Income", "Expense"])
            jumlah = st.number_input("Nominal (Rp)", min_value=0, step=1000)
        with t_col2:
            ket = st.text_input("Keterangan")
        
        if st.button("Simpan Data"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)",
                           (st.session_state['user'], tipe, jumlah, ket))
            conn.commit()
            conn.close()
            st.success("Data Berhasil Disimpan!")
            st.rerun()

    # --- TABEL RIWAYAT ---
    st.subheader("📜 Riwayat Transaksi")
    if not df.empty:
        # Bikin nomor urut dari 1
        df.index = range(1, len(df) + 1)
        
        # SAKTI: Ini buat ngilangin desimal dan nambahin pemisah ribuan biar rapi
        df_display = df.copy()
        df_display['amount'] = df_display['amount'].apply(lambda x: f"Rp {x:,.0f}")
        
        st.table(df_display)
    else:
        st.write("Belum ada riwayat.")