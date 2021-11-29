# SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica
#
# SPDX-License-Identifier: MPL-2.0

import re
from typing import Any
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit

import requests

from .utils import BatchingIterator, Registry, _json

DEFAULT_ROOT = "http://localhost:8080/Plone/"
ANONYMOUS_USER = "Anonymous"


class Session(requests.Session):
    """A `requests.Session` equiped as a plone.restapi client."""

    __api_root = ""

    def __init__(
        self,
        user: str = "",
        password: str = "",
        api_root: str = DEFAULT_ROOT,
    ) -> None:
        """`user` and `password` are used to 'Session.login'
        `api_root` is used as the base for relative urls passed to the CRUD methods.


        >>> request = api.Sssion(api_root='https://example.com').get('@actions').request
        >>> request.url
        'https://example.com/@actions'
        >>> request.headers['Accept']
        'application/json'
        """

        super().__init__()
        self.root = api_root
        self.user = ANONYMOUS_USER
        self.headers.update(accept="application/json")
        self.registry = Registry(self)
        self.hooks["response"] = [self._error_handler]
        if user and password:
            self.auth = (user, password)
            self.user = user

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__module__}.{self.__class__.__name__}: "
            f"{self.user}>"
        )

    def _error_handler(self, resp: requests.Response, *args, **kwargs):
        if resp.ok:
            return
        if resp.status_code == 500:
            error = resp.json()
            if error["type"] == "NotImplementedError":
                raise NotImplementedError(error["message"])

    @property
    def root(self) -> str:
        return self.__api_root

    @root.setter
    def root(self, url: str):
        url = urlsplit(urldefrag(url)[0]).geturl().strip("/") + "/"
        if self.__api_root != url:
            self.auth = None
            self.headers.pop("Authorization", None)
            self.user = ANONYMOUS_USER
            self.__api_root = url

    def request(
        self,
        method: str,
        url: Any,
        *args,
        **kwargs,
    ) -> requests.Response:
        url = urljoin(self.root, url.lstrip("/"))
        if not url.startswith(self.root):
            raise ValueError(
                f"Making requests to other hosts than {self.root} may leak credentials. "
                "Use a different requests.Session for those or change root"
            )
        return super().request(method, url, *args, **kwargs)

    def login(self, user: str, password: str) -> requests.Response:
        'Authenticate and add the "Bearer" token to the headers'
        resp = self.post(
            f"@login",
            json={"login": user, "password": password},
            headers={"Accept": "application/json"},
        )
        if not resp.ok:
            error = self._json(resp)["error"]
            if resp.status_code == 501:
                raise RuntimeError(error)
            if 399 < resp.status_code < 500:
                raise ValueError(error)
            resp.raise_for_status()

        self.user = user
        self.__token = self._json(resp)["token"]
        self.auth = (user, password)
        self.headers.update(authorization=f"Bearer {self.__token}")
        return resp

    def items(self, container: str) -> BatchingIterator:
        """Iterate over all items in `container`

        Implements an iterable over
        https://plonerestapi.readthedocs.io/en/latest/batching.html

        Implements a cheap __len__ too, so for use in progress bars etc.

        >>> len(session.items('/'))

        NB this is not an atomic operation; ie modifing the number of items in
           `container` during iteration may result in items not yielded.
        """
        return BatchingIterator(container, self)

    def _json(self, resp: requests.Response) -> dict:
        return _json(resp)
