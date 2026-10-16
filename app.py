import cloudinary
import cloudinary.uploader
import os
import json
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
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

ADMIN_USERNAMES = {
    "Sverre Hårstad"
}

def get_role(username):
    if username in ADMIN_USERNAMES:
        return "admin"

    user = User.query.filter_by(username=username).first()
    return user.role if user and user.role in ["admin", "user"] else "user"
# ==================== Models ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="user", nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        latest_reset = get_latest_reset("global", "all")

        point_query = PointRecord.query.filter_by(
            user_id=self.id,
            active=True
        )

        if latest_reset:
            point_query = point_query.filter(
                PointRecord.created_at > latest_reset
            )

        points = sum(
            record.points
            for record in point_query.all()
        )

        return {
            'id': self.id,
            'username': self.username,
            'role': get_role(self.username),
            'is_seed_admin': self.username in ADMIN_USERNAMES,
            'points': points,
            'created_at': self.created_at.isoformat()
        }
class Duel(db.Model):
    __tablename__ = 'duels'

    id = db.Column(db.Integer, primary_key=True)
    shooter1 = db.Column(db.String(120), nullable=False)
    shooter2 = db.Column(db.String(120), nullable=False)
    shooter1_club = db.Column(db.String(120), default="")
    shooter2_club = db.Column(db.String(120), default="")
    shooter1_class = db.Column(db.String(30), default="")
    shooter2_class = db.Column(db.String(30), default="")
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
    external_source = db.Column(db.String(20), default="")
    external_event_url = db.Column(db.Text, default="")
    external_event_id = db.Column(db.String(120), default="")
    external_discipline_id = db.Column(db.String(120), default="")
    external_class_id = db.Column(db.String(120), default="")
    is_deleted = db.Column(db.Boolean, default=False)

    def to_dict(self):
        tip_counts = {
    "1": Tip.query.filter_by(duel_id=self.id, pick="1").count(),
    "X": Tip.query.filter_by(duel_id=self.id, pick="X").count(),
    "2": Tip.query.filter_by(duel_id=self.id, pick="2").count()
}
        tournament_links = DuelTournament.query.filter_by(
            duel_id=self.id
        ).all()

        tournament_ids = [
            link.tournament_id for link in tournament_links
        ]
        return {
            "id": self.id,
            "tip_counts": tip_counts,
            "shooter1": self.shooter1,
            "shooter2": self.shooter2,
            "shooter1_club": self.shooter1_club,
            "shooter2_club": self.shooter2_club,
            "shooter1_class": self.shooter1_class,
            "shooter2_class": self.shooter2_class,
            "shooter1_img": self.shooter1_img,
            "shooter2_img": self.shooter2_img,
            "discipline": self.discipline,
            "venue": self.venue,
            "start_time": self.start_time,
            "start_at": self.start_at,
            "tournament_id": self.tournament_id,
            "tournament_ids": tournament_ids,
            "tournament_name": (
    Tournament.query.get(int(self.tournament_id)).name
    if self.tournament_id and Tournament.query.get(int(self.tournament_id))
    else ""
),
            "status": self.status,
            "outcome": self.outcome,
            "score1": self.score1,
            "score2": self.score2,
            "external_source": self.external_source,
            "external_event_url": self.external_event_url,
            "external_event_id": self.external_event_id,
            "external_discipline_id": self.external_discipline_id,
            "external_class_id": self.external_class_id
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

class ScoreReset(db.Model):
    __tablename__ = 'score_resets'

    id = db.Column(db.Integer, primary_key=True)
    scope_type = db.Column(db.String(30), nullable=False)
    scope_key = db.Column(db.String(120), nullable=False)
    reset_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
class Tournament(db.Model):
    __tablename__ = 'tournaments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    season = db.Column(db.String(50), default="")

    def to_dict(self):
        duel_count = (
    DuelTournament.query
    .join(Duel, DuelTournament.duel_id == Duel.id)
    .filter(
        DuelTournament.tournament_id == self.id,
        Duel.is_deleted == False
    )
    .count()
)

        access = TournamentAccess.query.filter_by(
            tournament_id=self.id
        ).first()

        return {
            "id": self.id,
            "name": self.name,
            "season": self.season,
            "duel_count": duel_count,
            "is_private": access.is_private if access else False
        }

class TournamentAccess(db.Model):
    __tablename__ = 'tournament_access'

    tournament_id = db.Column(db.Integer, primary_key=True)
    is_private = db.Column(db.Boolean, default=False)
    access_code_hash = db.Column(db.String(255), default="")


class TournamentMember(db.Model):
    __tablename__ = 'tournament_members'

    tournament_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, primary_key=True)
    joined_at = db.Column(db.DateTime, default=db.func.now())
class SiteSetting(db.Model):
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    hero_image = db.Column(db.Text, default="")

    def to_dict(self):
        return {
            "hero_image": self.hero_image
        }


