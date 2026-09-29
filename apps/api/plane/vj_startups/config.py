"""
Deployment-specific settings for VJ Startups, read from the environment.

Nothing here may be a value that differs between environments (hostnames, the
college email domain, where backend 2 lives) - those belong in one place so a
change of domain is a settings change, not a code change.
"""

import os

from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException

# The public marketing site. "www" is the host that actually resolves today;
# set VJ_PUBLIC_SITE_URL to change it (e.g. once the bare domain has DNS).
DEFAULT_PUBLIC_SITE_URL = "https://www.vjstartup.com"

# Email domain(s) whose owners are auto-onboarded into the global workspace.
DEFAULT_INSTITUTIONAL_EMAIL_DOMAINS = "vnrvjiet.in"

# Only ever used in local development (DEBUG on), where backend 2 runs beside the API.
LOCAL_MICROSERVICE_URL = "http://localhost:6220"


class MicroserviceNotConfigured(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "VJ_MICROSERVICE_URL is not set on the API, so it cannot reach the ecosystem service."
    default_code = "microservice_not_configured"


def public_site_url():
    """Base URL of the public site, without a trailing slash."""
    return (os.environ.get("VJ_PUBLIC_SITE_URL") or DEFAULT_PUBLIC_SITE_URL).strip().rstrip("/")


def institutional_email_domains():
    """Lower-case email domains (no '@') from VJ_INSTITUTIONAL_EMAIL_DOMAINS, comma separated."""
    raw = os.environ.get("VJ_INSTITUTIONAL_EMAIL_DOMAINS") or DEFAULT_INSTITUTIONAL_EMAIL_DOMAINS
    return [d.strip().lstrip("@").lower() for d in raw.split(",") if d.strip()]


def is_institutional_email(email):
    email = (email or "").strip().lower()
    return any(email.endswith("@" + domain) for domain in institutional_email_domains())


def microservice_base_url():
    """
    Base URL of backend 2 (the ecosystem service), or None when it is not
    configured. It never silently falls back to localhost in production: a
    missing setting used to make the API call itself and fail confusingly.
    """
    url = os.environ.get("VJ_MICROSERVICE_URL") or os.environ.get("NEXT_PUBLIC_MICROSERVICE_URL")
    if url:
        return url.strip().rstrip("/")
    return LOCAL_MICROSERVICE_URL if settings.DEBUG else None


def require_microservice_base_url():
    """Like microservice_base_url() but raises a clear 503 when it is not configured."""
    url = microservice_base_url()
    if url is None:
        raise MicroserviceNotConfigured()
    return url
