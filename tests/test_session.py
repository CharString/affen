from urllib.parse import urlparse

import pytest
from hypothesis import given
from hypothesis.provisional import urls

from plone_restapi_client import Session, api


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
    assert "Authentication" not in plone.headers
    assert api.ANONYMOUS_USER in repr(plone)


def test_does_not_unauthenticate_when_root_stays_the_same():
    plone = Session(api_root="https://example.com/")
    plone.auth = ("admin", "admin")
    plone.headers["Authentication"] = "Bearer deadbeef1234"

    plone.root = "https://example.com"
    assert plone.auth == ("admin", "admin")
    assert plone.headers["Authentication"] == "Bearer deadbeef1234"


def test_repr():
    s = repr(Session())
    assert api.ANONYMOUS_USER in s
    assert "plone_restapi_client" in s
    assert "Session" in s


@pytest.mark.vcr
def test_constructor_authenticates(plone_site):
    plone = Session("admin", "admin")
    assert plone.auth == ("admin", "admin")
    assert plone.headers["Authentication"].startswith("Bearer")


def test_repr_shows_user(plone):
    assert "admin" in repr(plone)


@pytest.mark.vcr
def test_iterating_over_foler(plone):
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


def test_missing_restapi(vcr):
    with vcr.use_cassette("mixtapes/restapi_not_installed.yaml"):
        with pytest.raises(RuntimeError):
            plone = Session("admin", "admin")


@pytest.mark.vcr
def test_wrong_credentials():
    with pytest.raises(ValueError) as info:
        plone = Session("foo", "bar")


@pytest.mark.vcr
def test_does_not_leak_authentication(plone):
    with pytest.raises(ValueError):
        response = plone.get("https://httpbin.org/headers")


@pytest.fixture(scope="module")
def vcr_config():
    return {
        "filter_headers": ["authorization", "authentication"],
        "record_mode": "none",
    }
