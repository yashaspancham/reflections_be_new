--create user and grant him permission 
CREATE DATABASE refDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON refDB.* TO 'django_user'@'localhost' IDENTIFIED BY 'refpwd';
FLUSH PRIVILEGES;

--create tables

CREATE TABLE entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entryContent TEXT NOT NULL,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    lastUpdated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);


CREATE TABLE tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    dueDate DATE,
    createdAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    lastUpdated DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

--example insets

INSERT INTO entries (entryContent) 
VALUES ('<p>This is my first journal entry in HTML</p>');

INSERT INTO tasks (description, dueDate) 
VALUES ('Finish backend setup', '2025-08-30');

--show entire table
SELECT * FROM entries;
SELECT * FROM tasks;