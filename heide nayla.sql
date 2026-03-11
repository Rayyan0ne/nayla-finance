-- Membuat tabel user biar Nayla bisa daftar akun
CREATE TABLE IF NOT EXISTS users (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(50) NOT NULL
);

-- Membuat tabel transaksi buat nyatet pengeluaran/pemasukan
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    type ENUM('Income', 'Expense'),
    amount DECIMAL(15, 2),
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username)
);