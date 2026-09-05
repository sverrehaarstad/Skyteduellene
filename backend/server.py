from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, UploadFile, File, Response, Header, Query
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict
from typing import List, Optional, Annotated, Literal
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import logging
import bcrypt
import jwt
import secrets
import asyncio
import requests
import uuid

# ---------- DB ----------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_ALGORITHM = "HS256"
POINTS_PER_CORRECT = 1

# ---------- Object storage ----------
STORAGE_BASE = (os.environ.get("INTEGRATION_PROXY_URL") or "").strip() or "https://integrations.emergentagent.com"
STORAGE_URL = STORAGE_BASE.rstrip("/") + "/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "skyteduellene"
storage_key = None


def init_storage(force: bool = False):
    global storage_key
    if storage_key and not force:
        return storage_key
    resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key


def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120,
    )
    if resp.status_code == 404:
        key = init_storage(force=True)
        resp = requests.put(
            f"{STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data, timeout=120,
        )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str):
    key = init_storage()
    resp = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60)
    if resp.status_code == 404:
        key = init_storage(force=True)
        resp = requests.get(f"{STORAGE_URL}/objects/{path}", headers={"X-Storage-Key": key}, timeout=60)
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# ---------- Helpers ----------
PyObjectId = Annotated[str, BeforeValidator(str)]


def now_utc():
    return datetime.now(timezone.utc)


def oid(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=404, detail="Duell ikke funnet")
    return ObjectId(id_str)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


def create_access_token(user_id: str, email: str, days: int = 7) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": now_utc() + timedelta(days=days),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def admin_email_set() -> set:
    seed = os.environ.get("ADMIN_EMAIL", "").lower()
    extra = os.environ.get("ADMIN_EMAILS", "")
    emails = {e.strip().lower() for e in extra.split(",") if e.strip()}
    if seed:
        emails.add(seed)
    return emails


def role_for(email: str) -> str:
    return "admin" if email.lower() in admin_email_set() else "user"


def send_reset_email(to_email: str, reset_link: str):
    api_key = os.environ.get("RESEND_API_KEY", "").strip()
    if not api_key:
        logger.info(f"[PASSORD-RESET] Ingen RESEND_API_KEY satt. Tilbakestillingslenke for {to_email}: {reset_link}")
        return
    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            "from": os.environ.get("SENDER_EMAIL", "onboarding@resend.dev"),
            "to": [to_email],
            "subject": "Tilbakestill passordet ditt – Skyteduellene",
            "html": f"""
                <div style=\"font-family:Arial,sans-serif;max-width:480px;margin:auto\">
                  <h2 style=\"color:#0F172A\">Tilbakestill passord</h2>
                  <p>Klikk på lenken under for å velge et nytt passord. Lenken er gyldig i 1 time.</p>
                  <p><a href=\"{reset_link}\" style=\"display:inline-block;background:#D92525;color:#fff;text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:bold\">Velg nytt passord</a></p>
                  <p style=\"color:#64748b;font-size:12px\">Hvis du ikke ba om dette, kan du se bort fra e-posten.</p>
                </div>
            """,
        })
    except Exception as e:
        logger.error(f"Kunne ikke sende e-post via Resend: {e}. Lenke for {to_email}: {reset_link}")



# ---------- Models ----------
class UserPublic(BaseModel):
    id: str
    email: str
    name: str
    role: str
    points: int = 0


class RegisterInput(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)


class LoginInput(BaseModel):
    email: EmailStr
    password: str
    remember: Optional[bool] = False


class ForgotInput(BaseModel):
    email: EmailStr
    origin: Optional[str] = ""


class ResetInput(BaseModel):
    token: str
    password: str = Field(min_length=6)


class GoogleSessionInput(BaseModel):
    session_id: str
    remember: Optional[bool] = False


class SettingsInput(BaseModel):
    hero_image: str


class RoleInput(BaseModel):
    role: Literal["admin", "user"]


class DuelCreate(BaseModel):
    shooter1: str
    shooter2: str
    shooter1_img: Optional[str] = ""
    shooter2_img: Optional[str] = ""
    discipline: str
    venue: Optional[str] = ""
    start_time: Optional[str] = ""
    start_at: Optional[str] = ""
    tournament_id: Optional[str] = ""


