# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import io

import pytest
from django.core.management.base import CommandError

from plane.vj_startups.management.commands.import_team_members import (
    build_headline,
    clean_email,
    clean_name,
    clean_photo_url,
    clean_url,
    parse_role,
    parse_rows,
    split_name,
)

# Shaped like the real team sheet (multi-line phone header, blank spacer rows,
# a row with no email) but with invented people.
SHEET = (
    "Display Name,Roll Number,Wing Name,Role,Department,Year,email-id,LInkedin (ifany),"
    '"Phone Number \n(must for - Wing Master)",Photo (Drive link),Insta (optional)\n'
    "Asha Rao,00A00A0000,Vision,Wing Master - Vision and Strategy,Information Technology,3rd Year,"
    "asha@example.com ,https://www.linkedin.com/in/asha?utm_source=share,9999999999,,\n"
    ",,Vision,,,,,,,,\n"
    ",,,,,,,,,,\n"
    "Ms.Meera,,Echo,wing member - Posters,CSE-AIML ,3rd Year,MEERA@Example.com,,,,\n"
    "Kiran Das,,Infra,Wing Member,,,,,,,\n"
)


@pytest.mark.unit
class TestTeamSheetParsing:
    def test_clean_name_strips_titles_and_fixes_lowercase(self):
        assert clean_name("Ms.Jasvini") == "Jasvini"
        assert clean_name("Mr. Anirudh") == "Anirudh"
        assert clean_name("Ms. sahithi varma") == "Sahithi Varma"
        assert clean_name("G. Sriram Charan") == "G. Sriram Charan"
        assert clean_name("Drake Miller") == "Drake Miller"

    def test_split_name(self):
        assert split_name("Asha Rao") == ("Asha", "Rao")
        assert split_name("Prince") == ("Prince", "")

    def test_clean_email_lowercases_trims_and_rejects_junk(self):
        assert clean_email(" Foo@Example.COM ") == "foo@example.com"
        assert clean_email("not-an-email") == ""
        assert clean_email("") == ""

    def test_clean_url_drops_tracking_params_and_non_urls(self):
        assert clean_url("https://www.linkedin.com/in/x?utm_source=share&y=1") == "https://www.linkedin.com/in/x"
        assert clean_url("Vahini Muttineni Photo") == ""

    def test_parse_role_normalises_case_and_keeps_focus(self):
        assert parse_role("wing member - ProblemHunt ") == (False, "Wing Member - ProblemHunt")
        assert parse_role("Wing Master - Financial Support- External Schemes") == (
            True,
            "Wing Master - Financial Support- External Schemes",
        )
        assert parse_role("Wing member ") == (False, "Wing Member")
        assert parse_role("") == (False, "Wing Member")

    def test_build_headline(self):
        assert build_headline("CSE-AIML ", "3rd Year") == "CSE-AIML - 3rd Year"
        assert build_headline("", "2nd year") == "2nd year"
        assert build_headline("", "") == ""

    def test_parse_rows_skips_blank_spacer_rows_and_maps_columns(self):
        rows = list(parse_rows(io.StringIO(SHEET)))
        assert [r["name"] for r in rows] == ["Asha Rao", "Meera", "Kiran Das"]
        asha, meera, kiran = rows
        assert asha["email"] == "asha@example.com"
        assert asha["is_master"] is True
        assert asha["linkedin"] == "https://www.linkedin.com/in/asha"
        assert asha["headline"] == "Information Technology - 3rd Year"
        assert meera["email"] == "meera@example.com"
        assert meera["role"] == "Wing Member - Posters"
        assert kiran["email"] == ""

    def test_parse_rows_never_exposes_phone_or_roll_number(self):
        for row in parse_rows(io.StringIO(SHEET)):
            assert "9999999999" not in str(row)
            assert "00A00A0000" not in str(row)

    def test_parse_rows_errors_clearly_when_columns_are_missing(self):
        with pytest.raises(CommandError):
            list(parse_rows(io.StringIO("Foo,Bar\n1,2\n")))


@pytest.mark.unit
class TestPhotoAndInstagram:
    def test_a_drive_share_link_becomes_a_loadable_image_url(self):
        expected = "https://drive.google.com/thumbnail?id=1AbCdEfGhIjKlMnOp&sz=w600"

        assert clean_photo_url("https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view?usp=sharing") == expected
        assert clean_photo_url("https://drive.google.com/open?id=1AbCdEfGhIjKlMnOp") == expected

    def test_other_values_are_kept_only_when_they_are_urls(self):
        assert clean_photo_url("https://example.com/me.jpg") == "https://example.com/me.jpg"
        assert clean_photo_url("Vahini Muttineni Photo") == ""
        assert clean_photo_url("https://drive.google.com/drive/folders/") == ""

    def test_only_the_real_drive_host_is_rewritten(self):
        lookalike = "https://evil.example/drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view"

        assert clean_photo_url(lookalike) == lookalike
        assert clean_photo_url("see drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view") == ""
        assert clean_photo_url("") == ""

    def test_the_sheet_photo_and_instagram_columns_are_read(self):
        sheet = (
            "Display Name,Wing Name,Role,email-id,Photo (Drive link),Insta (optional)\n"
            "Asha Rao,Vision,Wing Master,asha@example.com,"
            "https://drive.google.com/file/d/1AbCdEfGhIjKlMnOp/view,https://instagram.com/asha?igsh=x\n"
        )

        (row,) = list(parse_rows(io.StringIO(sheet)))

        assert row["photo"] == "https://drive.google.com/thumbnail?id=1AbCdEfGhIjKlMnOp&sz=w600"
        assert row["instagram"] == "https://instagram.com/asha"
