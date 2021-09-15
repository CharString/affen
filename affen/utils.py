# SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica
#
# SPDX-License-Identifier: MPL-2.0

from html.parser import HTMLParser
from typing import TYPE_CHECKING, Iterable, Optional, Sequence, Tuple

if TYPE_CHECKING:
    from . import Session


class BatchingIterator:
    def __init__(self, url: str, iterable: Iterable[dict], length: int):
        self.url = url
        self.iterator = iter(iterable)
        self.length = length

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.url}>"

    def __len__(self) -> int:
        return self.length

    def __iter__(self):
        return self.iterator

    def __next__(self):
        return next(self.iterator)


class Registry:
    """Dict-implementation of @registry endpoint

    Supports:

    Reading registry records:
    >>> session.registry['plone.app.querystring.field.path.title']
    'Location'

    Updating registry records:
    >>> session.registry['plone.app.querystring.field.path.title'] = 'Value'
    >>> session.registry['plone.app.querystring.field.path.title']
    'Value'

    >>> session.registry['plone.app.querystring.field.path.title'] = 1
    Traceback (most recent call last):
    ...
    ValueError: (1, <type 'unicode'>, 'value')


    See https://plonerestapi.readthedocs.io/en/latest/registry.html
    """

    def __init__(self, session: "Session"):
        self._session = session
        self._url = f"@registry"

    def __getitem__(self, key):
        resp = self._session.get(f"{self._url}/{key}")
        if resp.ok:
            return resp.json()
        error = resp.json()
        if (
            resp.status_code == 503
            and error["type"] == "KeyError"
            and key in error["message"]
        ):
            raise KeyError(key)
        else:
            resp.raise_for_status()

    def __setitem__(self, key, value):
        self.update({key: value})

    def update(self, *args, **kwargs):
        "Update registry like `dict.update` would"
        d = {}
        d.update(*args, **kwargs)
        resp = self._session.patch(f"{self._url}", json=d)
        if resp.ok:
            return
        if resp.status_code == 500:
            error = resp.json()
            if error["type"] == "WrongType":
                exc = ValueError(error["message"])
                exc.response = resp
                raise exc
        resp.raise_for_status()

    def __len__(self) -> int:
        resp = self._session.get(f"{self._url}")
        resp.raise_for_status()
        return resp.json()["items_total"]

    def __iter__(self):
        return iter(
            item["name"] for item in self._session.items(f"{self._url}")
        )
