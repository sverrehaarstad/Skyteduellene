"""Backend tests for NEW features: tournaments/seasons, season standings,
shooter profiles, and 1-point-per-correct-tip scoring."""
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
T = 30


@pytest.fixture(scope="module")
def creds():
    p = Path("/app/memory/test_credentials.md")
    if not p.exists():
        pytest.skip("missing credentials file")
    c = p.read_text()
    return {
        "email": re.search(r"(?im)^\s*-\s*Email:\s*(\S+)", c).group(1),
        "password": re.search(r"(?im)^\s*-\s*Password:\s*(\S+)", c).group(1),
    }


@pytest.fixture(scope="module")
def admin_headers(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=T)
    if r.status_code != 200:
        pytest.fail(f"Admin login failed {r.status_code}: {r.text[:300]}")
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def user_a():
    email = f"TEST_{uuid.uuid4().hex[:8]}@test.no"
    r = requests.post(f"{API}/auth/register", json={"name": "TEST Anna", "email": email, "password": "test123"}, timeout=T)
    assert r.status_code == 200, r.text
    d = r.json()
    return {"id": d["user"]["id"], "headers": {"Authorization": f"Bearer {d['token']}"}, "name": "TEST Anna"}


@pytest.fixture(scope="module")
def user_b():
    email = f"TEST_{uuid.uuid4().hex[:8]}@test.no"
    r = requests.post(f"{API}/auth/register", json={"name": "TEST Bjorn", "email": email, "password": "test123"}, timeout=T)
    assert r.status_code == 200, r.text
    d = r.json()
    return {"id": d["user"]["id"], "headers": {"Authorization": f"Bearer {d['token']}"}, "name": "TEST Bjorn"}


@pytest.fixture(scope="module")
def created(admin_headers):
    """Track created tournaments/duels for teardown."""
    box = {"tournaments": [], "duels": []}
    yield box
    for did in box["duels"]:
        requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=T)
    for tid in box["tournaments"]:
        requests.delete(f"{API}/tournaments/{tid}", headers=admin_headers, timeout=T)


def mk_tournament(admin_headers, created, name=None, season="2026"):
    name = name or f"TEST_Serie_{uuid.uuid4().hex[:6]}"
    r = requests.post(f"{API}/tournaments", json={"name": name, "season": season}, headers=admin_headers, timeout=T)
    assert r.status_code == 200, r.text
    d = r.json()
    created["tournaments"].append(d["id"])
    return d


def mk_duel(admin_headers, created, tournament_id="", s1=None, s2=None):
    s1 = s1 or f"TEST_Skytter_{uuid.uuid4().hex[:5]}"
    s2 = s2 or f"TEST_Skytter_{uuid.uuid4().hex[:5]}"
    payload = {
        "shooter1": s1, "shooter2": s2,
        "shooter1_img": "https://example.com/a.jpg", "shooter2_img": "https://example.com/b.jpg",
        "discipline": "TEST 300m", "venue": "TEST Bane", "start_time": "2026-08-01 12:00",
        "tournament_id": tournament_id,
    }
    r = requests.post(f"{API}/duels", json=payload, headers=admin_headers, timeout=T)
    assert r.status_code == 200, r.text
    d = r.json()
    created["duels"].append(d["id"])
    return d