class TournamentCreate(BaseModel):
    name: str
    season: Optional[str] = ""


class DuelUpdate(BaseModel):
    shooter1_img: Optional[str] = None
    shooter2_img: Optional[str] = None
    shooter1: Optional[str] = None
    shooter2: Optional[str] = None
    discipline: Optional[str] = None
    venue: Optional[str] = None
    start_at: Optional[str] = None


class ResultInput(BaseModel):
    outcome: Literal["1", "X", "2"]
    score1: Optional[str] = ""
    score2: Optional[str] = ""


class TipInput(BaseModel):
    pick: Literal["1", "X", "2"]


# ---------- App ----------
app = FastAPI()
api_router = APIRouter(prefix="/api")


async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Ikke innlogget")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="Bruker ikke funnet")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token utløpt")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ugyldig token")


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Kun admin har tilgang")
    return user


def user_to_public(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user.get("role", "user"),
        "points": user.get("points", 0),
    }


def duel_to_public(d: dict) -> dict:
    return {
        "id": str(d["_id"]),
        "shooter1": d["shooter1"],
        "shooter2": d["shooter2"],
        "shooter1_img": d.get("shooter1_img", ""),
        "shooter2_img": d.get("shooter2_img", ""),
        "discipline": d["discipline"],
        "venue": d.get("venue", ""),
        "start_time": d.get("start_time", ""),
        "start_at": d.get("start_at", ""),
        "status": d.get("status", "open"),
        "outcome": d.get("outcome"),
        "score1": d.get("score1", ""),
        "score2": d.get("score2", ""),
        "tip_counts": d.get("tip_counts", {"1": 0, "X": 0, "2": 0}),
        "tournament_id": d.get("tournament_id", ""),
        "tournament_name": d.get("tournament_name", ""),
        "created_at": d.get("created_at").isoformat() if d.get("created_at") else "",
    }


def tournament_to_public(t: dict) -> dict:
    return {
        "id": str(t["_id"]),
        "name": t["name"],
        "season": t.get("season", ""),
        "created_at": t.get("created_at").isoformat() if t.get("created_at") else "",
    }


# ---------- Auth routes ----------
@api_router.post("/auth/register")
async def register(data: RegisterInput):
    email = data.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="E-post er allerede registrert")
    doc = {
        "email": email,
        "name": data.name,
        "password_hash": hash_password(data.password),
        "role": role_for(email),
        "points": 0,
        "created_at": now_utc(),
    }
    res = await db.users.insert_one(doc)
    doc["_id"] = res.inserted_id
    token = create_access_token(str(res.inserted_id), email)
    return {"token": token, "user": user_to_public(doc)}


@api_router.post("/auth/login")
async def login(data: LoginInput):
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not user.get("password_hash") or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Feil e-post eller passord")
    token = create_access_token(str(user["_id"]), email, days=30 if data.remember else 7)
    return {"token": token, "user": user_to_public(user)}


@api_router.post("/auth/google")
async def google_login(data: GoogleSessionInput):
    try:
        resp = await asyncio.to_thread(
            requests.get,
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": data.session_id},
            timeout=15,
        )
    except Exception:
        raise HTTPException(status_code=502, detail="Kunne ikke kontakte Google-innlogging")
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Ugyldig eller utløpt Google-økt")
    info = resp.json()
    email = (info.get("email") or "").lower()
    name = info.get("name") or email.split("@")[0]
    if not email:
        raise HTTPException(status_code=400, detail="Google returnerte ingen e-post")

    user = await db.users.find_one({"email": email})
    if not user:
        doc = {
            "email": email,
            "name": name,
            "password_hash": "",
            "role": role_for(email),
            "points": 0,
            "auth_provider": "google",
            "picture": info.get("picture", ""),
            "created_at": now_utc(),
        }
        res = await db.users.insert_one(doc)
        doc["_id"] = res.inserted_id
        user = doc
    else:
        # ensure admin promotion if email is in allowlist
        if role_for(email) == "admin" and user.get("role") != "admin":
            await db.users.update_one({"_id": user["_id"]}, {"$set": {"role": "admin"}})
            user["role"] = "admin"
    token = create_access_token(str(user["_id"]), email, days=30 if data.remember else 7)
    return {"token": token, "user": user_to_public(user)}


