import os
from dotenv import load_dotenv
import requests


load_dotenv()
api_key = os.getenv('API_KEY')

def get_crypto_price(s_query):
    search_url = f"https://api.coingecko.com/api/v3/search?query={s_query}"
    headers = {"accept": "application/json"}
    response = requests.get(search_url, headers=headers)
    if response.status_code==200:
        search_data = response.json()
        coins = search_data.get('coins', [])

        if coins:
            coin_id = coins[0]['id']
            print(f"Found Coin: {coin_id}")

            price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            price_response = requests.get(price_url)

            if price_response.status_code == 200:
                price_data = price_response.json()
                print(f"{coin_id.capitalize()} Price (USD): {price_data[coin_id]['usd']}")
            else:
                print(f"Error fetching price: {price_response.status_code} - {price_response.text}")
        else:
            print("No coins found.")
    else:
        print(f"Error during search: {response.status_code} - {response.text}")

get_crypto_price("bitcoin")
