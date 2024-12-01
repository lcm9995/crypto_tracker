import requests
import os
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv('API_KEY')

def get_market_trends():
    # URL for the CoinGecko Market Trends endpoint
    url = "https://api.coingecko.com/api/v3/coins/categories"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        #data = response.json()
        if response.status_code == 200:
            return response.json()
        else:
            return []
        
        """ # Extract the relevant information from the response
        trends = {
            'total_market_cap': data['market_data']['total_market_cap']['usd'],
            'total_24h_vol': data['market_data']['total_24h_volumes']['usd'],
            'market_cap_change_24h': data['market_data']['market_cap_change_percentage_24h']
        } """
        #return trends
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market trends: {e}")
        return None  # Return None or handle the error appropriately
