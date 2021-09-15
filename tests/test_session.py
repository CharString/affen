# SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica
#
# SPDX-License-Identifier: MPL-2.0

from urllib.parse import urlparse

import pytest
from hypothesis import given
from hypothesis.provisional import urls

from affen import Session, api


@given(urls())
def test_root_always_endswith_single_slash(url):
    plone = Session(api_root=url)
    parts_in = urlparse(url)
    parts_out = urlparse(plone.root)
    assert plone.root.endswith("/")
    assert not plone.root.endswith("//")
    assert parts_out[:2] == parts_in[:2]  # scheme and host are untouched
    assert parts_out[3] == parts_in[3].replace("//", "/")  # path is "the same"


def test_changing_root_unauthenticates(plone):
    assert plone.auth
    assert "admin" in repr(plone)
    plone.root = "https://example.com"
    assert not plone.auth
    assert "Authorization" not in plone.headers
    assert api.ANONYMOUS_USER in repr(plone)


@pytest.mark.skip
@pytest.mark.vcr
def test_changing_root_invalidates_token():
    plone = Session()
    plone.login("admin", "admin")
    assert plone.get("@registry").ok
    old_root = plone.root
    old_token = plone.headers["authorization"]
    # change
    plone.root = "https://example.com"
    # change back
    plone.root = old_root
    plone.headers["authorization"] = old_token
    assert not plone.get("@registry").ok


def test_does_not_unauthenticate_when_root_stays_the_same():
    plone = Session(api_root="https://example.com/")
    plone.auth = ("admin", "admin")
    plone.headers["authorization"] = "Bearer deadbeef1234"

    plone.root = "https://example.com"
    assert plone.auth == ("admin", "admin")
    assert plone.headers["authorization"] == "Bearer deadbeef1234"


def test_repr():
    s = repr(Session())
    assert api.ANONYMOUS_USER in s
    assert "affen" in s
    assert "Session" in s


@pytest.mark.vcr
def test_constructor_authenticates_with_basic_authentication(plone_site):
    plone = Session("admin", "admin")
    assert plone.auth == ("admin", "admin")


def test_repr_shows_user(plone):
    assert "admin" in repr(plone)


@pytest.mark.vcr
def test_iterating_over_folder(plone):
    resp = plone.post(
        "", json={"@type": "Folder", "title": "Folder Iteration"}
    )
    assert resp.ok
    folder_url = resp.json()["@id"]
    for i in range(50):
        page = plone.post(
            folder_url, json={"@type": "Document", "title": f"Page {i} test."}
        )
        assert page.ok, page.json()

    page_titles = [p["title"] for p in plone.items(folder_url)]
    assert set(page_titles) == set([f"Page {i} test." for i in range(50)])
    iterator = plone.items(folder_url)
    assert len(iterator) == 50
    assert "folder-iteration" in repr(iterator)


@pytest.mark.vcr
def test_items_raises_error_on_bad_response():
    not_plone = Session("foo", "bar", "https://example.com")
    with pytest.raises(TypeError):
        next(not_plone.items("/"))


def test_missing_restapi(vcr):
    with vcr.use_cassette("mixtapes/restapi_not_installed.yaml"):
        with pytest.raises(RuntimeError):
            plone = Session()
            plone.login("admin", "admin")


@pytest.mark.vcr
def test_login_sets_token():
    plone = Session()
    plone.login("admin", "admin")
    assert plone.headers["authorization"].startswith("Bearer")


@pytest.mark.vcr
def test_wrong_credentials():
    with pytest.raises(ValueError) as info:
        Session().login("foo", "bar")


@pytest.mark.vcr
def test_does_not_leak_authentication(plone):
    with pytest.raises(ValueError) as info:
        response = plone.get("https://httpbin.org/headers")
    assert "http://127.0.0.1:8080/Plone" in str(info.value)


@pytest.mark.vcr
def test_accepts_absolute_paths_even_if_api_root_is_not_at_host_root(plone):
    assert plone.get("/@search").ok


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["authorization"],
        "record_mode": "once",
    }
