import pytest

from publisher.refresh_token import REFRESH_URL, refresh_token


class FakeResponse:
    def __init__(self, status, payload):
        self.status_code, self.payload = status, payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.response


def test_refresh_returns_new_token_and_lifetime():
    session = FakeSession(FakeResponse(200, {"access_token": "new", "token_type": "bearer",
                                             "expires_in": 5184000}))
    assert refresh_token("old", session=session) == ("new", 5184000)
    assert session.calls == [(REFRESH_URL, {"grant_type": "ig_refresh_token", "access_token": "old"})]


def test_refresh_error_message_never_contains_token():
    session = FakeSession(FakeResponse(400, {"error": {"message": "Session has expired"}}))
    with pytest.raises(RuntimeError) as info:
        refresh_token("secret-old-token", session=session)
    assert "Session has expired" in str(info.value)
    assert "secret-old-token" not in str(info.value)
