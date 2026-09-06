import os
from datetime import timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///skyteduellene.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT config
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30)

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# ==================== Models ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

# ==================== Routes ====================

@app.route('/')
def hello():
    return jsonify({"message": "Skyteduellene API kjører! 🎯"})

@app.route('/duels', methods=['GET'])
def get_duels():
    return jsonify([
        {"id": 1, "navn": "Duel 1", "status": "aktiv"},
        {"id": 2, "navn": "Duel 2", "status": "avsluttet"}
    ])

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
    
    # Sjekk om bruker allerede eksisterer
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Brukernavn er allerede i bruk"}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "E-post er allerede i bruk"}), 400
    
    # Opprett ny bruker
    user = User(username=data['username'], email=data['email'])
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Lag JWT token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        "success": True, 
        "message": "Bruker opprettet!",
        "access_token": access_token,
        "user": user.to_dict()
    }), 201

@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.json
    
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Brukernavn og passord er påkrevd"}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Ugyldig brukernavn eller passord"}), 401
    
    # Lag JWT token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        "success": True,
        "message": "Innlogget!",
        "access_token": access_token,
        "user": user.to_dict()
    }), 200

@app.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Bruker ikke funnet"}), 404
    
    return jsonify(user.to_dict()), 200

# ==================== Database initialization ====================

@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)
