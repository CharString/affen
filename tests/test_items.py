# SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica
#
# SPDX-License-Identifier: MPL-2.0

import pytest

from affen import Session
from affen.utils import BatchingIterator


@pytest.fixture
def folder(plone, vcr):
    with vcr.use_cassette("mixtapes/folder_with_50_items.yaml") as cassette:
        resp = plone.post(
            "", json={"@type": "Folder", "title": "Folder Iteration"}
        )
        assert resp.ok
        folder_url = resp.json()["@id"]
        for i in range(50):
            page = plone.post(
                folder_url,
                json={"@type": "Document", "title": f"Page {i} test."},
            )
            assert page.ok, page.json()
    yield folder_url


@pytest.mark.vcr
def test_iterating_over_folder(plone, folder):
    folder_url = folder
    page_titles = [p["title"] for p in plone.items(folder_url)]
    assert set(page_titles) == set([f"Page {i} test." for i in range(50)])
    iterator = plone.items(folder_url)
    assert len(iterator) == 50
    assert "folder-iteration" in repr(iterator)


@pytest.mark.vcr
def test_items_raises_error_on_bad_response():
    not_plone = Session("foo", "bar", "https://example.com")
    with pytest.raises(ValueError):
        next(not_plone.items("/"))


def test_getting_single_item_from_items(plone, folder, vcr_cassette):
    doc = plone.items(folder)[5]
    assert doc["title"] == "Page 5 test."
    assert vcr_cassette.play_count <= 1  # should be done in one request


def test_closed_slice_items(plone, folder, vcr_cassette):
    items = plone.items(folder)[25:35]
    assert len(items) == 10
    page_titles = set(p["title"] for p in items)
    assert page_titles == set([f"Page {i} test." for i in range(25, 35)])
    assert vcr_cassette.play_count <= 1  # should be done in one request


def test_half_open_slice_items(plone, folder, vcr_cassette):
    items = plone.items(folder)[:25]
    page_titles = set(p["title"] for p in items)
    assert page_titles == set([f"Page {i} test." for i in range(25)])


def test_open_ended_slice_items(plone, folder, vcr_cassette):
    items = plone.items(folder)[5:]
    page_titles = set(p["title"] for p in items)
    assert page_titles == set([f"Page {i} test." for i in range(5, 50)])
    if vcr_cassette.play_count:
        # recorded
        assert vcr_cassette.play_count > 1


@pytest.mark.vcr
def test_negative_indexing_raises_error(plone, folder):
    with pytest.raises(NotImplementedError):
        items = plone.items(folder)[-1]


@pytest.mark.vcr
def test_step_slice_raises_error(plone, folder):
    with pytest.raises(NotImplementedError):
        items = plone.items(folder)[1:26:8]