# ---------- Tournaments CRUD ----------
class TestTournamentCrud:
    def test_create_and_list_tournament(self, admin_headers, created):
        t = mk_tournament(admin_headers, created, name="TEST_Serie_List")
        assert t["name"] == "TEST_Serie_List"
        assert t["season"] == "2026"
        assert "_id" not in t and isinstance(t["id"], str)

        r = requests.get(f"{API}/tournaments", timeout=T)
        assert r.status_code == 200
        rows = r.json()
        found = [x for x in rows if x["id"] == t["id"]]
        assert found, "created tournament not present in GET /api/tournaments"
        assert found[0]["duel_count"] == 0

    def test_create_tournament_requires_admin(self, user_a):
        r = requests.post(f"{API}/tournaments", json={"name": "TEST_hack", "season": "x"},
                           headers=user_a["headers"], timeout=T)
        assert r.status_code == 403, r.text

    def test_create_tournament_unauthenticated(self):
        r = requests.post(f"{API}/tournaments", json={"name": "TEST_anon"}, timeout=T)
        assert r.status_code == 401

    def test_tournament_detail_404_and_invalid_id(self, admin_headers):
        r = requests.get(f"{API}/tournaments/64b7f0a1c2d3e4f5a6b7c8d9", timeout=T)
        assert r.status_code == 404
        r2 = requests.get(f"{API}/tournaments/not-an-objectid", timeout=T)
        assert r2.status_code == 404, f"expected 404 got {r2.status_code}: {r2.text[:200]}"

    def test_duel_count_and_name_propagation(self, admin_headers, created):
        t = mk_tournament(admin_headers, created, name="TEST_Serie_Count")
        d = mk_duel(admin_headers, created, tournament_id=t["id"])
        assert d["tournament_id"] == t["id"]
        assert d["tournament_name"] == "TEST_Serie_Count"

        # persisted on GET duel
        g = requests.get(f"{API}/duels/{d['id']}", timeout=T)
        assert g.status_code == 200
        assert g.json()["tournament_name"] == "TEST_Serie_Count"

        rows = requests.get(f"{API}/tournaments", timeout=T).json()
        row = next(x for x in rows if x["id"] == t["id"])
        assert row["duel_count"] == 1

    def test_filter_duels_by_tournament(self, admin_headers, created):
        t = mk_tournament(admin_headers, created)
        d = mk_duel(admin_headers, created, tournament_id=t["id"])
        r = requests.get(f"{API}/duels", params={"tournament_id": t["id"]}, timeout=T)
        assert r.status_code == 200
        assert [x["id"] for x in r.json()] == [d["id"]]

    def test_delete_tournament_detaches_duels(self, admin_headers, created):
        t = mk_tournament(admin_headers, created)
        d = mk_duel(admin_headers, created, tournament_id=t["id"])
        r = requests.delete(f"{API}/tournaments/{t['id']}", headers=admin_headers, timeout=T)
        assert r.status_code == 200 and r.json()["ok"] is True
        assert requests.get(f"{API}/tournaments/{t['id']}", timeout=T).status_code == 404
        after = requests.get(f"{API}/duels/{d['id']}", timeout=T).json()
        assert after["tournament_id"] == "" and after["tournament_name"] == ""

    def test_delete_tournament_requires_admin(self, admin_headers, created, user_a):
        t = mk_tournament(admin_headers, created)
        r = requests.delete(f"{API}/tournaments/{t['id']}", headers=user_a["headers"], timeout=T)
        assert r.status_code == 403


# ---------- Season standings + winner ----------
class TestSeasonStandings:
    def test_standings_ranking_and_winner(self, admin_headers, created, user_a, user_b):
        t = mk_tournament(admin_headers, created, name="TEST_Serie_Standings")
        duel = mk_duel(admin_headers, created, tournament_id=t["id"])

        # user_a tips correctly, user_b wrong
        assert requests.post(f"{API}/duels/{duel['id']}/tip", json={"pick": "1"},
                             headers=user_a["headers"], timeout=T).status_code == 200
        assert requests.post(f"{API}/duels/{duel['id']}/tip", json={"pick": "2"},
                             headers=user_b["headers"], timeout=T).status_code == 200

        # before result: standings exist but no points, no winner
        det = requests.get(f"{API}/tournaments/{t['id']}", timeout=T).json()
        assert det["duel_count"] == 1 and det["finished_count"] == 0
        assert det["winner"] is None
        assert len(det["standings"]) == 2
        assert all(row["points"] == 0 for row in det["standings"])

        # admin sets result 1
        r = requests.post(f"{API}/duels/{duel['id']}/result",
                          json={"outcome": "1", "score1": "98", "score2": "95"},
                          headers=admin_headers, timeout=T)
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "finished"

        det = requests.get(f"{API}/tournaments/{t['id']}", timeout=T).json()
        assert det["finished_count"] == 1
        top = det["standings"][0]
        assert top["id"] == user_a["id"], det["standings"]
        assert top["points"] == 1, "POINTS_PER_CORRECT should be 1"
        assert top["correct"] == 1 and top["total_tips"] == 1 and top["accuracy"] == 100.0
        loser = det["standings"][1]
        assert loser["id"] == user_b["id"] and loser["points"] == 0
        # Totalvinner shown only when all duels finished
        assert det["winner"] is not None and det["winner"]["id"] == user_a["id"]
        assert det["duels"][0]["id"] == duel["id"]

    def test_winner_hidden_while_duel_unfinished(self, admin_headers, created, user_a):
        t = mk_tournament(admin_headers, created, name="TEST_Serie_Partial")
        d1 = mk_duel(admin_headers, created, tournament_id=t["id"])
        d2 = mk_duel(admin_headers, created, tournament_id=t["id"])
        requests.post(f"{API}/duels/{d1['id']}/tip", json={"pick": "1"}, headers=user_a["headers"], timeout=T)
        requests.post(f"{API}/duels/{d1['id']}/result", json={"outcome": "1"}, headers=admin_headers, timeout=T)

        det = requests.get(f"{API}/tournaments/{t['id']}", timeout=T).json()
        assert det["duel_count"] == 2 and det["finished_count"] == 1
        assert det["winner"] is None, "winner must be None until all duels finished"
        assert det["standings"][0]["points"] == 1

        requests.post(f"{API}/duels/{d2['id']}/result", json={"outcome": "X"}, headers=admin_headers, timeout=T)
        det = requests.get(f"{API}/tournaments/{t['id']}", timeout=T).json()
        assert det["finished_count"] == 2
        assert det["winner"] and det["winner"]["id"] == user_a["id"]

    def test_admin_excluded_from_standings(self, admin_headers, created):
        t = mk_tournament(admin_headers, created)
        d = mk_duel(admin_headers, created, tournament_id=t["id"])
        requests.post(f"{API}/duels/{d['id']}/tip", json={"pick": "X"}, headers=admin_headers, timeout=T)
        det = requests.get(f"{API}/tournaments/{t['id']}", timeout=T).json()
        assert det["standings"] == []

    def test_empty_tournament_standings(self, admin_headers, created):
        t = mk_tournament(admin_headers, created)
        det = requests.get(f"{API}/tournaments/{t['id']}", timeout=T).json()
        assert det["duels"] == [] and det["standings"] == []
        assert det["winner"] is None and det["duel_count"] == 0


