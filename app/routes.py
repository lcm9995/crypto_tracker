from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import bcrypt
import requests
import sqlite3

# Create a Blueprint
app_routes = Blueprint("app_routes", __name__)
def get_db():
    conn = sqlite3.connect('crypto_tracker.db')
    return conn 
@app_routes.route('/')
def index():
    return render_template('home.html') 

@app_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user_check = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()

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
        flash('Registration successful!', 'success')
        return redirect(url_for('app_routes.login'))

    return render_template('register.html')

@app_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))  # Redirect to a protected route, like a dashboard
        else:
            flash('Invalid credentials. Please try again.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')
# Function to fetch cryptocurrency price
def get_crypto_price(s_query):
    search_url = f"https://api.coingecko.com/api/v3/search?query={s_query}"
    headers = {"accept": "application/json"}
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        search_data = response.json()
        coins = search_data.get('coins', [])

        if coins:
            coin_id = coins[0]['id']
            price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            price_response = requests.get(price_url)

            if price_response.status_code == 200:
                price_data = price_response.json()
                return {
                    "name": coins[0]['name'],
                    "symbol": coins[0]['symbol'],
                    "price": price_data[coin_id]['usd']
                }
            else:
                flash(f"Error fetching price: {price_response.text}", "danger")
        else:
            flash("No coins found. Please try another query.", "warning")
    else:
        flash(f"Error during search: {response.text}", "danger")
    return None

# Routes
@app_routes.route("/")
def home():
    return render_template("home.html")

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
            # First API call to search for the cryptocurrency
            search_url = f"https://api.coingecko.com/api/v3/search?query={query}"
            headers = {"accept": "application/json"}
            response = requests.get(search_url, headers=headers)
            
            if response.status_code == 200:
                search_data = response.json()
                coins = search_data.get('coins', [])
                
                # Prepare a list of coin ids for the second API call to get current prices
                coin_ids = [coin['id'] for coin in coins]
                price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={','.join(coin_ids)}&vs_currencies=usd"
                price_response = requests.get(price_url)

                if price_response.status_code == 200:
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
            return render_template('results.html', error_message="No query provided.") 

@app_routes.route('/test')
def test():
    return "Flask is working!"