# SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica
#
# SPDX-License-Identifier: MPL-2.0

import pytest


@pytest.mark.vcr
def test_registry_raises_keyerror(plone):
    with pytest.raises(KeyError) as info:
        plone.registry["plone-restapi-client-testkey"]
    assert "'plone-restapi-client-testkey'" in str(info.value)


@pytest.mark.vcr
def test_registry_raises_valueerror(plone):
    with pytest.raises(ValueError) as info:
        plone.registry["plone.allow_anon_views_about"] = "Should be bool"


@pytest.mark.vcr
def test_registry_raises_notimplementederror(plone):
    "Creating new keys isn't implemented"
    with pytest.raises(NotImplementedError) as info:
        plone.registry["nuskool"] = "The new oldskool"


@pytest.mark.vcr
def test_registry_implements_len(plone):
    assert len(plone.registry) > 0


@pytest.mark.vcr
def test_registry_implements_iteration(plone):
    for key in plone.registry:
        assert key
        break  # datetime values still throw a 500 error


@pytest.mark.vcr
def test_editing_registry(plone):
    plone.registry["plone.allow_anon_views_about"] = True
    assert plone.registry["plone.allow_anon_views_about"] == True
    plone.registry["plone.allow_anon_views_about"] = False
    assert plone.registry["plone.allow_anon_views_about"] == False


@pytest.mark.vcr
def test_registry_update(plone):
    plone.registry.update(
        {
            "plone.allow_anon_views_about": False,
            "plone.always_show_selector": False,
        }
    )
    assert plone.registry["plone.allow_anon_views_about"] == False
    assert plone.registry["plone.always_show_selector"] == False
