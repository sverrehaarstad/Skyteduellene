"""Tests for iteration-3 bug fixes:
1) delete_duel reclaims points from users with correct tips
2) POST /api/upload + GET /api/files/{path} for shooter images; PATCH /api/duels/{id}
3) (Frontend-only) admin duel tabs -- backend still exposes status filter used by that UI
"""
import base64
import io
import os
import re
import uuid
from pathlib import Path

import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL")).rstrip("/")
API = f"{BASE_URL}/api"

# a tiny valid 1x1 PNG
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)


@pytest.fixture(scope="module")
def creds():
    txt = Path("/app/memory/test_credentials.md").read_text()
    email = re.search(r"(?im)^\s*-\s*Email:\s*(\S+)", txt).group(1)
    password = re.search(r"(?im)^\s*-\s*Password:\s*(\S+)", txt).group(1)
    return {"email": email, "password": password}


@pytest.fixture(scope="module")
def admin_headers(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def test_user():
    email = f"TEST_{uuid.uuid4().hex[:8]}@test.no"
    r = requests.post(f"{API}/auth/register",
                      json={"name": "TEST DelPoints", "email": email, "password": "test123"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    return {"email": email, "password": "test123", "token": d["token"], "id": d["user"]["id"],
            "headers": {"Authorization": f"Bearer {d['token']}"}}


# ---------- BUG 1: delete_duel reclaims points ----------
class TestDeleteDuelReclaimsPoints:
    def test_delete_finished_duel_reclaims_correct_points(self, admin_headers, test_user):
        # 1) create duel
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST DelA", "shooter2": "TEST DelB", "discipline": "TEST"}, timeout=30)
        assert r.status_code == 200
        did = r.json()["id"]

        # 2) user tips correct outcome
        r = requests.post(f"{API}/duels/{did}/tip", headers=test_user["headers"],
                          json={"pick": "1"}, timeout=30)
        assert r.status_code == 200

        before = requests.get(f"{API}/auth/me", headers=test_user["headers"], timeout=30).json()["points"]

        # 3) admin sets result -> user gains +1
        r = requests.post(f"{API}/duels/{did}/result", headers=admin_headers,
                          json={"outcome": "1", "score1": "99", "score2": "97"}, timeout=30)
        assert r.status_code == 200, r.text

        after_result = requests.get(f"{API}/auth/me", headers=test_user["headers"], timeout=30).json()["points"]
        assert after_result == before + 1, f"expected +1 after result, {before}->{after_result}"

        # verify leaderboard reflects +1
        lb = requests.get(f"{API}/leaderboard", timeout=30).json()
        row = [x for x in lb if x["id"] == test_user["id"]][0]
        assert row["points"] == after_result

        # 4) admin deletes duel -> user loses that 1 point
        r = requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=30)
        assert r.status_code == 200

        after_delete = requests.get(f"{API}/auth/me", headers=test_user["headers"], timeout=30).json()["points"]
        assert after_delete == before, f"expected reclaim to {before}, got {after_delete}"

        # leaderboard row's correct count decremented (tip deleted too)
        lb = requests.get(f"{API}/leaderboard", timeout=30).json()
        row = [x for x in lb if x["id"] == test_user["id"]]
        if row:
            assert row[0]["points"] == after_delete

    def test_delete_open_duel_no_points_change(self, admin_headers, test_user):
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST OpenA", "shooter2": "TEST OpenB", "discipline": "TEST"}, timeout=30)
        did = r.json()["id"]
        requests.post(f"{API}/duels/{did}/tip", headers=test_user["headers"], json={"pick": "1"}, timeout=30)
        before = requests.get(f"{API}/auth/me", headers=test_user["headers"], timeout=30).json()["points"]
        assert requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=30).status_code == 200
        after = requests.get(f"{API}/auth/me", headers=test_user["headers"], timeout=30).json()["points"]
        assert after == before, "deleting an open duel (no correct tips) must not change points"

    def test_delete_wrong_tip_does_not_deduct(self, admin_headers, test_user):
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST WrA", "shooter2": "TEST WrB", "discipline": "TEST"}, timeout=30)
        did = r.json()["id"]
        # user tips '1' but result will be '2'
        requests.post(f"{API}/duels/{did}/tip", headers=test_user["headers"], json={"pick": "1"}, timeout=30)
        requests.post(f"{API}/duels/{did}/result", headers=admin_headers, json={"outcome": "2"}, timeout=30)
        before = requests.get(f"{API}/auth/me", headers=test_user["headers"], timeout=30).json()["points"]
        assert requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=30).status_code == 200
        after = requests.get(f"{API}/auth/me", headers=test_user["headers"], timeout=30).json()["points"]
        assert after == before, "deleting a duel where user tipped WRONG must not deduct"


