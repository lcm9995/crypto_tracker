import os
from flask import Flask #, g, jsonify, request
#from app import get_db, app
from dotenv import load_dotenv
from routes import app_routes

load_dotenv()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
#app.config['DATABASE'] = 'sqlite:///db.sqlite'

app.secret_key = os.getenv("SECRET_KEY", "12345")

app.register_blueprint(app_routes)

if __name__ == '__main__':
    app.run(debug=True)
    
