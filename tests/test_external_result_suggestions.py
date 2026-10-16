import os
import uuid


os.environ["DATABASE_URL"] = f"sqlite:////tmp/skyteduellene-test-{uuid.uuid4().hex}.db"
os.environ["JWT_SECRET_KEY"] = "test-secret"

import app as app_module  # noqa: E402
from flask_jwt_extended import create_access_token  # noqa: E402


app = app_module.app
db = app_module.db
User = app_module.User
Duel = app_module.Duel
Tip = app_module.Tip
PointRecord = app_module.PointRecord
ExternalResultSuggestion = app_module.ExternalResultSuggestion


def _auth_header(user_id):
    with app.app_context():
        token = create_access_token(identity=str(user_id))
    return {"Authorization": "Bearer " + token}


def _seed_users_and_duel():
    admin = User(
        username="Sverre Hårstad",
        email=f"admin-{uuid.uuid4().hex[:8]}@local.invalid",
    )
    admin.set_password("secret123")
    user = User(
        username="Testbruker",
        email=f"user-{uuid.uuid4().hex[:8]}@local.invalid",
    )
    user.set_password("secret123")
    duel = Duel(
        shooter1="Skytter A",
        shooter2="Skytter B",
        discipline="100m",
        external_source="mittdfs",
        external_event_url="https://mittdfs.no/resultat/123",
    )
    db.session.add_all([admin, user, duel])
    db.session.commit()
    return admin, user, duel


def setup_function():
    app.config["TESTING"] = True
    with app.app_context():
        db.drop_all()
        db.create_all()


def test_fetch_suggestion_serialization_and_counts(monkeypatch):
    with app.app_context():
        admin, _, duel = _seed_users_and_duel()
        admin_id = admin.id
        duel_id = duel.id

    def fake_fetch(_duel):
        return {
            "status": "suggested",
            "status_reason": "exact_match",
            "suggested_shooter1_name": "Skytter A",
            "suggested_shooter2_name": "Skytter B",
            "suggested_score1": "99",
            "suggested_score2": "97",
            "suggested_outcome": "1",
            "raw_source_data": {"raw": True},
            "normalized_source_data": {"match": "exact"},
            "event_url": "https://mittdfs.no/resultat/123",
        }

    monkeypatch.setattr(app_module.external_result_service, "fetch_suggestion", fake_fetch)

    client = app.test_client()
    headers = _auth_header(admin_id)
    response = client.post(f"/api/admin/duels/{duel_id}/result-suggestions/fetch", headers=headers)
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "suggested"
    assert payload["raw_source_data"] == {"raw": True}
    assert payload["normalized_source_data"] == {"match": "exact"}

    listed = client.get("/api/admin/result-suggestions", headers=headers)
    assert listed.status_code == 200
    data = listed.get_json()
    assert data["counts"]["suggested"] >= 1
    assert any(item["duel_id"] == duel_id for item in data["items"])


def test_approval_reuses_duel_result_points_logic(monkeypatch):
    with app.app_context():
        admin, user, duel = _seed_users_and_duel()
        db.session.add(Tip(user_id=user.id, duel_id=duel.id, pick="1"))
        db.session.commit()
        admin_id = admin.id
        user_id = user.id
        duel_id = duel.id

    def fake_fetch(_duel):
        return {
            "status": "suggested",
            "suggested_score1": "100",
            "suggested_score2": "98",
            "suggested_outcome": "1",
        }

    monkeypatch.setattr(app_module.external_result_service, "fetch_suggestion", fake_fetch)

    client = app.test_client()
    headers = _auth_header(admin_id)
    fetch = client.post(f"/api/admin/duels/{duel_id}/result-suggestions/fetch", headers=headers).get_json()
    approve = client.post(
        f"/api/admin/duels/{duel_id}/result-suggestions/{fetch['id']}/approve",
        headers=headers,
        json={},
    )
    assert approve.status_code == 200

    with app.app_context():
        duel = Duel.query.get(duel_id)
        assert duel.status == "finished"
        assert duel.outcome == "1"
        record = PointRecord.query.filter_by(duel_id=duel_id, user_id=user_id).first()
        assert record is not None
        assert record.points == 1
        suggestion = ExternalResultSuggestion.query.get(fetch["id"])
        assert suggestion.status == "approved"
        assert suggestion.approved_by_user_id == admin_id


def test_reject_then_approve_requires_explicit_reprocess(monkeypatch):
    with app.app_context():
        admin, _, duel = _seed_users_and_duel()
        admin_id = admin.id
        duel_id = duel.id

    monkeypatch.setattr(
        app_module.external_result_service,
        "fetch_suggestion",
        lambda _duel: {"status": "suggested", "suggested_score1": "95", "suggested_score2": "95", "suggested_outcome": "X"},
    )

    client = app.test_client()
    headers = _auth_header(admin_id)
    suggestion = client.post(f"/api/admin/duels/{duel_id}/result-suggestions/fetch", headers=headers).get_json()

    rejected = client.post(
        f"/api/admin/duels/{duel_id}/result-suggestions/{suggestion['id']}/reject",
        headers=headers,
        json={"note": "Feil match"},
    )
    assert rejected.status_code == 200
    assert rejected.get_json()["status"] == "rejected"

    denied = client.post(
        f"/api/admin/duels/{duel_id}/result-suggestions/{suggestion['id']}/approve",
        headers=headers,
        json={},
    )
    assert denied.status_code == 400

    allowed = client.post(
        f"/api/admin/duels/{duel_id}/result-suggestions/{suggestion['id']}/approve",
        headers=headers,
        json={"allow_reprocess": True, "outcome": "X", "score1": "95", "score2": "95"},
    )
    assert allowed.status_code == 200


def test_needs_review_states_for_unavailable_and_ambiguous(monkeypatch):
    with app.app_context():
        admin, _, duel = _seed_users_and_duel()
        admin_id = admin.id
        duel_id = duel.id

    client = app.test_client()
    headers = _auth_header(admin_id)

    monkeypatch.setattr(
        app_module.external_result_service,
        "fetch_suggestion",
        lambda _duel: {"status": "needs_review", "status_reason": "source_unavailable"},
    )
    unavailable = client.post(f"/api/admin/duels/{duel_id}/result-suggestions/fetch", headers=headers)
    assert unavailable.status_code == 200
    assert unavailable.get_json()["status_reason"] == "source_unavailable"

    monkeypatch.setattr(
        app_module.external_result_service,
        "fetch_suggestion",
        lambda _duel: {"status": "needs_review", "status_reason": "ambiguous_match"},
    )
    ambiguous = client.post(f"/api/admin/duels/{duel_id}/result-suggestions/fetch", headers=headers)
    assert ambiguous.status_code == 200
    assert ambiguous.get_json()["status_reason"] == "ambiguous_match"
