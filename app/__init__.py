from flask import Flask, g
import sqlite3
import os

DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'crypto_tracker.db')

def get_db():
    db = getattr(g, '_datebase', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with app.app_context():
        db = get_db()
        with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f :
            db.executescript(f.read())
        db.commit()
        
app = Flask(__name__)

def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()