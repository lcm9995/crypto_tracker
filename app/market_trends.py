import requests
import os
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv('API_KEY')

def get_market_trends():
    url = "https://api.coingecko.com/api/v3/coins/categories"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  
        #data = response.json()
        if response.status_code == 200:
            return response.json()
        else:
            return []
        
        """ 
        trends = {
            'total_market_cap': data['market_data']['total_market_cap']['usd'],
            'total_24h_vol': data['market_data']['total_24h_volumes']['usd'],
            'market_cap_change_24h': data['market_data']['market_cap_change_percentage_24h']
        } """
        #return trends
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching market trends: {e}")
        return None  
