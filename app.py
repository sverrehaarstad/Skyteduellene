import cloudinary
import cloudinary.uploader
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

cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

ADMIN_EMAILS = {
    "sverrehaarstad@icloud.com"
}

def get_role(email):
    return "admin" if email.lower() in ADMIN_EMAILS else "user"
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
            'role': get_role(self.email),
            'created_at': self.created_at.isoformat()
        }
class Duel(db.Model):
    __tablename__ = 'duels'

    id = db.Column(db.Integer, primary_key=True)
    shooter1 = db.Column(db.String(120), nullable=False)
    shooter2 = db.Column(db.String(120), nullable=False)
    shooter1_img = db.Column(db.Text, default="")
    shooter2_img = db.Column(db.Text, default="")
    discipline = db.Column(db.String(80), default="")
    venue = db.Column(db.String(120), default="")
    start_time = db.Column(db.String(100), default="")
    start_at = db.Column(db.String(100), default="")
    tournament_id = db.Column(db.String(100), default="")
    status = db.Column(db.String(30), default="open")
    outcome = db.Column(db.String(20), default="")
    score1 = db.Column(db.String(50), default="")
    score2 = db.Column(db.String(50), default="")
    is_deleted = db.Column(db.Boolean, default=False)

    def to_dict(self):
        tip_counts = {
    "1": Tip.query.filter_by(duel_id=self.id, pick="1").count(),
    "X": Tip.query.filter_by(duel_id=self.id, pick="X").count(),
    "2": Tip.query.filter_by(duel_id=self.id, pick="2").count()
}
        return {
            "id": self.id,
            "tip_counts": tip_counts,
            "shooter1": self.shooter1,
            "shooter2": self.shooter2,
            "shooter1_img": self.shooter1_img,
            "shooter2_img": self.shooter2_img,
            "discipline": self.discipline,
            "venue": self.venue,
            "start_time": self.start_time,
            "start_at": self.start_at,
            "tournament_id": self.tournament_id,
            "tournament_name": (
    Tournament.query.get(int(self.tournament_id)).name
    if self.tournament_id and Tournament.query.get(int(self.tournament_id))
    else ""
),
            "status": self.status,
            "outcome": self.outcome,
            "score1": self.score1,
            "score2": self.score2
        }
class Tip(db.Model):
    __tablename__ = 'tips'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    duel_id = db.Column(db.Integer, nullable=False)
    pick = db.Column(db.String(1), nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'duel_id', name='unique_user_duel_tip'),
    )

    def to_dict(self):
        duel = Duel.query.get(self.duel_id)

        correct = False
        if duel and duel.status == "finished":
            correct = self.pick == duel.outcome

        return {
            "id": self.id,
            "pick": self.pick,
            "correct": correct,
            "duel": duel.to_dict() if duel else None
        }

class PointRecord(db.Model):
    __tablename__ = 'point_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)

    duel_id = db.Column(db.Integer, nullable=False)
    tournament_id = db.Column(db.Integer, nullable=True)

    points = db.Column(db.Integer, default=0)

    shooter1 = db.Column(db.String(120), default="")
    shooter2 = db.Column(db.String(120), default="")

    active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=db.func.now())

class DuelPointStatus(db.Model):
    __tablename__ = 'duel_point_status'

    duel_id = db.Column(db.Integer, primary_key=True)
    points_enabled = db.Column(db.Boolean, default=True)

class DuelTournament(db.Model):
    __tablename__ = 'duel_tournaments'

    duel_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, primary_key=True)
class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    season = db.Column(db.String(50), default="")

    def to_dict(self):
        duel_count = Duel.query.filter_by(tournament_id=str(self.id)).count()

        return {
            "id": self.id,
            "name": self.name,
            "season": self.season,
            "duel_count": duel_count
        }

class SiteSetting(db.Model):
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    hero_image = db.Column(db.Text, default="")

    def to_dict(self):
        return {
            "hero_image": self.hero_image
        }
# ==================== Routes ====================

@app.route('/')
def hello():
    return jsonify({"message": "Skyteduellene API kjører! 🎯"})