# ---------- BUG 2: /api/upload + PATCH /api/duels + /api/files/{path} ----------
class TestUploadAndPatch:
    def test_upload_requires_admin(self, test_user):
        r = requests.post(f"{API}/upload",
                          files={"file": ("t.png", io.BytesIO(PNG_BYTES), "image/png")},
                          headers=test_user["headers"], timeout=30)
        assert r.status_code == 403

    def test_upload_unauthenticated(self):
        r = requests.post(f"{API}/upload",
                          files={"file": ("t.png", io.BytesIO(PNG_BYTES), "image/png")}, timeout=30)
        assert r.status_code == 401

    def test_upload_rejects_non_image(self, admin_headers):
        r = requests.post(f"{API}/upload",
                          files={"file": ("bad.txt", io.BytesIO(b"hello"), "text/plain")},
                          headers=admin_headers, timeout=30)
        assert r.status_code == 400

    def test_upload_and_serve_image(self, admin_headers):
        r = requests.post(f"{API}/upload",
                          files={"file": ("shooter.png", io.BytesIO(PNG_BYTES), "image/png")},
                          headers=admin_headers, timeout=60)
        assert r.status_code == 200, r.text
        url = r.json()["url"]
        assert url.startswith("/api/files/"), url
        # fetch through public route
        served = requests.get(f"{BASE_URL}{url}", timeout=60)
        assert served.status_code == 200
        assert served.headers.get("content-type", "").startswith("image/")
        assert served.content == PNG_BYTES

    def test_patch_duel_updates_shooter_images(self, admin_headers):
        # create a duel
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST PatchA", "shooter2": "TEST PatchB", "discipline": "TEST"}, timeout=30)
        did = r.json()["id"]

        # upload two images
        u1 = requests.post(f"{API}/upload",
                           files={"file": ("a.png", io.BytesIO(PNG_BYTES), "image/png")},
                           headers=admin_headers, timeout=60).json()["url"]
        u2 = requests.post(f"{API}/upload",
                           files={"file": ("b.png", io.BytesIO(PNG_BYTES), "image/png")},
                           headers=admin_headers, timeout=60).json()["url"]

        # PATCH the duel with images
        r = requests.patch(f"{API}/duels/{did}", headers=admin_headers,
                          json={"shooter1_img": u1, "shooter2_img": u2}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["shooter1_img"] == u1
        assert d["shooter2_img"] == u2

        # persisted via GET
        got = requests.get(f"{API}/duels/{did}", timeout=30).json()
        assert got["shooter1_img"] == u1
        assert got["shooter2_img"] == u2

        # cleanup
        requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=30)

    def test_patch_duel_requires_admin(self, admin_headers, test_user):
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST X", "shooter2": "TEST Y", "discipline": "TEST"}, timeout=30)
        did = r.json()["id"]
        r = requests.patch(f"{API}/duels/{did}", headers=test_user["headers"],
                           json={"shooter1_img": "/x"}, timeout=30)
        assert r.status_code == 403
        requests.delete(f"{API}/duels/{did}", headers=admin_headers, timeout=30)

    def test_patch_nonexistent_duel_returns_404(self, admin_headers):
        r = requests.patch(f"{API}/duels/000000000000000000000000", headers=admin_headers,
                           json={"shooter1_img": "/x"}, timeout=30)
        assert r.status_code == 404


# ---------- BUG 3 (backend support): status filter for admin tabs ----------
class TestDuelStatusFilterForTabs:
    def test_open_and_finished_status_filters(self, admin_headers):
        # ensure at least one of each
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST TabA", "shooter2": "TEST TabB", "discipline": "TEST"}, timeout=30)
        open_id = r.json()["id"]
        r = requests.post(f"{API}/duels", headers=admin_headers, json={
            "shooter1": "TEST TabC", "shooter2": "TEST TabD", "discipline": "TEST"}, timeout=30)
        fin_id = r.json()["id"]
        requests.post(f"{API}/duels/{fin_id}/result", headers=admin_headers,
                      json={"outcome": "1"}, timeout=30)

        openl = requests.get(f"{API}/duels?status=open", timeout=30).json()
        finl = requests.get(f"{API}/duels?status=finished", timeout=30).json()

        assert any(d["id"] == open_id for d in openl)
        assert all(d["status"] == "open" for d in openl)
        assert any(d["id"] == fin_id for d in finl)
        assert all(d["status"] == "finished" for d in finl)
        assert not any(d["id"] == fin_id for d in openl)
        assert not any(d["id"] == open_id for d in finl)

        # cleanup
        requests.delete(f"{API}/duels/{open_id}", headers=admin_headers, timeout=30)
        requests.delete(f"{API}/duels/{fin_id}", headers=admin_headers, timeout=30)