@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotInput):
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if user:
        token = secrets.token_urlsafe(32)
        await db.password_reset_tokens.insert_one({
            "token": token,
            "user_id": str(user["_id"]),
            "email": email,
            "expires_at": now_utc() + timedelta(hours=1),
            "used": False,
            "created_at": now_utc(),
        })
        app_url = (data.origin or os.environ.get("APP_URL", "")).rstrip("/")
        reset_link = f"{app_url}/reset?token={token}"
        await asyncio.to_thread(send_reset_email, email, reset_link)
    # Always generic response to avoid leaking which emails exist
    return {"ok": True, "message": "Hvis e-posten finnes, har vi sendt en tilbakestillingslenke."}


@api_router.post("/auth/reset-password")
async def reset_password(data: ResetInput):
    rec = await db.password_reset_tokens.find_one({"token": data.token})
    if not rec or rec.get("used"):
        raise HTTPException(status_code=400, detail="Ugyldig eller brukt lenke")
    expires_at = rec["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now_utc():
        raise HTTPException(status_code=400, detail="Lenken er utløpt")
    await db.users.update_one({"_id": ObjectId(rec["user_id"])}, {"$set": {"password_hash": hash_password(data.password)}})
    await db.password_reset_tokens.update_one({"_id": rec["_id"]}, {"$set": {"used": True}})
    return {"ok": True}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    # re-fetch to get fresh points
    fresh = await db.users.find_one({"_id": user["_id"]})
    return user_to_public(fresh)


# ---------- Duel routes ----------
@api_router.get("/duels")
async def list_duels(status: Optional[str] = None, tournament_id: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    if tournament_id:
        query["tournament_id"] = tournament_id
    duels = await db.duels.find(query).sort("created_at", -1).to_list(500)
    return [duel_to_public(d) for d in duels]


@api_router.get("/duels/{duel_id}")
async def get_duel(duel_id: str):
    duel = await db.duels.find_one({"_id": oid(duel_id)})
    if not duel:
        raise HTTPException(status_code=404, detail="Duell ikke funnet")
    return duel_to_public(duel)


@api_router.post("/duels")
async def create_duel(data: DuelCreate, admin: dict = Depends(require_admin)):
    payload = data.model_dump()
    tournament_name = ""
    if payload.get("tournament_id"):
        t = await db.tournaments.find_one({"_id": oid(payload["tournament_id"])})
        tournament_name = t["name"] if t else ""
    doc = {
        **payload,
        "tournament_name": tournament_name,
        "status": "open",
        "outcome": None,
        "score1": "",
        "score2": "",
        "tip_counts": {"1": 0, "X": 0, "2": 0},
        "created_at": now_utc(),
    }
    res = await db.duels.insert_one(doc)
    doc["_id"] = res.inserted_id
    return duel_to_public(doc)


@api_router.delete("/duels/{duel_id}")
async def delete_duel(duel_id: str, admin: dict = Depends(require_admin)):
    # Reclaim points awarded for correct tips on this duel before deleting
    correct_tips = await db.tips.find({"duel_id": duel_id, "correct": True}).to_list(2000)
    for t in correct_tips:
        await db.users.update_one({"_id": ObjectId(t["user_id"])}, {"$inc": {"points": -POINTS_PER_CORRECT}})
    await db.duels.delete_one({"_id": oid(duel_id)})
    await db.tips.delete_many({"duel_id": duel_id})
    return {"ok": True}


@api_router.patch("/duels/{duel_id}")
async def update_duel(duel_id: str, data: DuelUpdate, admin: dict = Depends(require_admin)):
    duel = await db.duels.find_one({"_id": oid(duel_id)})
    if not duel:
        raise HTTPException(status_code=404, detail="Duell ikke funnet")
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if updates:
        await db.duels.update_one({"_id": oid(duel_id)}, {"$set": updates})
    updated = await db.duels.find_one({"_id": oid(duel_id)})
    return duel_to_public(updated)


@api_router.post("/duels/{duel_id}/result")
async def set_result(duel_id: str, data: ResultInput, admin: dict = Depends(require_admin)):
    duel = await db.duels.find_one({"_id": oid(duel_id)})
    if not duel:
        raise HTTPException(status_code=404, detail="Duell ikke funnet")

    # Reverse previously awarded points if result already existed
    if duel.get("status") == "finished":
        prev_correct = await db.tips.find({"duel_id": duel_id, "correct": True}).to_list(1000)
        for t in prev_correct:
            await db.users.update_one({"_id": ObjectId(t["user_id"])}, {"$inc": {"points": -POINTS_PER_CORRECT}})

    await db.duels.update_one(
        {"_id": oid(duel_id)},
        {"$set": {"status": "finished", "outcome": data.outcome, "score1": data.score1, "score2": data.score2}},
    )

    # Evaluate tips
    tips = await db.tips.find({"duel_id": duel_id}).to_list(1000)
    for t in tips:
        correct = t["pick"] == data.outcome
        await db.tips.update_one({"_id": t["_id"]}, {"$set": {"correct": correct}})
        if correct:
            await db.users.update_one({"_id": ObjectId(t["user_id"])}, {"$inc": {"points": POINTS_PER_CORRECT}})

    updated = await db.duels.find_one({"_id": oid(duel_id)})
    return duel_to_public(updated)


# ---------- Tip routes ----------
@api_router.post("/duels/{duel_id}/tip")
async def place_tip(duel_id: str, data: TipInput, user: dict = Depends(get_current_user)):
    duel = await db.duels.find_one({"_id": oid(duel_id)})
    if not duel:
        raise HTTPException(status_code=404, detail="Duell ikke funnet")
    if duel.get("status") != "open":
        raise HTTPException(status_code=400, detail="Duellen er avsluttet, du kan ikke tippe")

    existing = await db.tips.find_one({"duel_id": duel_id, "user_id": str(user["_id"])})
    if existing:
        old_pick = existing["pick"]
        await db.tips.update_one({"_id": existing["_id"]}, {"$set": {"pick": data.pick}})
        if old_pick != data.pick:
            await db.duels.update_one({"_id": oid(duel_id)}, {"$inc": {f"tip_counts.{old_pick}": -1, f"tip_counts.{data.pick}": 1}})
    else:
        await db.tips.insert_one({
            "duel_id": duel_id,
            "user_id": str(user["_id"]),
            "pick": data.pick,
            "correct": None,
            "created_at": now_utc(),
        })
        await db.duels.update_one({"_id": oid(duel_id)}, {"$inc": {f"tip_counts.{data.pick}": 1}})
    return {"ok": True, "pick": data.pick}


@api_router.get("/my-tips")
async def my_tips(user: dict = Depends(get_current_user)):
    tips = await db.tips.find({"user_id": str(user["_id"])}).sort("created_at", -1).to_list(1000)
    result = []
    for t in tips:
        duel = await db.duels.find_one({"_id": ObjectId(t["duel_id"])})
        if not duel:
            continue
        result.append({
            "id": str(t["_id"]),
            "pick": t["pick"],
            "correct": t.get("correct"),
            "duel": duel_to_public(duel),
        })
    return result


# ---------- Leaderboard ----------
@api_router.get("/leaderboard")
async def leaderboard():
    users = await db.users.find({"role": {"$ne": "admin"}}).to_list(1000)
    rows = []
    for u in users:
        uid = str(u["_id"])
        total = await db.tips.count_documents({"user_id": uid})
        correct = await db.tips.count_documents({"user_id": uid, "correct": True})
        rows.append({
            "id": uid,
            "name": u["name"],
            "points": u.get("points", 0),
            "correct": correct,
            "total_tips": total,
            "accuracy": round((correct / total * 100), 1) if total else 0.0,
        })
    rows.sort(key=lambda r: (r["points"], r["correct"]), reverse=True)
    return rows


# ---------- Tournaments (Serier / Sesonger) ----------
@api_router.get("/tournaments")
async def list_tournaments():
    tours = await db.tournaments.find().sort("created_at", -1).to_list(200)
    out = []
    for t in tours:
        tid = str(t["_id"])
        duel_count = await db.duels.count_documents({"tournament_id": tid})
        pub = tournament_to_public(t)
        pub["duel_count"] = duel_count
        out.append(pub)
    return out


@api_router.post("/tournaments")
async def create_tournament(data: TournamentCreate, admin: dict = Depends(require_admin)):
    doc = {"name": data.name, "season": data.season or "", "created_at": now_utc()}
    res = await db.tournaments.insert_one(doc)
    doc["_id"] = res.inserted_id
    return tournament_to_public(doc)


@api_router.delete("/tournaments/{tid}")
async def delete_tournament(tid: str, admin: dict = Depends(require_admin)):
    await db.tournaments.delete_one({"_id": oid(tid)})
    await db.duels.update_many({"tournament_id": tid}, {"$set": {"tournament_id": "", "tournament_name": ""}})
    return {"ok": True}


@api_router.get("/tournaments/{tid}")
async def tournament_detail(tid: str):
    t = await db.tournaments.find_one({"_id": oid(tid)})
    if not t:
        raise HTTPException(status_code=404, detail="Sesong ikke funnet")
    duels = await db.duels.find({"tournament_id": tid}).sort("created_at", -1).to_list(500)
    duel_ids = [str(d["_id"]) for d in duels]

    # Standings: tippers ranked by points earned on this season's duels
    standings = {}
    if duel_ids:
        tips = await db.tips.find({"duel_id": {"$in": duel_ids}}).to_list(5000)
        for tip in tips:
            uid = tip["user_id"]
            if uid not in standings:
                standings[uid] = {"correct": 0, "total": 0}
            standings[uid]["total"] += 1
            if tip.get("correct"):
                standings[uid]["correct"] += 1

    rows = []
    for uid, s in standings.items():
        u = await db.users.find_one({"_id": ObjectId(uid)})
        if not u or u.get("role") == "admin":
            continue
        rows.append({
            "id": uid,
            "name": u["name"],
            "points": s["correct"] * POINTS_PER_CORRECT,
            "correct": s["correct"],
            "total_tips": s["total"],
            "accuracy": round((s["correct"] / s["total"] * 100), 1) if s["total"] else 0.0,
        })
    rows.sort(key=lambda r: (r["points"], r["correct"]), reverse=True)

    finished = sum(1 for d in duels if d.get("status") == "finished")
    all_done = len(duels) > 0 and finished == len(duels)
    winners = []
    if all_done and rows and rows[0]["points"] > 0:
        top = rows[0]["points"]
        winners = [r for r in rows if r["points"] == top]
    return {
        "tournament": tournament_to_public(t),
        "duels": [duel_to_public(d) for d in duels],
        "standings": rows,
        "winners": winners,
        "winner": winners[0] if winners else None,
        "finished_count": finished,
        "duel_count": len(duels),
    }


# ---------- Shooter profile ----------
@api_router.get("/shooters/{name}")
async def shooter_profile(name: str):
    duels = await db.duels.find({"$or": [{"shooter1": name}, {"shooter2": name}]}).sort("created_at", -1).to_list(500)
    image = ""
    wins = losses = draws = 0
    for d in duels:
        is_s1 = d["shooter1"] == name
        if not image:
            img = d.get("shooter1_img") if is_s1 else d.get("shooter2_img")
            if img:
                image = img
        if d.get("status") == "finished":
            oc = d.get("outcome")
            if oc == "X":
                draws += 1
            elif (oc == "1" and is_s1) or (oc == "2" and not is_s1):
                wins += 1
            else:
                losses += 1
    return {
        "name": name,
        "image": image,
        "record": {"wins": wins, "losses": losses, "draws": draws},
        "duels": [duel_to_public(d) for d in duels],
    }




# ---------- Site settings (admin-editable hero background) ----------
DEFAULT_HERO = "https://customer-assets-4nw71qhi.emergentagent.net/job_duel-shooter-tips/artifacts/7tyyrc1x_Stangskyting1.webp"


@api_router.get("/settings")
async def get_settings():
    doc = await db.settings.find_one({"key": "site"})
    hero = doc.get("hero_image") if doc else None
    return {"hero_image": hero or DEFAULT_HERO}


@api_router.put("/settings")
async def update_settings(data: SettingsInput, admin: dict = Depends(require_admin)):
    await db.settings.update_one(
        {"key": "site"},
        {"$set": {"hero_image": data.hero_image, "updated_at": now_utc()}},
        upsert=True,
    )
    return {"hero_image": data.hero_image}


# ---------- Admin: user management ----------
@api_router.get("/admin/users")
async def admin_list_users(admin: dict = Depends(require_admin)):
    users = await db.users.find().sort("created_at", 1).to_list(2000)
    seed = os.environ.get("ADMIN_EMAIL", "").lower()
    out = []
    for u in users:
        p = user_to_public(u)
        p["is_seed_admin"] = (u["email"].lower() == seed)
        out.append(p)
    return out


@api_router.post("/admin/users/{user_id}/role")
async def admin_set_role(user_id: str, data: RoleInput, admin: dict = Depends(require_admin)):
    target = await db.users.find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="Bruker ikke funnet")
    seed = os.environ.get("ADMIN_EMAIL", "").lower()
    if target["email"].lower() == seed and data.role != "admin":
        raise HTTPException(status_code=400, detail="Kan ikke fjerne admin fra hovedkontoen")
    await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": data.role}})
    updated = await db.users.find_one({"_id": ObjectId(user_id)})
    return user_to_public(updated)



# ---------- File upload (shooter images) ----------
MIME_TYPES = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}