@app.route('/api/duels', methods=['GET'])
def get_duels():
    duels = Duel.query.filter_by(is_deleted=False).order_by(Duel.id.desc()).all()
    return jsonify([duel.to_dict() for duel in duels])

@app.route('/api/duels/<int:duel_id>', methods=['GET'])
def get_duel(duel_id):
    duel = Duel.query.get(duel_id)

    if not duel:
        return jsonify({"error": "Duell ikke funnet"}), 404

    return jsonify(duel.to_dict()), 200

@app.route('/api/duels/<int:duel_id>', methods=['DELETE'])
@jwt_required()
def delete_duel(duel_id):
    duel = Duel.query.get(duel_id)

    if not duel:
        return jsonify({"error": "Duell ikke funnet"}), 404

    duel.is_deleted = True
    db.session.commit()

    return jsonify({"success": True}), 200
    
@app.route('/api/tournaments/<int:tid>', methods=['DELETE'])
@jwt_required()
def delete_tournament(tid):
    tournament = Tournament.query.get(tid)

    if not tournament:
        return jsonify({"error": "Serie ikke funnet"}), 404

    duels = Duel.query.filter_by(tournament_id=str(tid)).all()

    for duel in duels:
        Tip.query.filter_by(duel_id=duel.id).delete()
        db.session.delete(duel)

    db.session.delete(tournament)
    db.session.commit()

    return jsonify({"success": True}), 200

@app.route('/api/duels', methods=['POST', 'OPTIONS'])
def create_duel():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}

    if not data.get("shooter1") or not data.get("shooter2"):
        return jsonify({"error": "Begge navnene må fylles ut"}), 400

    duel = Duel(
        shooter1=data.get("shooter1", ""),
        shooter2=data.get("shooter2", ""),
        shooter1_img=data.get("shooter1_img", ""),
        shooter2_img=data.get("shooter2_img", ""),
        discipline=data.get("discipline", ""),
        venue=data.get("venue", ""),
        start_time=data.get("start_time", ""),
        start_at=data.get("start_at", ""),
        tournament_id=data.get("tournament_id", "")
    )

    db.session.add(duel)
    db.session.commit()

    return jsonify(duel.to_dict()), 201
@app.route('/api/duels/<int:duel_id>/tip', methods=['POST', 'OPTIONS'])
@jwt_required()
def tip_duel(duel_id):
    if request.method == 'OPTIONS':
        return '', 204

    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    pick = data.get("pick")

    if pick not in ["1", "X", "2"]:
        return jsonify({"error": "Ugyldig tips"}), 400

    duel = Duel.query.get(duel_id)
    if not duel:
        return jsonify({"error": "Duell ikke funnet"}), 404

    tip = Tip.query.filter_by(user_id=user_id, duel_id=duel_id).first()

    if tip:
        tip.pick = pick
    else:
        tip = Tip(user_id=user_id, duel_id=duel_id, pick=pick)
        db.session.add(tip)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Tips lagret",
        "tip": tip.to_dict()
    }), 200

@app.route('/api/duels/<int:duel_id>/result', methods=['POST', 'OPTIONS'])
@jwt_required()
def save_duel_result(duel_id):
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}

    duel = Duel.query.get(duel_id)
    if not duel:
        return jsonify({"error": "Duell ikke funnet"}), 404

    outcome = data.get("outcome")

    if outcome not in ["1", "X", "2"]:
        return jsonify({"error": "Ugyldig resultat"}), 400

    duel.outcome = outcome
    duel.score1 = str(data.get("score1", ""))
    duel.score2 = str(data.get("score2", ""))
    duel.status = "finished"

    status = DuelPointStatus.query.get(duel.id)
    points_enabled = True if not status else status.points_enabled

    tips = Tip.query.filter_by(duel_id=duel.id).all()

    correct_user_ids = {
        tip.user_id
        for tip in tips
        if tip.pick == outcome
    }

    existing_records = PointRecord.query.filter_by(
        duel_id=duel.id
    ).all()

    existing_by_user = {
        record.user_id: record
        for record in existing_records
    }

    for record in existing_records:
        if record.user_id in correct_user_ids:
            record.points = 1
            record.active = points_enabled
        else:
            record.points = 0
            record.active = False

    for user_id in correct_user_ids:
        if user_id not in existing_by_user:
            db.session.add(PointRecord(
                user_id=user_id,
                duel_id=duel.id,
                points=1,
                shooter1=duel.shooter1,
                shooter2=duel.shooter2,
                active=points_enabled
            ))

    db.session.commit()

    return jsonify(duel.to_dict()), 200

