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
        "VJ_WORKSPACE_ADMIN_WINGS",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.unit
class TestWingRoles:
    def test_every_wing_master_is_a_workspace_admin_by_default(self):
        assert config.workspace_admin_wing_slugs() == ["*"]
        for wing in ("vision", "ignition", "talent", "echo", "fuel", "infra", "any-new-wing"):
            assert config.workspace_role_for_wing(config.ROLE_ADMIN, wing) == config.ROLE_ADMIN, wing

    def test_wing_members_are_never_workspace_admins_through_their_wing(self):
        for wing in ("vision", "infra"):
            assert config.workspace_role_for_wing(config.ROLE_MEMBER, wing) == config.ROLE_MEMBER

    def test_a_missing_wing_slug_is_safe(self):
        assert config.workspace_role_for_wing(config.ROLE_ADMIN, None) == config.ROLE_ADMIN  # "*" covers it
        assert config.workspace_role_for_wing(config.ROLE_MEMBER, None) == config.ROLE_MEMBER

    def test_the_setting_can_limit_it_to_named_wings(self, monkeypatch):
        monkeypatch.setenv("VJ_WORKSPACE_ADMIN_WINGS", "Vision, infra ,")
        assert config.workspace_admin_wing_slugs() == ["vision", "infra"]
        assert config.workspace_role_for_wing(config.ROLE_ADMIN, "infra") == config.ROLE_ADMIN
        assert config.workspace_role_for_wing(config.ROLE_ADMIN, " Vision ") == config.ROLE_ADMIN
        assert config.workspace_role_for_wing(config.ROLE_ADMIN, "echo") == config.ROLE_MEMBER

    def test_a_named_wing_list_matches_exactly_not_by_substring(self, monkeypatch):
        monkeypatch.setenv("VJ_WORKSPACE_ADMIN_WINGS", "vision")
        assert config.workspace_role_for_wing(config.ROLE_ADMIN, "supervision") == config.ROLE_MEMBER
        assert config.workspace_role_for_wing(config.ROLE_ADMIN, None) == config.ROLE_MEMBER

    def test_an_empty_setting_makes_no_wing_master_a_workspace_admin(self, monkeypatch):
        monkeypatch.setenv("VJ_WORKSPACE_ADMIN_WINGS", "")
        assert config.workspace_admin_wing_slugs() == []
        assert config.workspace_role_for_wing(config.ROLE_ADMIN, "vision") == config.ROLE_MEMBER

    def test_a_higher_role_than_admin_still_counts_as_admin(self):
        assert config.workspace_role_for_wing(25, "vision") == config.ROLE_ADMIN


@pytest.mark.unit
class TestPlanWorkspaceMembership:
    def test_a_new_person_is_added_with_the_requested_role(self):
        assert config.plan_workspace_membership(None, False, 20) == ("add", 20)
        assert config.plan_workspace_membership(None, True, 15) == ("add", 15)

    def test_a_lower_active_role_is_raised(self):
        assert config.plan_workspace_membership(15, True, 20) == ("raise", 20)
        assert config.plan_workspace_membership(5, True, 15) == ("raise", 15)

    def test_the_same_or_a_higher_active_role_is_left_alone(self):
        assert config.plan_workspace_membership(20, True, 20) == ("keep", 20)
        assert config.plan_workspace_membership(20, True, 15) == ("keep", 20)
        assert config.plan_workspace_membership(15, True, 5) == ("keep", 15)

    def test_a_deactivated_membership_is_reactivated_and_never_lowered(self):
        assert config.plan_workspace_membership(15, False, 20) == ("reactivate", 20)
        assert config.plan_workspace_membership(20, False, 15) == ("reactivate", 20)
        assert config.plan_workspace_membership(5, False, 5) == ("reactivate", 5)

    def test_the_result_is_always_the_higher_of_the_current_and_requested_role(self):
        for current in (5, 15, 20):
            for requested in (5, 15, 20):
                for active in (True, False):
                    _, role = config.plan_workspace_membership(current, active, requested)
                    assert role == max(current, requested)


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
