"""Backend API tests for Riffeltippen (auth, duels, tips, results, leaderboard)."""
import os
import re
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
base_url = os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")
if not base_url:
    raise RuntimeError("REACT_APP_BACKEND_URL missing")
BASE_URL = base_url.rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="session")
def creds():
    p = Path("/app/memory/test_credentials.md")
    if not p.exists():
        pytest.skip("missing credentials file")
    c = p.read_text()
    email = re.search(r"(?im)^\s*-\s*Email:\s*(\S+)", c).group(1)
    password = re.search(r"(?im)^\s*-\s*Password:\s*(\S+)", c).group(1)
    return {"email": email, "password": password}


@pytest.fixture(scope="session")
def admin_token(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    data = r.json()
    assert data["user"]["role"] == "admin"
    return data["token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def test_user():
    email = f"TEST_{uuid.uuid4().hex[:8]}@test.no"
    r = requests.post(f"{API}/auth/register", json={
        "name": "TEST Tipper", "email": email, "password": "test123"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    return {"email": email, "password": "test123", "token": d["token"], "id": d["user"]["id"]}


@pytest.fixture(scope="session")
def user_headers(test_user):
    return {"Authorization": f"Bearer {test_user['token']}"}


# ---------- Auth ----------
class TestAuth:
    def test_register_returns_token_and_user(self):
        email = f"TEST_{uuid.uuid4().hex[:8]}@test.no"
        r = requests.post(f"{API}/auth/register", json={
            "name": "TEST Reg", "email": email, "password": "secret123"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d["token"], str) and len(d["token"]) > 10
        assert d["user"]["email"] == email.lower()
        assert d["user"]["role"] == "user"
        assert d["user"]["points"] == 0
        assert "_id" not in d["user"]

    def test_register_duplicate_email(self, test_user):
        r = requests.post(f"{API}/auth/register", json={
            "name": "dupe", "email": test_user["email"], "password": "test123"}, timeout=30)
        assert r.status_code == 400
        assert "registrert" in r.json()["detail"]

    def test_register_short_password_rejected(self):
        r = requests.post(f"{API}/auth/register", json={
            "name": "x", "email": f"TEST_{uuid.uuid4().hex[:6]}@test.no", "password": "123"}, timeout=30)
        assert r.status_code == 422

    def test_register_invalid_email_rejected(self):
        r = requests.post(f"{API}/auth/register", json={
            "name": "x", "email": "not-an-email", "password": "123456"}, timeout=30)
        assert r.status_code == 422

    def test_login_success(self, test_user):
        r = requests.post(f"{API}/auth/login", json={
            "email": test_user["email"], "password": test_user["password"]}, timeout=30)
        assert r.status_code == 200
        assert r.json()["user"]["email"] == test_user["email"].lower()

    def test_login_case_insensitive_email(self, test_user):
        r = requests.post(f"{API}/auth/login", json={
            "email": test_user["email"].upper(), "password": test_user["password"]}, timeout=30)
        assert r.status_code == 200

    def test_login_wrong_password(self, test_user):
        r = requests.post(f"{API}/auth/login", json={
            "email": test_user["email"], "password": "wrongpass"}, timeout=30)
        assert r.status_code == 401

    def test_me_requires_auth(self):
        r = requests.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 401

    def test_me_invalid_token(self):
        r = requests.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"}, timeout=30)
        assert r.status_code == 401

    def test_me_returns_profile(self, user_headers, test_user):
        r = requests.get(f"{API}/auth/me", headers=user_headers, timeout=30)
        assert r.status_code == 200
        assert r.json()["id"] == test_user["id"]

    def test_bcrypt_hash_format(self, creds):
        """Verify stored hash is bcrypt $2b$ format (direct DB check)."""
        import asyncio
        from motor.motor_asyncio import AsyncIOMotorClient
        env = dotenv_values("/app/backend/.env")

        async def check():
            cl = AsyncIOMotorClient(env["MONGO_URL"])
            u = await cl[env["DB_NAME"]].users.find_one({"email": creds["email"]})
            cl.close()
            return u
        u = asyncio.get_event_loop().run_until_complete(check())
        assert u is not None
        assert u["password_hash"].startswith("$2b$"), u["password_hash"][:10]


# ---------- Duels ----------
class TestDuels:
    def test_list_duels_public(self):
        r = requests.get(f"{API}/duels", timeout=30)
        assert r.status_code == 200
        duels = r.json()
        assert isinstance(duels, list)
        for d in duels:
            assert "_id" not in d
            assert set(["id", "shooter1", "shooter2", "discipline", "status", "tip_counts"]).issubset(d)

    def test_list_duels_status_filter(self):
        r = requests.get(f"{API}/duels", params={"status": "open"}, timeout=30)
        assert r.status_code == 200
        assert all(d["status"] == "open" for d in r.json())

    def test_create_duel_requires_admin(self, user_headers):
        r = requests.post(f"{API}/duels", headers=user_headers, json={
            "shooter1": "a", "shooter2": "b", "discipline": "x"}, timeout=30)
        assert r.status_code == 403

    def test_create_duel_unauthenticated(self):
        r = requests.post(f"{API}/duels", json={
            "shooter1": "a", "shooter2": "b", "discipline": "x"}, timeout=30)
        assert r.status_code == 401

    def test_create_and_delete_duel(self, admin_headers):
        payload = {"shooter1": "TEST Skytter A", "shooter2": "TEST Skytter B",
                   "discipline": "TEST 100m", "venue": "TEST Bane", "start_time": "2026-08-01 12:00"}
        r = requests.post(f"{API}/duels", headers=admin_headers, json=payload, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        did = d["id"]
        assert d["status"] == "open"
        assert d["shooter1"] == payload["shooter1"]
        assert d["tip_counts"] == {"1": 0, "X": 0, "2": 0}

        # verify persistence via list
        lst = requests.get(f"{API}/duels", timeout=30).json()
        assert any(x["id"] == did and x["venue"] == payload["venue"] for x in lst)

        # delete requires admin
        assert requests.delete(f"{API}/duels/{did}", timeout=30).status_code == 401
        r = requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=30)
        assert r.status_code == 200 and r.json()["ok"] is True
        lst = requests.get(f"{API}/duels", timeout=30).json()
        assert not any(x["id"] == did for x in lst)


# ---------- Tips + results + leaderboard ----------
class TestTipsAndResults:
    @pytest.fixture(scope="class")
    def duel_id(self, admin_headers):
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST T1", "shooter2": "TEST T2", "discipline": "TEST felt",
            "venue": "TEST V", "start_time": "2026-09-09 10:00"}, timeout=30)
        assert r.status_code == 200
        did = r.json()["id"]
        yield did
        requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=30)

    def test_tip_requires_auth(self, duel_id):
        r = requests.post(f"{API}/duels/{duel_id}/tip", json={"pick": "1"}, timeout=30)
        assert r.status_code == 401

    def test_invalid_pick_rejected(self, duel_id, user_headers):
        r = requests.post(f"{API}/duels/{duel_id}/tip", headers=user_headers,
                          json={"pick": "3"}, timeout=30)
        assert r.status_code == 422

    def test_place_tip_increments_count(self, duel_id, user_headers):
        r = requests.post(f"{API}/duels/{duel_id}/tip", headers=user_headers,
                          json={"pick": "1"}, timeout=30)
        assert r.status_code == 200 and r.json()["pick"] == "1"
        d = [x for x in requests.get(f"{API}/duels", timeout=30).json() if x["id"] == duel_id][0]
        assert d["tip_counts"]["1"] == 1

    def test_change_tip_moves_count(self, duel_id, user_headers):
        r = requests.post(f"{API}/duels/{duel_id}/tip", headers=user_headers,
                          json={"pick": "X"}, timeout=30)
        assert r.status_code == 200
        d = [x for x in requests.get(f"{API}/duels", timeout=30).json() if x["id"] == duel_id][0]
        assert d["tip_counts"]["1"] == 0
        assert d["tip_counts"]["X"] == 1
        mine = requests.get(f"{API}/my-tips", headers={**user_headers}, timeout=30).json()
        entry = [t for t in mine if t["duel"]["id"] == duel_id]
        assert len(entry) == 1, "changing tip must not duplicate the tip"
        assert entry[0]["pick"] == "X"
        assert entry[0]["correct"] is None

    def test_result_requires_admin(self, duel_id, user_headers):
        r = requests.post(f"{API}/duels/{duel_id}/result", headers=user_headers,
                          json={"outcome": "X"}, timeout=30)
        assert r.status_code == 403

    def test_invalid_outcome_rejected(self, duel_id, admin_headers):
        r = requests.post(f"{API}/duels/{duel_id}/result", headers=admin_headers,
                          json={"outcome": "Y"}, timeout=30)
        assert r.status_code == 422

    def test_result_awards_points_and_updates_leaderboard(self, duel_id, admin_headers, user_headers, test_user):
        before = requests.get(f"{API}/auth/me", headers=user_headers, timeout=30).json()["points"]
        r = requests.post(f"{API}/duels/{duel_id}/result", headers=admin_headers,
                          json={"outcome": "X", "score1": "98", "score2": "98"}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "finished" and d["outcome"] == "X" and d["score1"] == "98"

        after = requests.get(f"{API}/auth/me", headers=user_headers, timeout=30).json()["points"]
        assert after == before + 1, f"expected +1 point (POINTS_PER_CORRECT=1), got {before}->{after}"

        mine = requests.get(f"{API}/my-tips", headers=user_headers, timeout=30).json()
        entry = [t for t in mine if t["duel"]["id"] == duel_id][0]
        assert entry["correct"] is True

        lb = requests.get(f"{API}/leaderboard", timeout=30).json()
        row = [x for x in lb if x["id"] == test_user["id"]]
        assert row, "user missing from leaderboard"
        row = row[0]
        assert row["points"] == after
        assert row["correct"] >= 1
        assert row["accuracy"] == round(row["correct"] / row["total_tips"] * 100, 1)
        # leaderboard sorted desc by points
        pts = [x["points"] for x in lb]
        assert pts == sorted(pts, reverse=True)
        # admin excluded
        assert all("Admin" != x["name"] for x in lb)

    def test_cannot_tip_finished_duel(self, duel_id, user_headers):
        r = requests.post(f"{API}/duels/{duel_id}/tip", headers=user_headers,
                          json={"pick": "1"}, timeout=30)
        assert r.status_code == 400
        assert "avsluttet" in r.json()["detail"]

    def test_result_correction_reverses_points(self, duel_id, admin_headers, user_headers):
        before = requests.get(f"{API}/auth/me", headers=user_headers, timeout=30).json()["points"]
        r = requests.post(f"{API}/duels/{duel_id}/result", headers=admin_headers,
                          json={"outcome": "2", "score1": "95", "score2": "99"}, timeout=30)
        assert r.status_code == 200
        after = requests.get(f"{API}/auth/me", headers=user_headers, timeout=30).json()["points"]
        assert after == before - 1, f"points should be reversed: {before}->{after}"


# ---------- Edge cases ----------
class TestEdgeCases:
    def test_bad_objectid_duel_tip(self, user_headers):
        r = requests.post(f"{API}/duels/not-an-objectid/tip", headers=user_headers,
                          json={"pick": "1"}, timeout=30)
        assert r.status_code in (400, 404, 422), f"got {r.status_code}: {r.text[:200]}"

    def test_result_nonexistent_duel(self, admin_headers):
        r = requests.post(f"{API}/duels/000000000000000000000000/result",
                          headers=admin_headers, json={"outcome": "1"}, timeout=30)
        assert r.status_code == 404

    def test_my_tips_requires_auth(self):
        assert requests.get(f"{API}/my-tips", timeout=30).status_code == 401

    def test_brute_force_lockout(self, test_user):
        """Playbook: expect lockout after 5 failed logins (informational)."""
        codes = []
        for _ in range(6):
            codes.append(requests.post(f"{API}/auth/login", json={
                "email": test_user["email"], "password": "bad"}, timeout=30).status_code)
        assert 429 in codes, f"no rate limiting/lockout observed, codes={codes}"
