# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest
from django.test import override_settings

from plane.vj_startups import config


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in (
        "VJ_PUBLIC_SITE_URL",
        "VJ_INSTITUTIONAL_EMAIL_DOMAINS",
        "VJ_MICROSERVICE_URL",
        "NEXT_PUBLIC_MICROSERVICE_URL",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.unit
class TestPublicSiteUrl:
    def test_defaults_to_the_host_that_resolves(self):
        assert config.public_site_url() == "https://www.vjstartup.com"

    def test_can_be_overridden_and_loses_the_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("VJ_PUBLIC_SITE_URL", "https://vjstartup.com/")
        assert config.public_site_url() == "https://vjstartup.com"

    def test_a_blank_value_falls_back_to_the_default(self, monkeypatch):
        monkeypatch.setenv("VJ_PUBLIC_SITE_URL", "")
        assert config.public_site_url() == config.DEFAULT_PUBLIC_SITE_URL


@pytest.mark.unit
class TestInstitutionalEmail:
    def test_default_domain(self):
        assert config.institutional_email_domains() == ["vnrvjiet.in"]
        assert config.is_institutional_email("Someone@VNRVJIET.in")

    def test_other_domains_are_not_institutional(self):
        assert not config.is_institutional_email("someone@gmail.com")
        assert not config.is_institutional_email("someone@notvnrvjiet.in")
        assert not config.is_institutional_email("")
        assert not config.is_institutional_email(None)

    def test_multiple_domains_and_at_signs_are_tolerated(self, monkeypatch):
        monkeypatch.setenv("VJ_INSTITUTIONAL_EMAIL_DOMAINS", "@vnrvjiet.in, Example.EDU ,")
        assert config.institutional_email_domains() == ["vnrvjiet.in", "example.edu"]
        assert config.is_institutional_email("a@example.edu")


@pytest.mark.unit
class TestMicroserviceUrl:
    def test_uses_the_configured_url_without_a_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("VJ_MICROSERVICE_URL", "http://host.docker.internal:6220/")
        assert config.microservice_base_url() == "http://host.docker.internal:6220"

    def test_falls_back_to_the_legacy_variable(self, monkeypatch):
        monkeypatch.setenv("NEXT_PUBLIC_MICROSERVICE_URL", "http://legacy:6220")
        assert config.microservice_base_url() == "http://legacy:6220"

    def test_never_falls_back_to_localhost_in_production(self):
        with override_settings(DEBUG=False):
            assert config.microservice_base_url() is None
            with pytest.raises(config.MicroserviceNotConfigured) as excinfo:
                config.require_microservice_base_url()
        assert excinfo.value.status_code == 503

    def test_localhost_is_only_a_development_default(self):
        with override_settings(DEBUG=True):
            assert config.microservice_base_url() == config.LOCAL_MICROSERVICE_URL