@app.route('/api/duels/<int:duel_id>/remove-points', methods=['POST'])
@jwt_required()
def remove_duel_points(duel_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.email) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    duel = Duel.query.get(duel_id)

    if not duel:
        return jsonify({"error": "Duell ikke funnet"}), 404

    status = DuelPointStatus.query.get(duel_id)

    if not status:
        status = DuelPointStatus(
            duel_id=duel_id,
            points_enabled=False
        )
        db.session.add(status)
    else:
        status.points_enabled = False

    point_records = PointRecord.query.filter_by(
        duel_id=duel_id
    ).all()

    for record in point_records:
        record.active = False

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Poengene fra duellen er fjernet"
    }), 200
    
@app.route('/api/my-tips', methods=['GET'])
@jwt_required()
def get_my_tips():
    user_id = int(get_jwt_identity())

    tips = Tip.query.filter_by(user_id=user_id).all()

    return jsonify([tip.to_dict() for tip in tips]), 200

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    users = User.query.all()
    rows = []

    for user in users:
        tips = Tip.query.filter_by(user_id=user.id).all()
        total_tips = len(tips)

        point_records = PointRecord.query.filter_by(
            user_id=user.id,
            active=True
        ).all()

        points = sum(record.points for record in point_records)
        correct = points

        accuracy = round(
            (correct / total_tips) * 100
        ) if total_tips > 0 else 0

        rows.append({
            "id": user.id,
            "name": user.username,
            "correct": correct,
            "total_tips": total_tips,
            "accuracy": accuracy,
            "points": points
        })

    rows.sort(key=lambda x: x["points"], reverse=True)

    return jsonify(rows), 200

@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    tournaments = Tournament.query.order_by(Tournament.id.desc()).all()
    return jsonify([t.to_dict() for t in tournaments]), 200


@app.route('/api/tournaments', methods=['POST', 'OPTIONS'])
@jwt_required()
def create_tournament():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    season = data.get("season", "").strip()

    if not name:
        return jsonify({"error": "Navn på serie/sesong mangler"}), 400

    tournament = Tournament(
        name=name,
        season=season
    )

    db.session.add(tournament)
    db.session.commit()

    return jsonify(tournament.to_dict()), 201

