CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    pword TEXT NOT NULL,
    date_created DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS Cryptocurrencies (
    crypto_id TEXT PRIMARY KEY,
    currency_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    curr_price REAL,
    market_cap REAL,
    volume REAL,
    last_updated TIMESTAMP
);
CREATE TABLE IF NOT EXISTS Fave_Cryptocurrencies (
    user_id INTEGER,
    crypto_id TEXT,
    date_added DATE DEFAULT CURRENT_DATE,
    PRIMARY KEY (user_id, crypto_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (crypto_id) REFERENCES Cryptocurrencies(crypto_id)
);

CREATE TABLE IF NOT EXISTS Portfolio (
    portfolio_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INT NOT NULL UNIQUE,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS PortfolioEntry (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    crypto_id TEXT,
    quantity REAL NOT NULL,
    buy_price REAL,
    date_bought TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(crypto_id)
);

CREATE TABLE IF NOT EXISTS NewsItems (
    news_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    source_url TEXT,
    pub_date TIMESTAMP,
    crypto_id TEXT,
    FOREIGN KEY (crypto_id) REFERENCES Cryptocurrency(crypto_id) ON DELETE SET NULL
);