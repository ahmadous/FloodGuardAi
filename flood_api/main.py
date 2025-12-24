from __future__ import annotations

from flask import Request

from flood_api.gateway.app import app as flask_app


def api(request: Request):
    """Entry point for Firebase Functions HTTP requests."""
    with flask_app.request_context(request.environ):
        response = flask_app.full_dispatch_request()
    return response

