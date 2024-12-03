from flask import Flask, Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
import bcrypt
import requests
import sqlite3
import os
from market_trends import get_market_trends
from price_search import get_crypto_price
from dotenv import load_dotenv

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
@app_routes.route('/')
def index():
    trends_data = get_market_trends()
    return render_template('home.html', trends=trends_data) 

@app_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user_check = db.execute("SELECT * FROM Users WHERE username = ? OR email = ?", (username, email)).fetchone()

        if user_check:
            # If user exists with the same username or email, show an error message
            flash('Username or email already taken. Please choose another.', 'danger')
            return redirect(url_for('app_routes.register'))

        # Hash password before saving
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Insert into the database
        #conn = get_db()
        db.execute('INSERT INTO users (username, email, pword) VALUES (?, ?, ?)', (username, email, hashed_password))
        db.commit()

        user_id = db.execute('SELECT user_id FROM users WHERE username = ? AND email = ?', (username, email)).fetchone()[0]

        # Initialize an empty portfolio for the new user
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
# Function to fetch cryptocurrency price

# Routes
""" @app_routes.route("/")
def home():
    return render_template("home.html") """

'''@app_routes.route('/search', methods=['GET', 'POST'])
def search():
    search_results = None
    if request.method == 'POST':
        query = request.form.get('crypto_query')
        if query:
            # Call CoinGecko API to search for cryptocurrencies
            search_url = f"https://api.coingecko.com/api/v3/search?query={query}"
            response = requests.get(search_url)
            if response.status_code == 200:
                data = response.json()
                coins = data.get('coins', [])
                search_results = []

                for coin in coins:
                    coin_id = coin['id']
                    # Fetch price info for the coin
                    price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
                    price_response = requests.get(price_url)
                    if price_response.status_code == 200:
                        price_data = price_response.json()
                        coin_price = price_data.get(coin_id, {}).get('usd', 'N/A')
                        search_results.append({
                            'name': coin['name'],
                            'symbol': coin['symbol'],
                            'id': coin_id,
                            'price': coin_price
                        })
    return render_template('search_results.html', search_results=search_results)'''

@app_routes.route("/search", methods=["GET", "POST"])
def search():
        #if request.method == 'POST':
            #query = request.form.get('query')
            # Process the query and redirect to results
            #return redirect(url_for('results', query=query))
        return render_template('search.html')
        ''' if request.method == "POST":
            query = request.form.get("crypto_name")
            if query:
                crypto_data = get_crypto_price(query)
                if crypto_data:
                    return render_template("results.html", crypto=crypto_data)
            else:
                flash("Please enter a cryptocurrency name or symbol.", "warning")
        return redirect(url_for("app_routes.home"))'''
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
                
                # Prepare a list of coin ids for the second API call to get current prices
                coin_ids = [coin['id'] for coin in coins]
                price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coin_ids)}&vs_currencies=usd"
                price_response = requests.get(price_url)

                if price_response.status_code == 200:
                    print("Price response status is 200")
                    price_data = price_response.json()
                    # Merge the price data with coin details
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
    user_id = session['user_id']  # Get the current logged-in user's ID
    
    # Get the aggregated portfolio data: total quantity and average price per cryptocurrency
    portfolio_data = db.execute("""
        SELECT crypto_id, SUM(quantity) AS total_quantity, AVG(buy_price) AS average_buy_price
        FROM PortfolioEntry
        WHERE user_id = ?
        GROUP BY crypto_id
    """, (user_id,)).fetchall()
    
    # Now, you need to fetch the coin details (like name, symbol) to display them
    coin_details = {}
    for entry in portfolio_data:
        coin = db.execute("SELECT currency_name, symbol FROM Cryptocurrencies WHERE crypto_id = ?", (entry['crypto_id'],)).fetchone()
        coin_details[entry['crypto_id']] = coin
    
    return render_template('portfolio.html', portfolio_entries=portfolio_data, coin_details=coin_details)
