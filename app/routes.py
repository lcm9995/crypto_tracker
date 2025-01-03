from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
import bcrypt
import requests
import sqlite3
import os
from market_trends import get_market_trends
from price_search import get_crypto_price
from dotenv import load_dotenv
import time

load_dotenv()
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# Create a Blueprint
app_routes = Blueprint("app_routes", __name__)


@app.context_processor
def inject_session():
    user_id = 'user_id' in session
    return dict(user_id = user_id)
def get_db():
    conn = sqlite3.connect('app/crypto_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn
import requests

def fetch_coin_data(endpoint, params=None):
    base_url = "https://api.coingecko.com/api/v3"
    try:
        response = requests.get(f"{base_url}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return None

@app_routes.route('/')
def index():
    market_data = fetch_coin_data("global")
    if market_data:
        market_data = {
            "total_market_cap": market_data["data"]["total_market_cap"]["usd"],
            "volume_24h": market_data["data"]["total_volume"]["usd"],
            "bitcoin_dominance": market_data["data"]["market_cap_percentage"]["btc"]
        }
    else:
        market_data = {
            "total_market_cap": "Unavailable",
            "volume_24h": "Unavailable",
            "bitcoin_dominance": "Unavailable"
        }
    #trends_data = get_market_trends()
    user_name = None
    is_logged_in = False
    if 'user_id' in session:
        db = get_db()
        is_logged_in = True
        user = db.execute("SELECT username FROM Users WHERE user_id = ?", (session['user_id'],)).fetchone()
        if user:
            user_name = user['username']
    return render_template('home.html', market_data = market_data, user_name=user_name, is_logged_in=is_logged_in) 

@app_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user_check = db.execute("SELECT * FROM Users WHERE username = ? OR email = ?", (username, email)).fetchone()

        if user_check:
            flash('Username or email already taken. Please choose another.', 'danger')
            return redirect(url_for('app_routes.register'))

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        db.execute('INSERT INTO users (username, email, pword) VALUES (?, ?, ?)', (username, email, hashed_password))
        db.commit()

        user_id = db.execute('SELECT user_id FROM users WHERE username = ? AND email = ?', (username, email)).fetchone()[0]

        db.execute('INSERT INTO Portfolio (user_id) VALUES (?)', (user_id,))
        db.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('app_routes.login'))

    return render_template('register.html')
@app_routes.route('/get_login', methods=['GET'])
def get_login():
    return render_template('login.html')

@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        try:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
            return redirect('/login')

        if user and bcrypt.checkpw(password.encode('utf-8'), user['pword']):  # Use correct column name
            session['user_id'] = user['user_id']
            flash('Login successful!', 'success')
            return redirect("/")  # Redirect to a protected route, like a dashboard
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('login.html')


@app_routes.route("/search", methods=["GET", "POST"])
def search():
        return render_template('search.html')
@app_routes.route('/results', methods=['GET'])
def results():
        query = request.args.get('query')
        if query:
            print("Got query")
            # First API call to search for the cryptocurrency
            search_url = f"https://api.coingecko.com/api/v3/search?query={query}"
            headers = {"accept": "application/json"}
            response = requests.get(search_url, headers=headers)
            
            if response.status_code == 200:
                print("Respons status = 200")
                search_data = response.json()
                coins = search_data.get('coins', [])

                coin_ids = [coin['id'] for coin in coins]
                price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coin_ids)}&vs_currencies=usd"
                price_response = requests.get(price_url)

                if price_response.status_code == 200:
                    print("Price response status is 200")
                    price_data = price_response.json()
                    for coin in coins:
                        coin['price'] = price_data.get(coin['id'], {}).get('usd', 'N/A')

                    return render_template('results.html', coins=coins, query=query)
                else:
                    error_message = f"Error fetching prices: {price_response.status_code}"
                    return render_template('results.html', error_message=error_message)
            else:
                error_message = f"Error fetching search data: {response.status_code}"
                return render_template('results.html', error_message=error_message)
        else:
            print("No query")
            return render_template('search.html', error_message="No query provided.") 
@app_routes.route('/portfolio')
def portfolio():
    if 'user_id' not in session:
        flash('Please log in to view your portfolio.', 'danger')
        return redirect(url_for('app_routes.login'))
    
    db = get_db()
    user_id = session['user_id']  
    
   
    portfolio_data = db.execute("""
        SELECT crypto_id, SUM(quantity) AS total_quantity, AVG(buy_price) AS average_buy_price
        FROM PortfolioEntry
        WHERE user_id = ?
        GROUP BY crypto_id
    """, (user_id,)).fetchall()
    
    coin_details = {}
    for entry in portfolio_data:
        coin = db.execute("SELECT currency_name, symbol FROM Cryptocurrencies WHERE crypto_id = ?", (entry['crypto_id'],)).fetchone()
        print(f"Details for {entry['crypto_id']}: {coin}")
        coin_details[entry['crypto_id']] = coin
    
    return render_template('portfolio.html', portfolio_entries=portfolio_data, coin_details=coin_details)
