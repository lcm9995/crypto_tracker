from flask import Flask, g, jsonify, request
from . import get_db, app

if __name__ == '__main__':
    app.run(debug=True)
    