""" @app_routes.route('/portfolio')
def portfolio():
    if 'user_id' not in session:
        flash('Please log in to view your portfolio.', 'danger')
        return redirect(url_for('app_routes.login'))
    db = get_db()
    user_id = session['user_id']  # Get the current logged-in user's ID
    print("User ID: " + user_id)
    portfolio_data = db.execute('SELECT * FROM PortfolioEntry WHERE user_id = ?', (user_id,)).fetchall()
    
    return render_template('portfolio.html', portfolio_entries=portfolio_data) """
@app_routes.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user_id from session
    flash('You have been logged out.', 'info')
    return redirect('/login')

@app_routes.route('/coin/<coin_id>', methods=['GET'])
def coin_details(coin_id):
    # Fetch normal coin data by ID
    coin_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    coin_data_response = requests.get(coin_data_url)
    coin_data = coin_data_response.json() if coin_data_response.status_code == 200 else {}

    # Fetch BTC to currency exchange rate for that coin
    exchange_rates_url = f"https://api.coingecko.com/api/v3/exchange_rates"
    exchange_rates_response = requests.get(exchange_rates_url)
    exchange_rates = exchange_rates_response.json().get('rates', {}) if exchange_rates_response.status_code == 200 else {}

    btc_to_coin = exchange_rates.get(coin_id, {}).get('value', 'N/A')  # BTC exchange rate for the coin

    # Fetch historical chart data for that coin (e.g., last 30 days)

    historical_data_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
    historical_data_response = requests.get(historical_data_url)
    historical_data = historical_data_response.json() if historical_data_response.status_code == 200 else {}

    # Pass all the data to the template
    return render_template(
        'coin_details.html',
        coin_data= coin_data,
        historical_data= historical_data,
        exchange_rates=exchange_rates,
    )
def fetch_coin_details_from_api(coin_id):
    api_url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    response = requests.get(api_url)
    if response.status_code == 200:
        print("fetcg coin details status code = 200!!")
        coin_data = response.json()
        return {
            'id': coin_data['id'],
            'name': coin_data['name'],
            'symbol': coin_data['symbol'].upper(),
            'current_price': coin_data['market_data']['current_price']['usd'],
            'market_cap': coin_data['market_data']['market_cap']['usd'],
            'volume': coin_data['market_data']['total_volume']['usd'],
            'last_updated': coin_data['last_updated']
        }
    return None
