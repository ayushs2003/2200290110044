from flask import Flask, request, jsonify
import requests
import numpy as np

app = Flask(__name__)

AUTH_CREDENTIALS = {
    "email": "ayush.2226csit1012@kiet.edu",
    "name": "ayush singh",
    "rollNo": "2200290110044",
    "accessCode": "SxVeja",
    "clientID": "526c3c4c-e578-4902-87a5-f19bb6836f98",
    "clientSecret": "PsQkXvQpVSedgehw"
}

AUTH_URL = "http://20.244.56.144/evaluation-service/auth"

STOCK_API_BASE_URL = "http://20.244.56.144/evaluation-service"

def get_stock_price_history(ticker, minutes=None):
    HEADERS = {
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0"
    }

    access_token_request = requests.post(AUTH_URL, json=AUTH_CREDENTIALS)
    request_json = access_token_request.json()

    HEADERS["Authorization"] = f"Bearer {request_json['access_token']}"

    url = f"{STOCK_API_BASE_URL}/stocks/{ticker}"
    if minutes is not None:
        url += f"?minutes={minutes}"
    
    response = requests.get(url, headers=HEADERS)
    return response.json()

def calculate_average(price_history):
    if not price_history:
        return 0
    
    total = 0
    for item in price_history:
        total += item['price']
    
    return total / len(price_history)

def calculate_correlation(price_history_1, price_history_2):
    if not price_history_1 or not price_history_2:
        return 0
    
    try:
        prices_1 = []
        for item in price_history_1:
            if isinstance(item, dict) and 'price' in item:
                prices_1.append(float(item['price']))
        
        prices_2 = []
        for item in price_history_2:
            if isinstance(item, dict) and 'price' in item:
                prices_2.append(float(item['price']))
        
        
        if not prices_1 or not prices_2:
            return 0
        
        prices_1 = np.array(prices_1)
        prices_2 = np.array(prices_2)
        
        min_length = min(len(prices_1), len(prices_2))
        
        if min_length < 2:
            return 0
        
        prices_1 = prices_1[:min_length]
        prices_2 = prices_2[:min_length]
        
        if np.std(prices_1) == 0 or np.std(prices_2) == 0:
            return 0
        
        correlation_matrix = np.corrcoef(prices_1, prices_2)
        correlation = correlation_matrix[0, 1]
        
        if np.isnan(correlation):
            return 0
        
        return correlation
    except Exception as e:
        return 0

@app.route('/stocks/<ticker>', methods=['GET'])
def get_average_stock_price(ticker):
    minutes = request.args.get('minutes')
    
    if minutes == 'm' or not minutes or not minutes.isdigit():
        minutes = 60
    else:
        minutes = int(minutes)
        
    aggregation = request.args.get('aggregation')
    
    if aggregation != 'average':
        return jsonify({'error': 'Only average aggregation is supported'}), 400
    
    data = get_stock_price_history(ticker, minutes)
    
    if isinstance(data, list):
        price_history = data
    else:
        if 'stock' in data:
            stock_data = data.get('stock', {})
            price = stock_data.get('price', 0)
            timestamp = stock_data.get('lastUpdatedAt', '')
            price_history = [{'price': price, 'lastUpdatedAt': timestamp}]
        else:
            return jsonify({'error': 'Invalid data received from stock API'}), 500
    
    average_price = calculate_average(price_history)
    
    response = {
        'averageStockPrice': average_price,
        'priceHistory': price_history
    }
    
    return jsonify(response)

@app.route('/stockcorrelation', methods=['GET'])
def get_stock_correlation():
    minutes = request.args.get('minutes')
    
    if minutes == 'm' or not minutes or not minutes.isdigit():
        minutes = 60
    else:
        minutes = int(minutes)
    
    tickers = request.args.getlist('ticker')
    
    if len(tickers) != 2:
        return jsonify({'error': 'Exactly 2 tickers are required'}), 400
    
    data_1 = get_stock_price_history(tickers[0], minutes)
    
    data_2 = get_stock_price_history(tickers[1], minutes)
    
    if not isinstance(data_1, list):
        if 'stock' in data_1:
            data_1 = [data_1.get('stock', {})]
        else:
            return jsonify({'error': f'Invalid data received for {tickers[0]}'}), 500
    
    if not isinstance(data_2, list):
        if 'stock' in data_2:
            data_2 = [data_2.get('stock', {})]
        else:
            return jsonify({'error': f'Invalid data received for {tickers[1]}'}), 500
    
    if not data_1 or not data_2:
        return jsonify({'error': 'No price data available for one or both stocks'}), 404
    
    
    correlation = calculate_correlation(data_1, data_2)
    
    avg_price_1 = calculate_average(data_1)
    avg_price_2 = calculate_average(data_2)
    
    response = {
        'correlation': round(correlation, 4),
        'stocks': {
            tickers[0]: {
                'averagePrice': avg_price_1,
                'priceHistory': data_1
            },
            tickers[1]: {
                'averagePrice': avg_price_2,
                'priceHistory': data_2
            }
        }
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
