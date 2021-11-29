# SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica
#
# SPDX-License-Identifier: MPL-2.0

from html.parser import HTMLParser
from typing import (
    TYPE_CHECKING,
    Generator,
    Iterable,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

import requests

if TYPE_CHECKING:
    import json

    import simplejson

    from . import Session

    JSONDecodeError: Union[
        Type[simplejson.JSONDecodeError], Type[json.JSONDecodeError]
    ]

try:
    from simplejson import JSONDecodeError
except ImportError:
    from json import JSONDecodeError


def _json(resp: requests.Response) -> dict:
    "Return dict or raise ValueError"
    try:
        d = resp.json()
    except JSONDecodeError as e:
        raise ValueError("Server did not return JSON") from e
    return d


class BatchingIterator:
    def __init__(self, url: str, session: "Session"):
        self.session = session
        self.url = url
        self._response = None
        self._iterator = None

    @property
    def response(self):
        if not self._response:
            self._response = self.session.get(self.url)
        return self._response

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.url}>"

    def __len__(self) -> int:
        d = self.response.json()
        return d.get("items_total", len(d.get("items", [])))

    def __iter__(self):
        if not self._iterator:
            self._iterator = iter(self._items(self.response))
        return self._iterator

    def __next__(self):
        return next(self.__iter__())

    def __getitem__(self, key):
        if isinstance(key, slice):
            start = key.start or 0
            stop = key.stop
            if key.step:
                raise NotImplementedError("Step slice is not implemented")
        else:
            start, stop = key, key + 1
        if start < 0:
            raise NotImplementedError("Negative indexing is not implemented")

        if not stop:
            return iter(
                self._items(
                    self.session.get(self.url, params={"b_start": start})
                )
            )

        size = stop - start
        self._response = self.session.get(
            self.url, params={"b_size": size, "b_start": start}
        )
        items = self._response.json()["items"]
        return items[0] if size == 1 else items

    def _items(
        self, container: Union[str, requests.Response]
    ) -> Generator[dict, None, None]:
        if isinstance(container, requests.Response):
            resp = container
        else:
            resp = self.session.get(container)
        resp.raise_for_status()
        result = _json(resp)
        for item in result.get("items", []):
            yield item

        more = result.get("batching", {}).get("next")
        if more:
            # tail recursion is not a thing in Python
            # this might overflow stack for huge results ?!
            yield from self._items(more)


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
