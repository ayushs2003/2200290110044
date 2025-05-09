from flask import Flask, jsonify
import requests

app = Flask(__name__)

WINDOW_SIZE = 10

windows = {
    'p': [],
    'f': [],
    'e': [],
    'r': [],
}

URL_MAPPING = {
    'p': "http://20.244.56.144/evaluation-service/primes",
    'f': "http://20.244.56.144/evaluation-service/fibo",
    'e': "http://20.244.56.144/evaluation-service/even",
    'r': "http://20.244.56.144/evaluation-service/rand"
}

AUTH_CREDENTIALS = {
    "email": "ayush.2226csit1012@kiet.edu",
    "name": "ayush singh",
    "rollNo": "2200290110044",
    "accessCode": "SxVeja",
    "clientID": "526c3c4c-e578-4902-87a5-f19bb6836f98",
    "clientSecret": "PsQkXvQpVSedgehw"
}

AUTH_URL = "http://20.244.56.144/evaluation-service/auth"

@app.route('/numbers/<numberid>', methods=['GET'])
def get_numbers(numberid):
    HEADERS = {
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:138.0) Gecko/20100101 Firefox/138.0"
    }

    if numberid not in ['p', 'f', 'e', 'r']:
        return jsonify({"error": "Invalid number ID"}), 400
    
    access_token_request = requests.post(AUTH_URL, json=AUTH_CREDENTIALS)
    request_json = access_token_request.json()

    HEADERS["Authorization"] = f"Bearer {request_json['access_token']}"

    window_prev_state = windows[numberid].copy()
    
    try:
        response = requests.get(URL_MAPPING[numberid], headers=HEADERS)
        
        if response.status_code != 200:
            numbers = []
        else:
            numbers = response.json()
            
        for num in numbers['numbers']:
            if num not in windows[numberid]:
                windows[numberid].append(num)
                if len(windows[numberid]) > WINDOW_SIZE:
                    windows[numberid].pop(0)

    except Exception as e:
        numbers = []
    
    avg = calculate_average(windows[numberid])
    
    return jsonify({
        "windowPrevState": window_prev_state,
        "windowCurrState": windows[numberid],
        "numbers": numbers,
        "avg": avg
    })

def calculate_average(numbers):
    if not numbers:
        return 0.00
    return round(sum(numbers) / len(numbers), 2)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)