@api_router.post("/upload")
async def upload_image(file: UploadFile = File(...), admin: dict = Depends(require_admin)):
    ext = (file.filename.rsplit(".", 1)[-1] if "." in file.filename else "png").lower()
    if ext not in MIME_TYPES:
        raise HTTPException(status_code=400, detail="Kun bildefiler er tillatt (png, jpg, webp, gif)")
    content_type = file.content_type or MIME_TYPES[ext]
    path = f"{APP_NAME}/shooters/{uuid.uuid4()}.{ext}"
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Bildet er for stort (maks 8MB)")
    try:
        result = await asyncio.to_thread(put_object, path, data, content_type)
    except Exception as e:
        logger.error(f"Opplasting feilet: {e}")
        raise HTTPException(status_code=502, detail="Kunne ikke laste opp bildet")
    stored_path = result["path"]
    await db.files.insert_one({
        "storage_path": stored_path,
        "content_type": content_type,
        "original_filename": file.filename,
        "created_at": now_utc(),
    })
    return {"url": f"/api/files/{stored_path}"}


@api_router.get("/files/{path:path}")
async def serve_file(path: str):
    record = await db.files.find_one({"storage_path": path})
    if not record:
        raise HTTPException(status_code=404, detail="Fil ikke funnet")
    try:
        data, content_type = await asyncio.to_thread(get_object, path)
    except Exception:
        raise HTTPException(status_code=404, detail="Fil ikke funnet")
    return Response(content=data, media_type=record.get("content_type", content_type),
                    headers={"Cache-Control": "public, max-age=86400"})



app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    try:
        await asyncio.to_thread(init_storage)
        logger.info("Object storage initialized")
    except Exception as e:
        logger.error(f"Storage init failed: {e}")
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").lower()
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "name": "Admin",
            "password_hash": hash_password(admin_password),
            "role": "admin",
            "points": 0,
            "created_at": now_utc(),
        })
        logger.info("Admin seeded")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})

    # Promote any allowlisted admin emails (e.g. Sverre) if their account exists
    for e in admin_email_set():
        await db.users.update_one({"email": e}, {"$set": {"role": "admin"}})

    # TTL cleanup of expired reset tokens
    try:
        await db.password_reset_tokens.create_index("expires_at", expireAfterSeconds=3600)
    except Exception:
        pass


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
