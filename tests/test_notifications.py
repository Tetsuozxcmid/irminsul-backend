from app.core.security import create_jwt_pair


def test_create_notification_internal(client, user):
    r = client.post(
        "/api/notifications",
        json={
            "user_id": user.id,
            "title": "Новое сообщение",
            "source": "system",
            "payload": {"k": "v"},
            "idempotency_key": "idem-1",
        },
        headers={"X-Internal-Key": "test-internal-key"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Новое сообщение"
    assert data["source"] == "system"
    assert data["payload"] == {"k": "v"}
    assert data["read"] is False
    assert data["idempotency_key"] == "idem-1"
    assert data["user_id"] == user.id


def test_create_idempotent_returns_existing(client, user):
    body = {
        "user_id": user.id,
        "title": "A",
        "source": "s",
        "idempotency_key": "same-key",
    }
    r1 = client.post(
        "/api/notifications",
        json=body,
        headers={"X-Internal-Key": "test-internal-key"},
    )
    r2 = client.post(
        "/api/notifications",
        json=body,
        headers={"X-Internal-Key": "test-internal-key"},
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


def test_websocket_snapshot_unread(client, user):
    r = client.post(
        "/api/notifications",
        json={
            "user_id": user.id,
            "title": "WS test",
            "source": "test",
        },
        headers={"X-Internal-Key": "test-internal-key"},
    )
    assert r.status_code == 200

    access, _ = create_jwt_pair(user)
    with client.websocket_connect(
        "/api/notifications/ws",
        headers={"Cookie": f"access_token={access}"},
    ) as ws:
        first = ws.receive_json()
        assert first["type"] == "snapshot"
        assert len(first["items"]) >= 1
        titles = [x["title"] for x in first["items"]]
        assert "WS test" in titles


def test_websocket_receives_live_notification(client, user):
    access, _ = create_jwt_pair(user)
    with client.websocket_connect(
        "/api/notifications/ws",
        headers={"Cookie": f"access_token={access}"},
    ) as ws:
        ws.receive_json()
        client.post(
            "/api/notifications",
            json={
                "user_id": user.id,
                "title": "Live push",
                "source": "live",
            },
            headers={"X-Internal-Key": "test-internal-key"},
        )
        msg = ws.receive_json()
        assert msg["type"] == "notification"
        assert msg["item"]["title"] == "Live push"


def test_mark_notification_read(client, user):
    r = client.post(
        "/api/notifications",
        json={
            "user_id": user.id,
            "title": "Read me",
            "source": "test",
        },
        headers={"X-Internal-Key": "test-internal-key"},
    )
    nid = r.json()["id"]

    access, _ = create_jwt_pair(user)
    client.cookies.set("access_token", access)

    patch = client.patch(f"/api/notifications/{nid}", json={"read": True})
    assert patch.status_code == 200
    assert patch.json()["read"] is True

    listed = client.get("/api/notifications", params={"unread_only": True})
    assert listed.status_code == 200
    ids = [x["id"] for x in listed.json()]
    assert nid not in ids


def test_get_notifications_array_and_cursor(client, user):
    access, _ = create_jwt_pair(user)
    client.cookies.set("access_token", access)

    for i in range(3):
        client.post(
            "/api/notifications",
            json={
                "user_id": user.id,
                "title": f"T{i}",
                "source": "bulk",
            },
            headers={"X-Internal-Key": "test-internal-key"},
        )

    r = client.get("/api/notifications", params={"limit": 2})
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)
    assert len(arr) == 2
    next_c = r.headers.get("x-next-cursor")
    if next_c:
        r2 = client.get(
            "/api/notifications",
            params={"limit": 2, "cursor": int(next_c)},
        )
        assert r2.status_code == 200
        assert isinstance(r2.json(), list)
