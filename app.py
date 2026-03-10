import streamlit as st
import mysql.connector
import pandas as pd

# Konfigurasi Database (Pake st.secrets biar aman!)
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["db_host"],
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        port=st.secrets["db_port"],
        database=st.secrets["db_name"]
    )

st.set_page_config(page_title="Nayla Finance", page_icon="💰")

# --- SESSION STATE (Biar nggak bolak-balik login) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user' not in st.session_state:
    st.session_state['user'] = ""

# --- FUNGSI AUTH ---
def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
    res = cursor.fetchone()
    conn.close()
    return res

def register_user(username, password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        conn.close()
        return True
    except:
        return False

# --- UI APP ---
st.title("💰 Nayla Project (Personal Finance)")

if not st.session_state['logged_in']:
    tab1, tab2 = st.tabs(["Login", "Daftar Akun"])
    
    with tab1:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Masuk"):
            if login_user(u, p):
                st.session_state['logged_in'] = True
                st.session_state['user'] = u
                st.rerun()
            else:
                st.error("Gagal login, cek lagi ya!")

    with tab2:
        new_u = st.text_input("Username Baru")
        new_p = st.text_input("Password Baru", type="password")
        if st.button("Buat Akun"):
            if register_user(new_u, new_p):
                st.success("Akun berhasil dibuat! Silakan Login.")
            else:
                st.error("Username udah ada atau error.")

else:
    st.sidebar.write(f"Halo, **{st.session_state['user']}**! 👋")
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- DASHBOARD UTAMA ---
    st.subheader("Tambah Catatan Baru")
    col1, col2 = st.columns(2)
    with col1:
        tipe = st.selectbox("Tipe", ["Income", "Expense"])
        jumlah = st.number_input("Nominal (Rp)", min_value=0)
    with col2:
        ket = st.text_area("Keterangan")
    
    if st.button("Simpan Catatan"):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO transactions (username, type, amount, note) VALUES (%s, %s, %s, %s)",
                       (st.session_state['user'], tipe, jumlah, ket))
        conn.commit()
        conn.close()
        st.success("Data berhasil disimpan!")

    st.divider()
    st.subheader("Riwayat Keuangan")
    conn = get_db_connection()
    df = pd.read_sql(f"SELECT type, amount, note, created_at FROM transactions WHERE username='{st.session_state['user']}' ORDER BY created_at DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)