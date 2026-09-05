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

@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.json
    
    # Validering
    if not data.get('username') or len(data.get('username', '')) < 1:
        return jsonify({"error": "Brukernavn er påkrevd"}), 400
    
    if not data.get('email') or '@' not in data.get('email', ''):
        return jsonify({"error": "Gyldig e-post er påkrevd"}), 400
    
    if not data.get('password') or len(data.get('password', '')) < 6:
        return jsonify({"error": "Passord må være minst 6 tegn"}), 400
    
    # TODO: Lagre bruker i database
    return jsonify({
        "success": True, 
        "message": "Bruker opprettet!",
        "user": {
            "id": 1,
            "username": data.get('username'),
            "email": data.get('email')
        }
    }), 201

if __name__ == '__main__':
    app.run(debug=False)
