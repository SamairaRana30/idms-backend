from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token


def test_password_hashing():
    hashed = get_password_hash("testpassword")
    assert verify_password("testpassword", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_token():
    token = create_access_token({"sub": "admin", "role": "admin"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "admin"


def test_invalid_token():
    assert decode_access_token("invalid.token.here") is None