class ExternalResultSuggestion(db.Model):
    __tablename__ = 'external_result_suggestions'

    id = db.Column(db.Integer, primary_key=True)
    duel_id = db.Column(db.Integer, nullable=False, index=True)
    source = db.Column(db.String(20), nullable=False)
    source_url = db.Column(db.Text, default="")
    event_url = db.Column(db.Text, default="")
    external_event_id = db.Column(db.String(120), default="")
    external_discipline_id = db.Column(db.String(120), default="")
    external_class_id = db.Column(db.String(120), default="")
    suggested_shooter1_name = db.Column(db.String(120), default="")
    suggested_shooter2_name = db.Column(db.String(120), default="")
    suggested_score1 = db.Column(db.String(50), default="")
    suggested_score2 = db.Column(db.String(50), default="")
    suggested_outcome = db.Column(db.String(20), default="")
    raw_source_data = db.Column(db.Text, default="")
    normalized_source_data = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="waiting", nullable=False)
    status_reason = db.Column(db.String(120), default="")
    rejection_note = db.Column(db.Text, default="")
    fetched_at = db.Column(db.DateTime, nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    approved_by_user_id = db.Column(db.Integer, nullable=True)
    rejected_by_user_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.now(),
        onupdate=db.func.now()
    )

    def to_dict(self):
        def parse_json_blob(value):
            if not value:
                return None
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return None

        duel = Duel.query.get(self.duel_id)
        return {
            "id": self.id,
            "duel_id": self.duel_id,
            "duel": duel.to_dict() if duel else None,
            "source": self.source,
            "source_url": self.source_url,
            "event_url": self.event_url,
            "external_event_id": self.external_event_id,
            "external_discipline_id": self.external_discipline_id,
            "external_class_id": self.external_class_id,
            "suggested_shooter1_name": self.suggested_shooter1_name,
            "suggested_shooter2_name": self.suggested_shooter2_name,
            "suggested_score1": self.suggested_score1,
            "suggested_score2": self.suggested_score2,
            "suggested_outcome": self.suggested_outcome,
            "raw_source_data": parse_json_blob(self.raw_source_data),
            "normalized_source_data": parse_json_blob(self.normalized_source_data),
            "status": self.status,
            "status_reason": self.status_reason,
            "rejection_note": self.rejection_note,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "approved_by_user_id": self.approved_by_user_id,
            "rejected_by_user_id": self.rejected_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
# ==================== Routes ====================
def get_latest_reset(scope_type, scope_key):
    reset = ScoreReset.query.filter_by(
        scope_type=scope_type,
        scope_key=str(scope_key)
    ).order_by(ScoreReset.reset_at.desc()).first()

    return reset.reset_at if reset else None


ALLOWED_EXTERNAL_SOURCES = {"mittdfs", "megalink"}
SUGGESTION_STATUS_VALUES = {
    "waiting",
    "suggested",
    "approved",
    "rejected",
    "needs_review"
}


def _safe_json_dumps(payload):
    if payload is None:
        return ""
    try:
        return json.dumps(payload, ensure_ascii=False)
    except (TypeError, ValueError):
        return ""


def _safe_iso_datetime(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _extract_outcome(score1, score2):
    try:
        left = float(score1)
        right = float(score2)
    except (TypeError, ValueError):
        return ""
    if left > right:
        return "1"
    if right > left:
        return "2"
    return "X"


def _is_admin_user(user):
    return user is not None and get_role(user.username) == "admin"


def _validate_source_url(url):
    if not url:
        return True
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _get_admin_user_or_error():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not _is_admin_user(user):
        return None, (jsonify({"error": "Ingen tilgang"}), 403)
    return user, None


def _apply_duel_result(duel, outcome, score1="", score2=""):
    duel.outcome = outcome
    duel.score1 = str(score1)
    duel.score2 = str(score2)
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


class ExternalResultSuggestionService:
    def __init__(self):
        self.timeout_seconds = float(
            os.getenv("EXTERNAL_RESULTS_TIMEOUT_SECONDS", "8")
        )
        self.mittdfs_base_url = os.getenv(
            "MITTDFS_RESULTS_BASE_URL",
            "https://mittdfs.no/resultater/"
        )
        self.megalink_base_url = os.getenv(
            "MEGALINK_RESULTS_BASE_URL",
            "https://res.megalink.no/"
        )

    def fetch_suggestion(self, duel):
        source = (duel.external_source or "").strip().lower()
        if source not in ALLOWED_EXTERNAL_SOURCES:
            return {
                "status": "needs_review",
                "status_reason": "missing_source",
                "message": "Duellen mangler gyldig ekstern kilde."
            }

        event_url = (duel.external_event_url or "").strip()
        if not event_url:
            return {
                "status": "waiting",
                "status_reason": "missing_event_url",
                "message": "Duellen mangler kobling til ekstern resultat-URL."
            }

        if not _validate_source_url(event_url):
            return {
                "status": "needs_review",
                "status_reason": "invalid_event_url",
                "message": "Resultat-URL er ugyldig."
            }

        if app.config.get("TESTING"):
            return {
                "status": "needs_review",
                "status_reason": "source_unavailable",
                "message": "Eksterne oppslag er deaktivert i testmodus."
            }

        if source == "mittdfs":
            return self._fetch_mittdfs(duel, event_url)
        return self._fetch_megalink(duel, event_url)

    def _fetch_url(self, url):
        request_obj = Request(
            url,
            headers={"User-Agent": "Skyteduellene/1.0"}
        )
        with urlopen(request_obj, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="ignore")
        return body

    def _fetch_mittdfs(self, duel, event_url):
        return self._conservative_fetch("mittdfs", duel, event_url)

    def _fetch_megalink(self, duel, event_url):
        return self._conservative_fetch("megalink", duel, event_url)

    def _conservative_fetch(self, source, duel, event_url):
        try:
            body = self._fetch_url(event_url)
        except (HTTPError, URLError, TimeoutError, ValueError):
            return {
                "status": "needs_review",
                "status_reason": "source_unavailable",
                "message": f"{source} kunne ikke leses akkurat nå."
            }

        return {
            "status": "needs_review",
            "status_reason": "parser_unavailable",
            "message": f"Ingen trygg parser tilgjengelig for {source} ennå.",
            "raw_source_data": {
                "event_url": event_url,
                "body_preview": body[:800]
            },
            "normalized_source_data": {
                "source": source,
                "event_url": event_url,
                "duel_id": duel.id
            }
        }


external_result_service = ExternalResultSuggestionService()
@app.route('/')
def hello():
    return jsonify({"message": "Skyteduellene API kjører! 🎯"})

@app.route('/api/duels', methods=['GET'])
def get_duels():
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()

    user_id = int(identity) if identity else None
    user = User.query.get(user_id) if user_id else None
    is_admin = user is not None and get_role(user.username) == "admin"

    if is_admin:
        duels = Duel.query.filter(
            Duel.is_deleted == False
        ).order_by(Duel.id.desc()).all()
    else:
        duels = Duel.query.filter(
            Duel.is_deleted == False,
            Duel.status != "finished"
        ).order_by(Duel.id.desc()).all()

    visible_duels = []

    for duel in duels:
        links = DuelTournament.query.filter_by(
            duel_id=duel.id
        ).all()

        private_tournament_ids = []

        for link in links:
            access = TournamentAccess.query.filter_by(
                tournament_id=link.tournament_id
            ).first()

            if access and access.is_private:
                private_tournament_ids.append(link.tournament_id)

        if not private_tournament_ids:
            visible_duels.append(duel)
            continue

        if is_admin:
            visible_duels.append(duel)
            continue

        if user_id:
            membership = TournamentMember.query.filter(
                TournamentMember.user_id == user_id,
                TournamentMember.tournament_id.in_(private_tournament_ids)
            ).first()

            if membership:
                visible_duels.append(duel)

    return jsonify([duel.to_dict() for duel in visible_duels])
@app.route('/api/duels/<int:duel_id>', methods=['GET'])
def get_duel(duel_id):
    duel = Duel.query.get(duel_id)

    if not duel or duel.is_deleted:
        return jsonify({"error": "Duell ikke funnet"}), 404

    links = DuelTournament.query.filter_by(duel_id=duel.id).all()

    private_tournament_ids = []

    for link in links:
        access = TournamentAccess.query.filter_by(
            tournament_id=link.tournament_id
        ).first()

        if access and access.is_private:
            private_tournament_ids.append(link.tournament_id)

    if private_tournament_ids:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()

        if not identity:
            return jsonify({"error": "Ingen tilgang"}), 403

        user_id = int(identity)
        user = User.query.get(user_id)

        is_admin = user is not None and get_role(user.username) == "admin"

        membership = TournamentMember.query.filter(
            TournamentMember.user_id == user_id,
            TournamentMember.tournament_id.in_(private_tournament_ids)
        ).first()

        if not is_admin and not membership:
            return jsonify({"error": "Ingen tilgang"}), 403

    return jsonify(duel.to_dict()), 200

@app.route('/api/duels/<int:duel_id>', methods=['DELETE'])
@jwt_required()
def delete_duel(duel_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403
    duel = Duel.query.get(duel_id)

    if not duel:
        return jsonify({"error": "Duell ikke funnet"}), 404

    duel.is_deleted = True
    db.session.commit()

    return jsonify({"success": True}), 200


@app.route('/api/duels/<int:duel_id>', methods=['PATCH'])
@jwt_required()
def update_duel(duel_id):
    user, error_response = _get_admin_user_or_error()
    if error_response:
        return error_response

    duel = Duel.query.get(duel_id)
    if not duel or duel.is_deleted:
        return jsonify({"error": "Duell ikke funnet"}), 404

    data = request.get_json() or {}

    external_source = data.get("external_source", duel.external_source)
    if external_source is None:
        external_source = ""
    external_source = str(external_source).strip().lower()

    external_event_url = data.get("external_event_url", duel.external_event_url)
    if external_event_url is None:
        external_event_url = ""
    external_event_url = str(external_event_url).strip()

    if external_source and external_source not in ALLOWED_EXTERNAL_SOURCES:
        return jsonify({"error": "Ugyldig ekstern kilde"}), 400

    if external_event_url and not _validate_source_url(external_event_url):
        return jsonify({"error": "Ugyldig ekstern resultat-URL"}), 400

    editable_fields = [
        "shooter1_img",
        "shooter2_img",
        "shooter1",
        "shooter2",
        "shooter1_club",
        "shooter2_club",
        "shooter1_class",
        "shooter2_class",
        "discipline",
        "venue",
        "start_time",
        "start_at",
        "external_event_id",
        "external_discipline_id",
        "external_class_id"
    ]

    for field in editable_fields:
        if field in data:
            value = data.get(field)
            setattr(duel, field, "" if value is None else str(value))

    duel.external_source = external_source
    duel.external_event_url = external_event_url

    db.session.commit()
    return jsonify(duel.to_dict()), 200
    
@app.route('/api/tournaments/<int:tid>', methods=['DELETE'])
@jwt_required()
def delete_tournament(tid):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403
    tournament = Tournament.query.get(tid)

    if not tournament:
        return jsonify({"error": "Serie ikke funnet"}), 404

    DuelTournament.query.filter_by(
        tournament_id=tid
    ).delete()

    TournamentMember.query.filter_by(
        tournament_id=tid
    ).delete()

    TournamentAccess.query.filter_by(
        tournament_id=tid
    ).delete()

    db.session.delete(tournament)
    db.session.commit()

    return jsonify({"success": True}), 200
@app.route('/api/duels', methods=['POST', 'OPTIONS'])
def create_duel():
    if request.method == 'OPTIONS':
        return '', 204
        
    verify_jwt_in_request()

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    data = request.get_json() or {}

    if not data.get("shooter1") or not data.get("shooter2"):
        return jsonify({"error": "Begge navnene må fylles ut"}), 400

    tournament_ids = data.get("tournament_ids")

    if not isinstance(tournament_ids, list):
        old_tournament_id = data.get("tournament_id", "")
        tournament_ids = [old_tournament_id] if old_tournament_id else []

    legacy_tournament_id = str(tournament_ids[0]) if tournament_ids else ""
    external_source = str(data.get("external_source", "")).strip().lower()
    external_event_url = str(data.get("external_event_url", "")).strip()
    external_event_id = str(data.get("external_event_id", "")).strip()
    external_discipline_id = str(data.get("external_discipline_id", "")).strip()
    external_class_id = str(data.get("external_class_id", "")).strip()

    if external_source and external_source not in ALLOWED_EXTERNAL_SOURCES:
        return jsonify({"error": "Ugyldig ekstern kilde"}), 400

    if external_event_url and not _validate_source_url(external_event_url):
        return jsonify({"error": "Ugyldig ekstern resultat-URL"}), 400

    duel = Duel(
        shooter1=data.get("shooter1", ""),
        shooter2=data.get("shooter2", ""),
        shooter1_club=data.get("shooter1_club", ""),
        shooter2_club=data.get("shooter2_club", ""),
        shooter1_class=data.get("shooter1_class", ""),
        shooter2_class=data.get("shooter2_class", ""),
        shooter1_img=data.get("shooter1_img", ""),
        shooter2_img=data.get("shooter2_img", ""),
        discipline=data.get("discipline", ""),
        venue=data.get("venue", ""),
        start_time=data.get("start_time", ""),
        start_at=data.get("start_at", ""),
        tournament_id=legacy_tournament_id,
        external_source=external_source,
        external_event_url=external_event_url,
        external_event_id=external_event_id,
        external_discipline_id=external_discipline_id,
        external_class_id=external_class_id
    )

    db.session.add(duel)
    db.session.flush()

    for tournament_id in tournament_ids:
        try:
            tournament_id = int(tournament_id)
        except (TypeError, ValueError):
            continue

        db.session.add(DuelTournament(
            duel_id=duel.id,
            tournament_id=tournament_id
        ))

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
    links = DuelTournament.query.filter_by(duel_id=duel.id).all()

    private_tournament_ids = []

    for link in links:
        access = TournamentAccess.query.filter_by(
            tournament_id=link.tournament_id
        ).first()

        if access and access.is_private:
            private_tournament_ids.append(link.tournament_id)

    if private_tournament_ids:
        user = User.query.get(user_id)
        is_admin = user is not None and get_role(user.username) == "admin"

        membership = TournamentMember.query.filter(
            TournamentMember.user_id == user_id,
            TournamentMember.tournament_id.in_(private_tournament_ids)
        ).first()

        if not is_admin and not membership:
            return jsonify({"error": "Ingen tilgang"}), 403

    if duel.status == "finished":
        return jsonify({"error": "Duellen er avsluttet"}), 400

    if duel.start_at:
        try:
            start_time = datetime.fromisoformat(duel.start_at)

            if start_time.tzinfo is None:
                start_time = start_time.replace(
                    tzinfo=ZoneInfo("Europe/Oslo")
                )

            if datetime.now(ZoneInfo("Europe/Oslo")) >= start_time:
                return jsonify({
                    "error": "Tippefristen for denne duellen har gått ut"
                }), 400

        except ValueError:
            pass

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
@app.route('/api/duels/<int:duel_id>/tip', methods=['DELETE'])
@jwt_required()
def delete_own_tip(duel_id):
    user_id = int(get_jwt_identity())

    duel = Duel.query.get(duel_id)
    if not duel or duel.is_deleted:
        return jsonify({"error": "Duell ikke funnet"}), 404
    links = DuelTournament.query.filter_by(duel_id=duel.id).all()

    private_tournament_ids = []

    for link in links:
        access = TournamentAccess.query.filter_by(
            tournament_id=link.tournament_id
        ).first()

        if access and access.is_private:
            private_tournament_ids.append(link.tournament_id)

    if private_tournament_ids:
        user = User.query.get(user_id)
        is_admin = user is not None and get_role(user.username) == "admin"

        membership = TournamentMember.query.filter(
            TournamentMember.user_id == user_id,
            TournamentMember.tournament_id.in_(private_tournament_ids)
        ).first()

        if not is_admin and not membership:
            return jsonify({"error": "Ingen tilgang"}), 403

    if duel.status == "finished":
        return jsonify({"error": "Duellen er avsluttet"}), 400

    if duel.start_at:
        try:
            start_time = datetime.fromisoformat(duel.start_at)

            if start_time.tzinfo is None:
                start_time = start_time.replace(
                    tzinfo=ZoneInfo("Europe/Oslo")
                )

            if datetime.now(ZoneInfo("Europe/Oslo")) >= start_time:
                return jsonify({
                    "error": "Tippefristen for denne duellen har gått ut"
                }), 400
        except ValueError:
            pass

    tip = Tip.query.filter_by(
        user_id=user_id,
        duel_id=duel_id
    ).first()

    if not tip:
        return jsonify({"error": "Du har ikke tippet på denne duellen"}), 404

    db.session.delete(tip)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Tipset er slettet"
    }), 200
@app.route('/api/duels/<int:duel_id>/result', methods=['POST', 'OPTIONS'])
@jwt_required()
def save_duel_result(duel_id):
    if request.method == 'OPTIONS':
        return '', 204
    user, error_response = _get_admin_user_or_error()
    if error_response:
        return error_response

    data = request.get_json() or {}

    duel = Duel.query.get(duel_id)
    if not duel:
        return jsonify({"error": "Duell ikke funnet"}), 404

    outcome = data.get("outcome")

    if outcome not in ["1", "X", "2"]:
        return jsonify({"error": "Ugyldig resultat"}), 400

    _apply_duel_result(
        duel,
        outcome=outcome,
        score1=data.get("score1", ""),
        score2=data.get("score2", "")
    )

    db.session.commit()

    return jsonify(duel.to_dict()), 200


@app.route('/api/admin/result-suggestions', methods=['GET'])
@jwt_required()
def list_result_suggestions():
    user, error_response = _get_admin_user_or_error()
    if error_response:
        return error_response

    status_param = str(request.args.get("status", "")).strip()
    duel_id_param = str(request.args.get("duel_id", "")).strip()

    query = ExternalResultSuggestion.query.order_by(
        ExternalResultSuggestion.created_at.desc()
    )

    if status_param:
        statuses = [
            status.strip() for status in status_param.split(",")
            if status.strip()
        ]
    else:
        statuses = ["waiting", "suggested", "needs_review"]

    valid_statuses = [
        status for status in statuses
        if status in SUGGESTION_STATUS_VALUES
    ]

    if valid_statuses:
        query = query.filter(ExternalResultSuggestion.status.in_(valid_statuses))

    if duel_id_param:
        try:
            duel_id = int(duel_id_param)
        except ValueError:
            return jsonify({"error": "Ugyldig duel_id"}), 400
        query = query.filter_by(duel_id=duel_id)

    suggestions = query.limit(200).all()
    counts = {
        "waiting": 0,
        "suggested": 0,
        "approved": 0,
        "rejected": 0,
        "needs_review": 0
    }

    all_counts = db.session.query(
        ExternalResultSuggestion.status,
        db.func.count(ExternalResultSuggestion.id)
    ).group_by(ExternalResultSuggestion.status).all()

    for status, count in all_counts:
        if status in counts:
            counts[status] = count

    return jsonify({
        "counts": counts,
        "items": [item.to_dict() for item in suggestions]
    }), 200


@app.route('/api/admin/result-suggestions/<int:suggestion_id>', methods=['GET'])
@jwt_required()
def get_result_suggestion(suggestion_id):
    user, error_response = _get_admin_user_or_error()
    if error_response:
        return error_response

    suggestion = ExternalResultSuggestion.query.get(suggestion_id)
    if not suggestion:
        return jsonify({"error": "Forslaget ble ikke funnet"}), 404
    return jsonify(suggestion.to_dict()), 200


@app.route('/api/admin/duels/<int:duel_id>/result-suggestions/fetch', methods=['POST'])
@jwt_required()
def fetch_result_suggestion_for_duel(duel_id):
    user, error_response = _get_admin_user_or_error()
    if error_response:
        return error_response

    duel = Duel.query.get(duel_id)
    if not duel or duel.is_deleted:
        return jsonify({"error": "Duell ikke funnet"}), 404

    service_result = external_result_service.fetch_suggestion(duel)
    status = service_result.get("status", "needs_review")
    if status not in SUGGESTION_STATUS_VALUES:
        status = "needs_review"

    suggestion = ExternalResultSuggestion.query.filter_by(
        duel_id=duel.id
    ).order_by(ExternalResultSuggestion.created_at.desc()).first()

    if not suggestion:
        suggestion = ExternalResultSuggestion(
            duel_id=duel.id,
            source=(duel.external_source or "").strip().lower() or "mittdfs"
        )
        db.session.add(suggestion)

    suggestion.source = (duel.external_source or suggestion.source or "").strip().lower()
    suggestion.source_url = service_result.get("source_url") or duel.external_event_url or ""
    suggestion.event_url = service_result.get("event_url") or duel.external_event_url or ""
    suggestion.external_event_id = service_result.get("external_event_id") or duel.external_event_id or ""
    suggestion.external_discipline_id = service_result.get("external_discipline_id") or duel.external_discipline_id or ""
    suggestion.external_class_id = service_result.get("external_class_id") or duel.external_class_id or ""
    suggestion.suggested_shooter1_name = service_result.get("suggested_shooter1_name") or duel.shooter1
    suggestion.suggested_shooter2_name = service_result.get("suggested_shooter2_name") or duel.shooter2
    suggestion.suggested_score1 = str(service_result.get("suggested_score1", ""))
    suggestion.suggested_score2 = str(service_result.get("suggested_score2", ""))
    suggestion.suggested_outcome = service_result.get("suggested_outcome") or _extract_outcome(
        suggestion.suggested_score1,
        suggestion.suggested_score2
    )
    suggestion.status = status
    suggestion.status_reason = service_result.get("status_reason", "")
    suggestion.raw_source_data = _safe_json_dumps(service_result.get("raw_source_data"))
    suggestion.normalized_source_data = _safe_json_dumps(service_result.get("normalized_source_data"))
    suggestion.fetched_at = datetime.utcnow()

    if suggestion.status in {"waiting", "suggested", "needs_review"}:
        suggestion.rejection_note = ""
        suggestion.rejected_at = None
        suggestion.rejected_by_user_id = None

    db.session.commit()

    response = suggestion.to_dict()
    response["message"] = service_result.get("message", "")
    return jsonify(response), 200


@app.route('/api/admin/duels/<int:duel_id>/result-suggestions/<int:suggestion_id>/approve', methods=['POST'])
@jwt_required()
def approve_result_suggestion(duel_id, suggestion_id):
    user, error_response = _get_admin_user_or_error()
    if error_response:
        return error_response

    duel = Duel.query.get(duel_id)
    if not duel or duel.is_deleted:
        return jsonify({"error": "Duell ikke funnet"}), 404

    suggestion = ExternalResultSuggestion.query.get(suggestion_id)
    if not suggestion:
        return jsonify({"error": "Forslaget ble ikke funnet"}), 404

    if suggestion.duel_id != duel.id:
        return jsonify({"error": "Forslaget tilhører ikke valgt duell"}), 400

    data = request.get_json() or {}
    allow_reprocess = bool(data.get("allow_reprocess", False))

    if suggestion.status in {"approved", "rejected"} and not allow_reprocess:
        return jsonify({"error": "Forslaget er allerede behandlet"}), 400

    score1 = str(data.get("score1", suggestion.suggested_score1 or "")).strip()
    score2 = str(data.get("score2", suggestion.suggested_score2 or "")).strip()
    outcome = str(data.get("outcome", suggestion.suggested_outcome or "")).strip().upper()

    if outcome not in {"1", "X", "2"}:
        outcome = _extract_outcome(score1, score2)

    if outcome not in {"1", "X", "2"}:
        return jsonify({
            "error": "Kunne ikke bestemme utfall. Angi resultat (1/X/2) eller gyldige scorer."
        }), 400

    _apply_duel_result(
        duel,
        outcome=outcome,
        score1=score1,
        score2=score2
    )

    suggestion.suggested_score1 = score1
    suggestion.suggested_score2 = score2
    suggestion.suggested_outcome = outcome
    suggestion.status = "approved"
    suggestion.approved_at = datetime.utcnow()
    suggestion.approved_by_user_id = user.id
    suggestion.rejection_note = ""
    suggestion.rejected_at = None
    suggestion.rejected_by_user_id = None

    db.session.commit()

    return jsonify({
        "duel": duel.to_dict(),
        "suggestion": suggestion.to_dict()
    }), 200


@app.route('/api/admin/duels/<int:duel_id>/result-suggestions/<int:suggestion_id>/reject', methods=['POST'])
@jwt_required()
def reject_result_suggestion(duel_id, suggestion_id):
    user, error_response = _get_admin_user_or_error()
    if error_response:
        return error_response

    duel = Duel.query.get(duel_id)
    if not duel or duel.is_deleted:
        return jsonify({"error": "Duell ikke funnet"}), 404

    suggestion = ExternalResultSuggestion.query.get(suggestion_id)
    if not suggestion:
        return jsonify({"error": "Forslaget ble ikke funnet"}), 404

    if suggestion.duel_id != duel.id:
        return jsonify({"error": "Forslaget tilhører ikke valgt duell"}), 400

    if suggestion.status == "approved":
        return jsonify({"error": "Godkjent forslag kan ikke avvises uten ny behandling"}), 400

    data = request.get_json() or {}
    suggestion.status = "rejected"
    suggestion.rejection_note = str(data.get("note", "")).strip()
    suggestion.rejected_at = datetime.utcnow()
    suggestion.rejected_by_user_id = user.id

    db.session.commit()
    return jsonify(suggestion.to_dict()), 200


@app.route('/api/duels/<int:duel_id>/remove-points', methods=['POST'])
@jwt_required()
def remove_duel_points(duel_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
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

    tips = (
    Tip.query
    .join(Duel, Tip.duel_id == Duel.id)
    .filter(
        Tip.user_id == user_id,
        Duel.is_deleted == False
    )
    .all()
)

    return jsonify([tip.to_dict() for tip in tips]), 200

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    users = User.query.all()
    rows = []

    for user in users:
        tips = (
            Tip.query
            .join(Duel, Tip.duel_id == Duel.id)
            .filter(
                Tip.user_id == user.id,
                Duel.is_deleted == False
            )
            .all()
        )

        total_tips = len(tips)

        correct = 0

        for tip in tips:
            duel = Duel.query.get(tip.duel_id)

            if duel and duel.status == "finished" and tip.pick == duel.outcome:
                correct += 1
    

        latest_reset = get_latest_reset("global", "all")

        point_query = PointRecord.query.filter_by(
            user_id=user.id,
            active=True
        )

        if latest_reset:
            point_query = point_query.filter(
                PointRecord.created_at > latest_reset
            )

        point_records = point_query.all()
        points = sum(record.points for record in point_records)

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
@app.route('/api/admin/users', methods=['GET'])
@jwt_required()
def get_admin_users():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    users = User.query.order_by(User.created_at.asc()).all()

    return jsonify([user.to_dict() for user in users]), 200
@app.route('/api/admin/users/<int:target_user_id>/role', methods=['POST'])
@jwt_required()
def set_user_role(target_user_id):
    admin_id = int(get_jwt_identity())
    admin = User.query.get(admin_id)

    if not admin or get_role(admin.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    target_user = User.query.get(target_user_id)

    if not target_user:
        return jsonify({"error": "Bruker ikke funnet"}), 404

    if target_user.username in ADMIN_USERNAMES:
        return jsonify({"error": "Hovedadmin kan ikke endres"}), 400

    data = request.get_json() or {}
    role = data.get("role")

    if role not in ["admin", "user"]:
        return jsonify({"error": "Ugyldig rolle"}), 400

    target_user.role = role
    db.session.commit()

    return jsonify(target_user.to_dict()), 200
@app.route('/api/admin/users/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(target_user_id):
    admin_id = int(get_jwt_identity())
    admin = User.query.get(admin_id)

    if not admin or get_role(admin.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    if target_user_id == admin_id:
        return jsonify({"error": "Du kan ikke slette din egen admin-konto"}), 400

    target_user = User.query.get(target_user_id)

    if not target_user:
        return jsonify({"error": "Bruker ikke funnet"}), 404

    if get_role(target_user.username) == "admin":
        return jsonify({"error": "Admin-kontoer kan ikke slettes"}), 400

    Tip.query.filter_by(user_id=target_user_id).delete()
    PointRecord.query.filter_by(user_id=target_user_id).delete()
    TournamentMember.query.filter_by(user_id=target_user_id).delete()

    db.session.delete(target_user)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Brukeren er slettet"
    }), 200
@app.route('/api/tournaments', methods=['GET'])
def get_tournaments():
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()

    user_id = int(identity) if identity else None
    user = User.query.get(user_id) if user_id else None
    is_admin = user is not None and get_role(user.username) == "admin"

    tournaments = Tournament.query.order_by(Tournament.id.desc()).all()
    visible_tournaments = []

    for tournament in tournaments:
        access = TournamentAccess.query.filter_by(
            tournament_id=tournament.id
        ).first()

        if not access or not access.is_private:
            visible_tournaments.append(tournament)
            continue

        if is_admin:
            visible_tournaments.append(tournament)
            continue

        if user_id:
            membership = TournamentMember.query.filter_by(
                tournament_id=tournament.id,
                user_id=user_id
            ).first()

            if membership:
                visible_tournaments.append(tournament)

    return jsonify([t.to_dict() for t in visible_tournaments]), 200


@app.route('/api/tournaments', methods=['POST', 'OPTIONS'])
@jwt_required()
def create_tournament():
    if request.method == 'OPTIONS':
        return '', 204
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    season = data.get("season", "").strip()
    is_private = bool(data.get("is_private", False))
    access_code = str(data.get("access_code", "")).strip()

    if not name:
        return jsonify({"error": "Navn på serie/sesong mangler"}), 400

    if is_private and not access_code:
        return jsonify({"error": "Privat serie må ha en kode"}), 400

    tournament = Tournament(
        name=name,
        season=season
    )

    db.session.add(tournament)
    db.session.flush()

    access = TournamentAccess(
        tournament_id=tournament.id,
        is_private=is_private,
        access_code_hash=(
            generate_password_hash(access_code)
            if is_private
            else ""
        )
    )

    db.session.add(access)
    db.session.commit()

    return jsonify(tournament.to_dict()), 201

@app.route('/api/tournaments/<int:tid>/join', methods=['POST'])
@jwt_required()
def join_tournament(tid):
    user_id = int(get_jwt_identity())

    tournament = Tournament.query.get(tid)
    if not tournament:
        return jsonify({"error": "Serie ikke funnet"}), 404

    access = TournamentAccess.query.filter_by(
        tournament_id=tid
    ).first()

    if not access or not access.is_private:
        return jsonify({"error": "Denne serien er ikke privat"}), 400

    existing_member = TournamentMember.query.filter_by(
        tournament_id=tid,
        user_id=user_id
    ).first()

    if existing_member:
        return jsonify({
            "success": True,
            "message": "Du er allerede med i serien"
        }), 200

    data = request.get_json() or {}
    access_code = str(data.get("access_code", "")).strip()

    if not access_code or not check_password_hash(
        access.access_code_hash,
        access_code
    ):
        return jsonify({"error": "Feil kode"}), 403

    member = TournamentMember(
        tournament_id=tid,
        user_id=user_id
    )

    db.session.add(member)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Du er nå med i serien"
    }), 200
@app.route('/api/tournaments/<int:tid>', methods=['GET'])
def get_tournament(tid):
    tournament = Tournament.query.get(tid)

    if not tournament:
        return jsonify({"error": "Fant ikke serien"}), 404

    access = TournamentAccess.query.filter_by(
        tournament_id=tid
    ).first()

    if access and access.is_private:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()

        if not identity:
            return jsonify({
                "error": "Du må være logget inn for å se denne serien"
            }), 401

        user_id = int(identity)
        user = User.query.get(user_id)

        is_admin = (
            user is not None
            and get_role(user.username) == "admin"
        )

        member = TournamentMember.query.filter_by(
            tournament_id=tid,
            user_id=user_id
        ).first()

        if not is_admin and not member:
            return jsonify({
                "error": "Du må bli med i serien med kode først"
            }), 403
    links = DuelTournament.query.filter_by(
        tournament_id=tid
    ).all()

    duel_ids = [link.duel_id for link in links]

    all_duels = Duel.query.filter(
        Duel.id.in_(duel_ids)
    ).order_by(Duel.id.desc()).all() if duel_ids else []

    visible_duels = [
        duel for duel in all_duels
        if not duel.is_deleted
    ]

    standings = []

    users = User.query.all()

    for user in users:
        tips = Tip.query.filter(
            Tip.user_id == user.id,
            Tip.duel_id.in_(duel_ids)
        ).all() if duel_ids else []

        if not tips:
            continue
        tournament_reset = get_latest_reset("tournament", tid)
        season_reset = get_latest_reset("season", tournament.season)

        reset_times = [
            reset_time
            for reset_time in [tournament_reset, season_reset]
            if reset_time
        ]

        latest_reset = max(reset_times) if reset_times else None
        point_records = []

        if duel_ids:
            point_query = PointRecord.query.filter(
                PointRecord.user_id == user.id,
                PointRecord.duel_id.in_(duel_ids),
                PointRecord.active == True
            )

            if latest_reset:
                point_query = point_query.filter(
                    PointRecord.created_at > latest_reset
                )

            point_records = point_query.all()

        correct = sum(record.points for record in point_records)

        total_tips = sum(
    1
    for tip in tips
    if any(duel.id == tip.duel_id for duel in visible_duels)
)
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
        1 for duel in visible_duels
        if duel.status == "finished"
    )

    all_done = len(visible_duels) > 0 and finished_count == len(visible_duels)

    winners = []

    if all_done and standings and standings[0]["points"] > 0:
        top_points = standings[0]["points"]

        winners = [
            row for row in standings
            if row["points"] == top_points
        ]

    return jsonify({
        "tournament": tournament.to_dict(),
        "duels": [duel.to_dict() for duel in visible_duels],
        "standings": standings,
        "winners": winners,
        "winner": winners[0] if winners else None,
        "finished_count": finished_count,
        "duel_count": len(visible_duels)
    }), 200