@app.route('/api/tournaments/<int:tid>', methods=['GET'])
def get_tournament(tid):
    tournament = Tournament.query.get(tid)

    if not tournament:
        return jsonify({"error": "Fant ikke serien"}), 404

    duels = Duel.query.filter_by(
        tournament_id=str(tid)
    ).order_by(Duel.id.desc()).all()

    duel_ids = [duel.id for duel in duels]

    standings = []

    users = User.query.all()

    for user in users:
        # Ikke vis admin i sesongtabellen
        if get_role(user.email) == "admin":
            continue

        tips = Tip.query.filter(
            Tip.user_id == user.id,
            Tip.duel_id.in_(duel_ids)
        ).all() if duel_ids else []

        if not tips:
            continue

        correct = 0

        for tip in tips:
            duel = Duel.query.get(tip.duel_id)

            if (
                duel
                and duel.status == "finished"
                and tip.pick == duel.outcome
            ):
                correct += 1

        total_tips = len(tips)
        accuracy = round(
            (correct / total_tips) * 100, 1
        ) if total_tips > 0 else 0

        standings.append({
            "id": user.id,
            "name": user.username,
            "points": correct,
            "correct": correct,
            "total_tips": total_tips,
            "accuracy": accuracy
        })

    standings.sort(
        key=lambda row: (row["points"], row["correct"]),
        reverse=True
    )

    finished_count = sum(
        1 for duel in duels
        if duel.status == "finished"
    )

    all_done = len(duels) > 0 and finished_count == len(duels)

    winners = []

    if all_done and standings and standings[0]["points"] > 0:
        top_points = standings[0]["points"]

        winners = [
            row for row in standings
            if row["points"] == top_points
        ]

    return jsonify({
        "tournament": tournament.to_dict(),
        "duels": [duel.to_dict() for duel in duels],
        "standings": standings,
        "winners": winners,
        "winner": winners[0] if winners else None,
        "finished_count": finished_count,
        "duel_count": len(duels)
    }), 200

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.json
    
    # Validering
    if not data.get('email') or '@' not in data.get('email', ''):
        return jsonify({"error": "Gyldig e-post er påkrevd"}), 400
    
    if not data.get('password') or len(data.get('password', '')) < 6:
        return jsonify({"error": "Passord må være minst 6 tegn"}), 400
    
    # Sjekk om bruker allerede eksisterer
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "E-post er allerede i bruk"}), 400
    
    # Opprett ny bruker med navn eller email som username
    username = data.get('name') or data['email'].split('@')[0]
    if User.query.filter_by(username=username).first():
        username = f"{username}_{User.query.count()}"
    
    user = User(username=username, email=data['email'])
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Lag JWT token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "success": True, 
        "message": "Bruker opprettet!",
        "token": access_token,
        "user": user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.json
    
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "E-post og passord er påkrevd"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({"error": "Ugyldig e-post eller passord"}), 401
    
    # Lag JWT token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        "success": True,
        "message": "Innlogget!",
        "token": access_token,
        "user": user.to_dict()
    }), 200

@app.route('/api/auth/me', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_me():
    if request.method == 'OPTIONS':
        return '', 204
    
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({"error": "Bruker ikke funnet"}), 404
    
    return jsonify(user.to_dict()), 200

@app.route('/api/settings', methods=['GET'])
def get_settings():
    setting = SiteSetting.query.first()

    if not setting:
        return jsonify({"hero_image": ""}), 200

    return jsonify(setting.to_dict()), 200


@app.route('/api/settings', methods=['PUT'])
@jwt_required()
def update_settings():
    data = request.get_json() or {}
    hero_image = data.get("hero_image", "")

    setting = SiteSetting.query.first()

    if not setting:
        setting = SiteSetting(hero_image=hero_image)
        db.session.add(setting)
    else:
        setting.hero_image = hero_image

    db.session.commit()

    return jsonify(setting.to_dict()), 200

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_image():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.email) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    if "file" not in request.files:
        return jsonify({"error": "Ingen bildefil mottatt"}), 400

    file = request.files["file"]

    if not file or file.filename == "":
        return jsonify({"error": "Ingen bildefil valgt"}), 400

    try:
        result = cloudinary.uploader.upload(
            file,
            folder="skyteduellene"
        )

        return jsonify({
            "url": result["secure_url"]
        }), 200

    except Exception as e:
        print("Cloudinary upload error:", e)
        return jsonify({"error": "Kunne ikke laste opp bildet"}), 500
# ==================== Database initialization ====================

@app.before_request
def create_tables():
    db.create_all()

    finished_duels = Duel.query.filter_by(status="finished").all()

    changed = False

    for duel in finished_duels:
        correct_tips = Tip.query.filter_by(
            duel_id=duel.id,
            pick=duel.outcome
        ).all()

        for tip in correct_tips:
            existing = PointRecord.query.filter_by(
                user_id=tip.user_id,
                duel_id=duel.id
            ).first()

            if not existing:
                point_record = PointRecord(
                    user_id=tip.user_id,
                    duel_id=duel.id,
                    points=1,
                    shooter1=duel.shooter1,
                    shooter2=duel.shooter2,
                    active=True
                )
                db.session.add(point_record)
                changed = True

    if changed:
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=False)
