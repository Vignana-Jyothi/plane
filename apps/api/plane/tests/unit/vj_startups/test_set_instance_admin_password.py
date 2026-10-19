# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.vj_startups.management.commands.set_instance_admin_password import (
    MIN_LENGTH,
    check_new_password,
    refusal_reason,
)


@pytest.mark.unit
class TestNewPassword:
    def test_a_strong_password_is_accepted_unchanged(self):
        assert check_new_password("Xq7#mV9!rT2@pLw5") == "Xq7#mV9!rT2@pLw5"

    @pytest.mark.parametrize("empty", ["", "   ", None])
    def test_an_empty_password_is_refused_with_a_hint_about_where_it_comes_from(self, empty):
        with pytest.raises(ValueError, match="VJ_NEW_PASSWORD"):
            check_new_password(empty)

    def test_a_short_password_is_refused(self):
        with pytest.raises(ValueError, match="too short"):
            check_new_password("aB3$" * ((MIN_LENGTH - 1) // 4) + "x")

    @pytest.mark.parametrize("weak", ["passwordpassword", "123456789012", "qwertyuiopasdf"])
    def test_a_guessable_password_is_refused(self, weak):
        with pytest.raises(ValueError, match="easy to guess"):
            check_new_password(weak)

    def test_the_reason_never_contains_the_password(self):
        secret = "passwordpassword"
        with pytest.raises(ValueError) as err:
            check_new_password(secret)
        assert secret not in str(err.value)


@pytest.mark.unit
class TestEligibility:
    def test_an_instance_admin_may_be_reset(self):
        assert refusal_reason(True, True, True, False) is None

    def test_a_superuser_may_be_reset(self):
        assert refusal_reason(True, True, False, True) is None

    def test_an_ordinary_member_is_refused(self):
        assert "not an Instance Admin" in refusal_reason(True, True, False, False)

    def test_a_missing_account_is_refused(self):
        assert "No Plane account" in refusal_reason(False, False, False, False)

    def test_a_deactivated_admin_is_refused(self):
        assert "deactivated" in refusal_reason(True, False, True, True)
