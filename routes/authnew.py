"""JWT helpers for browser cookies and API Bearer tokens."""

from datetime import datetime, timedelta, timezone
from functools import wraps
import logging

import jwt
from flask import current_app, g, jsonify, redirect, request, url_for, flash

from models import User, db

logger = logging.getLogger(name)

COOKIE_NAME = "access_token"


def _ttl_seconds():
    return int(current_app.config.get("JWT_TTL_SECONDS", 7200))


def _secret():
    return current_app.config["JWT_SECRET_KEY"]


def _algorithm():
    return current_app.config.get("JWT_ALGORITHM", "HS256")


def create_token(user):
    """Create a signed JWT for the given User model instance."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "user_id": user.id,
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(seconds=_ttl_seconds()),
    }
    return jwt.encode(payload, _secret(), algorithm=_algorithm())


def extract_token():
    """Read JWT from Authorization: Bearer ... or access_token cookie."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip() or None
    return request.cookies.get(COOKIE_NAME) or None


def decode_token(token):
    """Decode and validate JWT. Raises jwt exceptions on failure."""
    return jwt.decode(token, _secret(), algorithms=[_algorithm()])


def get_current_user():
    """Load User from JWT (cached on flask.g for the request)."""
    if "jwt_user" in g:
        return g.jwt_user

    token = extract_token()
    if not token:
        g.jwt_user = None
        return None

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        logger.info("[JWT] token expired")
        g.jwt_user = None
        return None
    except jwt.InvalidTokenError:
        logger.info("[JWT] invalid token")
        g.jwt_user = None
        return None

    user_id = payload.get("user_id") or payload.get("sub")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        g.jwt_user = None
        return None

    user = db.session.get(User, user_id)
    g.jwt_user = user
    g.jwt_payload = payload
    return user


def set_auth_cookie(response, token):
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=_ttl_seconds(),
        httponly=True,
        samesite="Lax",
        secure=bool(current_app.config.get("JWT_COOKIE_SECURE", False)),
    )
    return response


def clear_auth_cookie(response):
    response.delete_cookie(COOKIE_NAME)
    return response


def login_required(view):
    """HTML routes: redirect to login if there is no valid JWT."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Please login first", "danger")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    """HTML admin routes: require JWT + role admin."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            flash("Access denied", "danger")
            return redirect(url_for("auth.login"))
        if user.role != "admin":
            flash("Access denied", "danger")
            return redirect(url_for("shop.index"))
        return view(*args, **kwargs)

    return wrapped


def token_required(view):
    """API routes: return JSON 401 if Bearer/cookie JWT is missing or invalid."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        token = extract_token()
        if not token:
            logger.info("[JWT] protected route called without token")
            return jsonify({"error": "Authorization: Bearer <token> required"}), 401

        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            logger.info("[JWT] token expired")
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            logger.info("[JWT] invalid token")
            return jsonify({"error": "Invalid token"}), 401

        user_id = payload.get("user_id") or payload.get("sub")
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid token"}), 401

        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 401

        request.user = user
        request.jwt_payload = payload
        g.jwt_user = user
        return view(*args, **kwargs)

    return wrapped


def admin_token_required(view):
    """API admin routes: JWT + role admin."""

    @wraps(view)
    @token_required
    def wrapped(*args, **kwargs):
        if getattr(request, "user", None) is None or request.user.role != "admin":
            logger.info("[JWT] admin denied")
            return jsonify({"error": "Admins only"}), 403
        return view(*args, **kwargs)

    return wrapped