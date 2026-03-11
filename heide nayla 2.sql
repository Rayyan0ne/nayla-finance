CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_name VARCHAR(100),
    course_name VARCHAR(100),
    progress INT DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Aktif',
    username VARCHAR(50)
);