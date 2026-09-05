from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    return jsonify({"message": "Skyteduellene API kjører! 🎯"})

@app.route('/duels', methods=['GET'])
def get_duels():
    # Returnerer en array direkte, ikke wrappet i objekt
    return jsonify([
        {"id": 1, "navn": "Duel 1", "status": "aktiv"},
        {"id": 2, "navn": "Duel 2", "status": "avsluttet"}
    ])

@app.route('/api/dueller', methods=['GET'])
def get_dueller():
    return jsonify({
        "dueller": [
            {"id": 1, "navn": "Duel 1", "status": "aktiv"},
            {"id": 2, "navn": "Duel 2", "status": "avsluttet"}
        ]
    })

@app.route('/api/duell', methods=['POST'])
def create_duell():
    data = request.json
    return jsonify({"success": True, "duell": data}), 201

if __name__ == '__main__':
    app.run(debug=False)