# ---------- Scoring = 1 point ----------
class TestScoring:
    def test_one_point_per_correct_tip(self, admin_headers, created):
        email = f"TEST_{uuid.uuid4().hex[:8]}@test.no"
        reg = requests.post(f"{API}/auth/register", json={"name": "TEST Scorer", "email": email, "password": "test123"}, timeout=T).json()
        h = {"Authorization": f"Bearer {reg['token']}"}
        assert reg["user"]["points"] == 0

        d = mk_duel(admin_headers, created)
        requests.post(f"{API}/duels/{d['id']}/tip", json={"pick": "2"}, headers=h, timeout=T)
        requests.post(f"{API}/duels/{d['id']}/result", json={"outcome": "2"}, headers=admin_headers, timeout=T)

        me = requests.get(f"{API}/auth/me", headers=h, timeout=T).json()
        assert me["points"] == 1, f"expected 1 point per correct tip, got {me['points']}"

        tips = requests.get(f"{API}/my-tips", headers=h, timeout=T).json()
        mine = [x for x in tips if x["duel"]["id"] == d["id"]]
        assert mine and mine[0]["correct"] is True

        lb = requests.get(f"{API}/leaderboard", timeout=T).json()
        row = next(x for x in lb if x["id"] == reg["user"]["id"])
        assert row["points"] == 1 and row["correct"] == 1

        # re-setting the result to a different outcome must reverse the point
        requests.post(f"{API}/duels/{d['id']}/result", json={"outcome": "1"}, headers=admin_headers, timeout=T)
        me2 = requests.get(f"{API}/auth/me", headers=h, timeout=T).json()
        assert me2["points"] == 0, f"points not reversed on result change: {me2['points']}"


# ---------- Shooter profile ----------
class TestShooterProfile:
    def test_shooter_profile_record_and_duels(self, admin_headers, created):
        s1 = f"TEST_Ola_{uuid.uuid4().hex[:5]}"
        d1 = mk_duel(admin_headers, created, s1=s1)
        d2 = mk_duel(admin_headers, created, s2=s1)
        d3 = mk_duel(admin_headers, created, s1=s1)
        requests.post(f"{API}/duels/{d1['id']}/result", json={"outcome": "1"}, headers=admin_headers, timeout=T)  # win
        requests.post(f"{API}/duels/{d2['id']}/result", json={"outcome": "1"}, headers=admin_headers, timeout=T)  # loss (he is s2)
        requests.post(f"{API}/duels/{d3['id']}/result", json={"outcome": "X"}, headers=admin_headers, timeout=T)  # draw

        r = requests.get(f"{API}/shooters/{s1}", timeout=T)
        assert r.status_code == 200, r.text
        p = r.json()
        assert p["name"] == s1
        assert p["image"] == "https://example.com/a.jpg" or p["image"] == "https://example.com/b.jpg"
        assert p["record"] == {"wins": 1, "losses": 1, "draws": 1}, p["record"]
        ids = {d["id"] for d in p["duels"]}
        assert {d1["id"], d2["id"], d3["id"]} <= ids

    def test_unknown_shooter_returns_empty(self):
        r = requests.get(f"{API}/shooters/TEST_Ukjent_Skytter_XYZ", timeout=T)
        assert r.status_code == 200
        p = r.json()
        assert p["duels"] == [] and p["record"] == {"wins": 0, "losses": 0, "draws": 0}
        assert p["image"] == ""

    def test_shooter_name_with_space_urlencoded(self, admin_headers, created):
        name = "TEST Kari Nordmann"
        d = mk_duel(admin_headers, created, s1=name)
        r = requests.get(f"{API}/shooters/{requests.utils.quote(name)}", timeout=T)
        assert r.status_code == 200
        assert d["id"] in [x["id"] for x in r.json()["duels"]]