@app_routes.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user_id from session
    flash('You have been logged out.', 'info')
    return redirect('/login')

@app_routes.route('/coin/<coin_id>', methods=['GET'])
def coin_details(coin_id):

    coin_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    coin_data_response = requests.get(coin_data_url)
    coin_data = coin_data_response.json() if coin_data_response.status_code == 200 else {}

    exchange_rates_url = f"https://api.coingecko.com/api/v3/exchange_rates"
    exchange_rates_response = requests.get(exchange_rates_url)
    exchange_rates = exchange_rates_response.json().get('rates', {}) if exchange_rates_response.status_code == 200 else {}

    btc_to_coin = exchange_rates.get(coin_id, {}).get('value', 'N/A') 


    historical_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
    historical_data_response = requests.get(historical_data_url)
    historical_data = historical_data_response.json() if historical_data_response.status_code == 200 else {}

    return render_template(
        'coin_details.html',
        coin_data= coin_data,
        historical_data= historical_data,
        exchange_rates=exchange_rates,
    )
def fetch_coin_details_from_api(coin_id):
    retries = 8
    for attempt in range(retries):
        try:
            api_url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                print("fetch coin details status code = 200!!")
                coin_data = response.json()
                print(coin_data)
                return {
                    'id': coin_data['id'],
                    'name': coin_data['name'],
                    'symbol': coin_data['symbol'].upper(),
                    'current_price': coin_data['market_data']['current_price']['usd'],
                    'market_cap': coin_data['market_data']['market_cap']['usd'],
                    'volume': coin_data['market_data']['total_volume']['usd'],
                    'last_updated': coin_data['last_updated']
                }
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt +1 } failed: {e}")
            time.sleep(5)
    return None
@app_routes.route('/coin/<coin_id>/add_to_portfolio', methods=['GET', 'POST'])
def add_to_portfolio(coin_id):
    if 'user_id' not in session:
        flash('You must be logged in to add to your portfolio.', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()
    coin = db.execute("SELECT * FROM Cryptocurrencies WHERE crypto_id = ?", (coin_id,)).fetchone()
    
    if not coin:
        print("not coin")
        coin_details = fetch_coin_details_from_api(coin_id)
        if coin_details:
            print("got coin details")
            db.execute("""
                INSERT INTO Cryptocurrencies (crypto_id, currency_name, symbol)
                VALUES (?, ?, ?)""",
                       (coin_details['id'], coin_details['name'], coin_details['symbol']))
            db.commit()
            coin = db.execute("SELECT * FROM Cryptocurrencies WHERE crypto_id = ?", (coin_id,)).fetchone()
        else:
            print("couldn't get coin details")
            flash('Unable to fetch cryptocurrency details.', 'danger')
            return redirect('/')

    if request.method == 'POST':
        print("request method == post")
        quantity = request.form['quantity']
        try:
            quantity = float(quantity) 
        except ValueError:
            print("Value error for quantity ")
            flash('Please enter a valid quantity.', 'danger')
            return redirect(f'/coin/{coin_id}/add_to_portfolio')
        coin_details = fetch_coin_details_from_api(coin_id)
        db.execute("""
            INSERT INTO PortfolioEntry (user_id, crypto_id, quantity, buy_price)
            VALUES (?, ?, ?, ?)""", (user_id, coin_id, quantity, coin_details['current_price']))
        db.commit()
        print("successfully added to portfolio")
        flash(f'Added {quantity} of {coin_details["name"]} to your portfolio!', 'success')
        return redirect('/portfolio') 
    print("request method == get")
    return render_template('add_to_portfolio.html', coin_data=coin)

@app_routes.route('/test')
def test():
    return "Flask is working!"

@app_routes.route('/browse/categories')
def browse_by_categories():
    #categories = fetch_coin_data("coins/categories")
    trends_data = get_market_trends()
    if not trends_data:
        flash("Unable to fetch data Please try again later.", "danger")
        categories = []

    return render_template('browse_categories.html',  trends=trends_data)
def get_trending_coins():
    
    url = "https://pro-api.coingecko.com/api/v3/search/trending"

    headers = {"accept": "application/json", 
               "x-cg-demo-api-key": "\tCG-Y9SkpCgtQrLRsfXywCt3t1B7" }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        return data['coins'] # Returns the list of trending coins
    else:
        print(f"Error fetching data: {response.status_code}")
        return None
    #coins = response.json()

@app_routes.route('/browse/popular')
def browse_popular_coins():
    #popular_coins = fetch_coin_data("coins/markets", params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 10, "page": 1})
    trending_coins = get_trending_coins()
    if not trending_coins:
        flash("Unable to fetch popular coins. Please try again later.", "danger")
        
        return redirect('/')

    return render_template('browse_popular.html', coins=trending_coins)
@app_routes.route('/browse/by-name')
def browse_by_name():
    coins_list = fetch_coin_data("coins/list")
    if not coins_list:
        flash("Unable to fetch coin names. Please try again later.", "danger")
        coins_list = []

    return render_template('browse_by_name.html', coins=coins_list)