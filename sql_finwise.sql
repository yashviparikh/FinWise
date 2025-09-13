CREATE DATABASE investment;
USE investment;
drop database investment;

CREATE TABLE users (
    userid INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    money DECIMAL(12,2) DEFAULT 10000,
    profitorloss DECIMAL(12,2) DEFAULT 0,
    profitpercent FLOAT DEFAULT 0.0,
    losspercent FLOAT DEFAULT 0.0,
    last_login DATETIME,
    progress INT DEFAULT 0,
    level INT DEFAULT 0
);


-- STOCK TABLE
CREATE TABLE stock (
    stock_id INT PRIMARY KEY AUTO_INCREMENT,
    stock_symbol VARCHAR(10) UNIQUE NOT NULL,
    stock_name VARCHAR(100)
);

-- WATCHLIST TABLE
CREATE TABLE watchlist (
    watchlist_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    stock_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(userid),
    FOREIGN KEY (stock_id) REFERENCES stock(stock_id)
);

-- PORTFOLIO TABLE
CREATE TABLE portfolio (
    portfolioid INT PRIMARY KEY AUTO_INCREMENT,
    userid INT,
    stock_id INT NOT NULL,
    stockname VARCHAR(100),
    companyname VARCHAR(100),
    totalquantity INT DEFAULT 0,
    averagebuyprice DECIMAL(12,2) DEFAULT 0.00,
    totalinvested DECIMAL(12,2) DEFAULT 0.00,
    FOREIGN KEY (userid) REFERENCES users(userid)
);

-- TRANSACTION HISTORY TABLE
CREATE TABLE transactionhistory (
    transactionid INT PRIMARY KEY AUTO_INCREMENT,
    userid INT NOT NULL,
    portfolioid INT NOT NULL,
    companyname VARCHAR(100) NOT NULL,
    stockname VARCHAR(100) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    transactiontype VARCHAR(10) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES users(userid),
    FOREIGN KEY (portfolioid) REFERENCES portfolio(portfolioid)
);

-- FIFO LOT TABLE
CREATE TABLE fifolot (
    lotid INT PRIMARY KEY AUTO_INCREMENT,
    userid INT NOT NULL,
    portfolioid INT NOT NULL,
    companyname VARCHAR(100) NOT NULL,
    quantityremaining INT NOT NULL,
    pricepershare DECIMAL(12,2) NOT NULL,
    buydate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES users(userid),
    FOREIGN KEY (portfolioid) REFERENCES portfolio(portfolioid)
);

CREATE TABLE stockhistory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userid INT NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    dates DATE NOT NULL,
    close_price FLOAT NOT NULL,
    UNIQUE KEY unique_user_stock_date (userid, stock_name, dates)
);

CREATE TABLE useractivity (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    userid INT NOT NULL,
    activity_type VARCHAR(50) NOT NULL, 
    activity_value FLOAT DEFAULT 0,    
    activity_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES Users(userid)
);

CREATE TABLE milestones (
    milestone_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    description VARCHAR(255),
    type VARCHAR(20),   
    threshold_value FLOAT  
);

CREATE TABLE usermilestones (
    usermilestone_id INT PRIMARY KEY AUTO_INCREMENT,
    userid INT,
    milestone_id INT,
    achieved_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userid) REFERENCES Users(userid),
    FOREIGN KEY (milestone_id) REFERENCES Milestones(milestone_id)
);

CREATE TABLE stockdata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(30),        
    date DATE,                  
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    adj_close FLOAT,
    volume BIGINT,
    UNIQUE(symbol, date)         
);

select * from users;
select * from watchlist;
select * from stock;
select * from portfolio;
select * from transactionhistory;
select * from fifolot;
select * from stockhistory;
select * from useractivity;
select * from milestones;
select * from usermilestones;
select * from stockdata;

drop table STOCKDATA;
INSERT INTO users (userid, name, email) VALUES (1, 'alice','alice@gmail.com');
ALTER TABLE users MODIFY COLUMN level VARCHAR(20) DEFAULT 'Beginner';
INSERT INTO milestones (name, description, type, threshold_value) VALUES
('Beginner Investor', 'Own at least 1 stock in your portfolio', 'portfolio', 1),
('Intermediate Investor', 'Own at least 6 stocks in your portfolio', 'portfolio', 6),
('Advanced Investor', 'Own at least 11 stocks in your portfolio', 'portfolio', 11),

('Profit Novice', 'Achieve at least 5% profit on investments', 'profit', 5),
('Profit Achiever', 'Achieve at least 20% profit on investments', 'profit', 20),
('Profit Expert', 'Achieve at least 51% profit on investments', 'profit', 51),

('3-Day Streak', 'Log in or trade for 3 consecutive days', 'consistency', 3),
('7-Day Streak', 'Log in or trade for 7 consecutive days', 'consistency', 7),
('30-Day Streak', 'Log in or trade for 30 consecutive days', 'consistency', 30);

SELECT * FROM stock WHERE stock_symbol = 'TCS';

INSERT INTO stock (stock_symbol, stock_name)
VALUES ('TCS', 'Tata Consultancy Services Limited');

SELECT * FROM stock WHERE stock_symbol = 'TCS';
DELETE FROM stock WHERE stock_symbol = 'TCS';

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/stock_list.csv'
INTO TABLE stock
FIELDS TERMINATED BY ',' 
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@SYMBOL, @NAME, @SERIES, @DATE, @PAIDUP, @MKTLOT, @ISIN, @FACEVALUE)
SET stock_symbol = @SYMBOL,
    stock_name   = @NAME;

select*from stock;

SHOW VARIABLES LIKE 'secure_file_priv';

select*from users;

SELECT * FROM useractivity WHERE userid=1 ORDER BY activity_date DESC;
SELECT * FROM stockhistory WHERE userid=1 ORDER BY dates DESC;

DELETE FROM fifolot WHERE userid = 1;
SELECT * FROM transactionhistory WHERE userid = 1;
SELECT * FROM portfolio WHERE userid = 1;
ALTER TABLE portfolio ADD COLUMN profitorloss DECIMAL(12,2) DEFAULT 0;

DESCRIBE Portfolio;


-- show portfolio rows (inspect totalinvested, totalquantity, averagebuyprice)
SELECT portfolioid, userid, stockname, totalquantity, averagebuyprice, totalinvested
FROM portfolio
WHERE userid = 1;

-- show FIFO lots for that portfolio
SELECT * FROM fifolot WHERE userid = 1;

-- check transactions
SELECT * FROM transactionhistory WHERE userid = 1 ORDER BY timestamp DESC LIMIT 10;
ALTER TABLE portfolio DROP COLUMN profitorloss;

