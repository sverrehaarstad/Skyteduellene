from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict
from typing import List, Optional, Annotated, Literal
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import logging
import bcrypt
import jwt

# ---------- DB ----------
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_ALGORITHM = "HS256"
POINTS_PER_CORRECT = 3

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


def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": now_utc() + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


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


class DuelCreate(BaseModel):
    shooter1: str
    shooter2: str
    discipline: str
    venue: Optional[str] = ""
    start_time: Optional[str] = ""


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
        "discipline": d["discipline"],
        "venue": d.get("venue", ""),
        "start_time": d.get("start_time", ""),
        "status": d.get("status", "open"),
        "outcome": d.get("outcome"),
        "score1": d.get("score1", ""),
        "score2": d.get("score2", ""),
        "tip_counts": d.get("tip_counts", {"1": 0, "X": 0, "2": 0}),
        "created_at": d.get("created_at").isoformat() if d.get("created_at") else "",
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
        "role": "user",
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
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Feil e-post eller passord")
    token = create_access_token(str(user["_id"]), email)
    return {"token": token, "user": user_to_public(user)}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    # re-fetch to get fresh points
    fresh = await db.users.find_one({"_id": user["_id"]})
    return user_to_public(fresh)


# ---------- Duel routes ----------
@api_router.get("/duels")
async def list_duels(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    duels = await db.duels.find(query).sort("created_at", -1).to_list(500)
    return [duel_to_public(d) for d in duels]


@api_router.post("/duels")
async def create_duel(data: DuelCreate, admin: dict = Depends(require_admin)):
    doc = {
        **data.model_dump(),
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
    await db.duels.delete_one({"_id": oid(duel_id)})
    await db.tips.delete_many({"duel_id": duel_id})
    return {"ok": True}


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


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