@app.route('/api/tournaments/<int:tid>/reset-points', methods=['POST'])
@jwt_required()
def reset_tournament_points(tid):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    tournament = Tournament.query.get(tid)

    if not tournament:
        return jsonify({"error": "Serie ikke funnet"}), 404

    reset = ScoreReset(
        scope_type="tournament",
        scope_key=str(tid)
    )

    db.session.add(reset)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Poengene i serien er nullstilt"
    }), 200

@app.route('/api/leaderboard/reset-points', methods=['POST'])
@jwt_required()
def reset_global_points():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    reset = ScoreReset(
        scope_type="global",
        scope_key="all"
    )

    db.session.add(reset)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Totalpoengene er nullstilt"
    }), 200
@app.route('/api/seasons/<string:season>/reset-points', methods=['POST'])
@jwt_required()
def reset_season_points(season):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403

    tournaments = Tournament.query.filter_by(
        season=season
    ).all()

    if not tournaments:
        return jsonify({"error": "Sesong ikke funnet"}), 404

    reset = ScoreReset(
        scope_type="season",
        scope_key=season
    )

    db.session.add(reset)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Poengene for sesongen {season} er nullstilt"
    }), 200
@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204

    data = request.get_json() or {}

    username = str(data.get('username', '')).strip()
    password = data.get('password', '')

    if not username:
        return jsonify({"error": "Brukernavn er påkrevd"}), 400

    if len(username) < 3:
        return jsonify({"error": "Brukernavn må være minst 3 tegn"}), 400

    if not password or len(password) < 6:
        return jsonify({"error": "Passord må være minst 6 tegn"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Brukernavnet er allerede i bruk"}), 400

    user = User(
        username=username,
        email=f"user-{os.urandom(16).hex()}@local.invalid"
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

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

    data = request.get_json() or {}

    username = str(data.get('username', '')).strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"error": "Brukernavn og passord er påkrevd"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Ugyldig brukernavn eller passord"}), 401

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
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or get_role(user.username) != "admin":
        return jsonify({"error": "Ingen tilgang"}), 403
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

    if not user or get_role(user.username) != "admin":
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

def create_tables():
    db.create_all()
    
    
    changed = False

    for duel in Duel.query.all():
        normalized_source = (duel.external_source or "").strip().lower()
        if normalized_source not in ALLOWED_EXTERNAL_SOURCES:
            normalized_source = ""
        if duel.external_source != normalized_source:
            duel.external_source = normalized_source
            changed = True

        if not duel.tournament_id:
            continue

        try:
            tournament_id = int(duel.tournament_id)
        except (TypeError, ValueError):
            continue

        existing_link = DuelTournament.query.filter_by(
            duel_id=duel.id,
            tournament_id=tournament_id
        ).first()

        if not existing_link:
            db.session.add(DuelTournament(
                duel_id=duel.id,
                tournament_id=tournament_id
            ))
            changed = True

    for suggestion in ExternalResultSuggestion.query.all():
        normalized_status = (suggestion.status or "").strip().lower()
        if normalized_status not in SUGGESTION_STATUS_VALUES:
            suggestion.status = "needs_review"
            changed = True

    if changed:
        db.session.commit()

with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=False)