@app_routes.route('/coin/<coin_id>/add_to_portfolio', methods=['GET', 'POST'])
def add_to_portfolio(coin_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to add to your portfolio.', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()

    # Get the coin details from the database (only static data)
    coin = db.execute("SELECT * FROM Cryptocurrencies WHERE crypto_id = ?", (coin_id,)).fetchone()
    
    if not coin:
        print("not coin")
        # Fetch real-time coin data from the API
        coin_details = fetch_coin_details_from_api(coin_id)
        if coin_details:
            print("got coin details")
            # You could add static data to your DB if needed, but not dynamic data
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
            quantity = float(quantity)  # Make sure the quantity is a number
        except ValueError:
            print("Value error for quantity ")
            flash('Please enter a valid quantity.', 'danger')
            return redirect(f'/coin/{coin_id}/add_to_portfolio')

        # Fetch real-time data again to get the latest price, market cap, etc.
        coin_details = fetch_coin_details_from_api(coin_id)

        # Add the portfolio entry with the real-time price data
        db.execute("""
            INSERT INTO PortfolioEntry (user_id, crypto_id, quantity, buy_price)
            VALUES (?, ?, ?, ?)""", (user_id, coin_id, quantity, coin_details['current_price']))
        db.commit()
        print("successfully added to portfolio")
        flash(f'Added {quantity} of {coin_details["name"]} to your portfolio!', 'success')
        return redirect('/portfolio')  # Redirect to the portfolio page
    print("request method == get")
    return render_template('add_to_portfolio.html', coin_data=coin)

""" @app_routes.route('/coin/<coin_id>/add_to_portfolio', methods=['GET', 'POST'])
def add_to_portfolio(coin_id):
    print("In add_to_portfolio route")

    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to add to your portfolio.', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()

    # Get coin details
    coin = db.execute("SELECT * FROM Cryptocurrencies WHERE crypto_id = ?", (coin_id,)).fetchone()
    if not coin:
        # Fetch and insert the coin details if it doesn't exist
        coin_details = fetch_coin_details_from_api(coin_id)  # Replace with actual API fetch logic
        if coin_details:
            db.execute()
                INSERT INTO Cryptocurrencies (crypto_id, currency_name, symbol, curr_price, market_cap, volume, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?),
                       (coin_details['id'], coin_details['name'], coin_details['symbol'], 
                        coin_details['current_price'], coin_details['market_cap'], 
                        coin_details['volume'], coin_details['last_updated']))
            db.commit()
            coin = db.execute("SELECT * FROM Cryptocurrencies WHERE crypto_id = ?", (coin_id,)).fetchone()
        else:
            flash('Unable to fetch cryptocurrency details.', 'danger')
            return redirect('/')

    if request.method == 'POST':
        # Process form submission
        quantity = request.form.get('quantity', '').strip()
        try:
            quantity = float(quantity)
        except ValueError:
            flash('Please enter a valid quantity.', 'danger')
            return redirect(url_for('app_routes.add_to_portfolio', coin_id=coin_id))

        # Add portfolio entry
        portfolio = db.execute("SELECT * FROM Portfolio WHERE user_id = ?", (user_id,)).fetchone()
        if not portfolio:
            db.execute('INSERT INTO Portfolio (user_id) VALUES (?)', (user_id,))
            db.commit()

        db.execute(
            INSERT INTO PortfolioEntry (user_id, crypto_id, quantity, buy_price)
            VALUES (?, ?, ?, ?), (user_id, coin_id, quantity, coin['curr_price']))
        db.commit()

        flash(f'Added {quantity} of {coin["currency_name"]} to your portfolio!', 'success')
        return redirect('/portfolio')

    # Render a form page if GET method
    return render_template('add_to_portfolio.html', coin=coin) """


""" @app_routes.route('/coin/<coin_id>/add_to_portfolio', methods=['GET', 'POST'])
def add_to_portfolio(coin_id):
    print("In add to portfolio route")
    # Check if the user is logged in
    if 'user_id' not in session:
        flash('You must be logged in to add to your portfolio.', 'danger')
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()

    # Get the coin details
    coin = db.execute("SELECT * FROM Cryptocurrencies WHERE crypto_id = ?", (coin_id,)).fetchone()
    
    if not coin:
        coin_details = fetch_coin_details_from_api(coin_id)  # Replace with actual API fetch logic
        if coin_details:
            db.execute(
                INSERT INTO Cryptocurrencies (crypto_id, currency_name, symbol, curr_price, market_cap, volume, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?),
                       (coin_details['id'], coin_details['name'], coin_details['symbol'], 
                        coin_details['current_price'], coin_details['market_cap'], 
                        coin_details['volume'], coin_details['last_updated']))
            db.commit()
            coin = db.execute("SELECT * FROM Cryptocurrencies WHERE crypto_id = ?", (coin_id,)).fetchone()
        else:
            print("No coin details")
            flash('Unable to fetch cryptocurrency details.', 'danger')
            return redirect('/')

    if request.method == 'POST':
        quantity = request.form['quantity']
        try:
            quantity = float(quantity)  # Make sure the quantity is a number
        except ValueError:
            flash('Please enter a valid quantity.', 'danger')
            return redirect('/'+coin_id + '/add_to_portfolio')

        # Check if a portfolio already exists for this user
        portfolio = db.execute("SELECT * FROM Portfolio WHERE user_id = ?", (user_id,)).fetchone()
        if not portfolio:
            # Create a new portfolio if it doesn't exist
            db.execute('INSERT INTO Portfolio (user_id) VALUES (?)', (user_id,))
            db.commit()

        # Add the portfolio entry to the database
        db.execute(
            INSERT INTO PortfolioEntry (user_id, crypto_id, quantity, buy_price)
            VALUES (?, ?, ?, ?), (user_id, coin_id, quantity, coin['curr_price']))
        db.commit()

        flash(f'Added {quantity} of {coin["currency_name"]} to your portfolio!', 'success')
        return redirect('/portfolio')  # Redirect to the portfolio page

    #return render_template('portfolio.html')
    return redirect('/portfolio') """

@app_routes.route('/test')
def test():
    return "Flask is working!"