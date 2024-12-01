import os
from dotenv import load_dotenv
import requests
from flask import flash


load_dotenv()
api_key = os.getenv('API_KEY')

def get_crypto_price(s_query):
    search_url = f"https://api.coingecko.com/api/v3/search?query={s_query}"
    headers = {"accept": "application/json"}
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        search_data = response.json()
        coins = search_data.get('coins', [])
        print("In price_search.py")

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