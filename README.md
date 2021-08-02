<!--
SPDX-FileCopyrightText: 2021 Centrum Wiskunde en Informatica

SPDX-License-Identifier: CC0-1.0
-->

# Affen: plone.restapi for Humans™

**Affen** is a [requests](https://docs.python-requests.org) Session equiped to
easily consume [plone.restapi](https://plonerestapi.readthedocs.io)

## Iterating without Affen

```python
>>> import requests
>>> response = requests.get('https://plonedemo.kitconcept.com/@search?sort_on=path',
... headers={'Accept': 'application/json'}, auth=('admin', 'admin'))
>>> for i, item in enumerate(response.json()['items']):
...     print(i, item['@id'])
...
0 https://plonedemo.kitconcept.com/de
1 https://plonedemo.kitconcept.com/de/Assets
2 https://plonedemo.kitconcept.com/de/demo
3 https://plonedemo.kitconcept.com/de/demo/a-image.jpg
4 https://plonedemo.kitconcept.com/de/demo/big_buck_bunny.mp4
5 https://plonedemo.kitconcept.com/de/demo/ein-link
6 https://plonedemo.kitconcept.com/de/demo/ein-ordner
7 https://plonedemo.kitconcept.com/de/demo/ein-ordner/eine-seite-in-einem-ordner
8 https://plonedemo.kitconcept.com/de/demo/ein-termin
9 https://plonedemo.kitconcept.com/de/demo/eine-nachricht
10 https://plonedemo.kitconcept.com/de/demo/eine-seite
11 https://plonedemo.kitconcept.com/de/demo/ploneconf-plone5.pdf
12 https://plonedemo.kitconcept.com/de/frontpage
13 https://plonedemo.kitconcept.com/en
14 https://plonedemo.kitconcept.com/en/assets
15 https://plonedemo.kitconcept.com/en/demo
16 https://plonedemo.kitconcept.com/en/demo/a-event
17 https://plonedemo.kitconcept.com/en/demo/a-file.pdf
18 https://plonedemo.kitconcept.com/en/demo/a-folder
19 https://plonedemo.kitconcept.com/en/demo/a-folder/a-page-inside-a-folder
20 https://plonedemo.kitconcept.com/en/demo/a-link
21 https://plonedemo.kitconcept.com/en/demo/a-news-item
22 https://plonedemo.kitconcept.com/en/demo/a-page
23 https://plonedemo.kitconcept.com/en/demo/a-photo.jpg
24 https://plonedemo.kitconcept.com/en/demo/a-video.mp4
>>>
```

And then follow the [batching](https://plonerestapi.readthedocs.io/en/latest/batching.html) for more.
(and remember to start `enumerate` at the right number)

```python
>>> response = requests.get(response.json()['batching']['next'],
... headers={'Accept': 'application/json'}, auth=2*('admin',))
>>> for i, item in enumerate(response.json()['items'], start=i + 1):
...     print(i, item['@id'])
...
25 https://plonedemo.kitconcept.com/en/frontpage
26 https://plonedemo.kitconcept.com/my-document
>>>
```

An Affen Session can take credentials and an api_root in the contructor, and
has an `items` function that iterates over anything in restapi that uses the
batching protocol; like Folders, Collectors and restapi endpoints like
`@search`:

```python
>>> from affen import Session
>>> plone = Session('admin', 'admin', 'https://plonedemo.kitconcept.com')
>>> for i, item in enumerate(plone.items('@search?sort_on=path')):
...     print(i, item['@id'])
...
0 https://plonedemo.kitconcept.com/de
1 https://plonedemo.kitconcept.com/de/Assets
2 https://plonedemo.kitconcept.com/de/demo
3 https://plonedemo.kitconcept.com/de/demo/a-image.jpg
4 https://plonedemo.kitconcept.com/de/demo/big_buck_bunny.mp4
5 https://plonedemo.kitconcept.com/de/demo/ein-link
6 https://plonedemo.kitconcept.com/de/demo/ein-ordner
7 https://plonedemo.kitconcept.com/de/demo/ein-ordner/eine-seite-in-einem-ordner
8 https://plonedemo.kitconcept.com/de/demo/ein-termin
9 https://plonedemo.kitconcept.com/de/demo/eine-nachricht
10 https://plonedemo.kitconcept.com/de/demo/eine-seite
11 https://plonedemo.kitconcept.com/de/demo/ploneconf-plone5.pdf
12 https://plonedemo.kitconcept.com/de/frontpage
13 https://plonedemo.kitconcept.com/en
14 https://plonedemo.kitconcept.com/en/assets
15 https://plonedemo.kitconcept.com/en/demo
16 https://plonedemo.kitconcept.com/en/demo/a-event
17 https://plonedemo.kitconcept.com/en/demo/a-file.pdf
18 https://plonedemo.kitconcept.com/en/demo/a-folder
19 https://plonedemo.kitconcept.com/en/demo/a-folder/a-page-inside-a-folder
20 https://plonedemo.kitconcept.com/en/demo/a-link
21 https://plonedemo.kitconcept.com/en/demo/a-news-item
22 https://plonedemo.kitconcept.com/en/demo/a-page
23 https://plonedemo.kitconcept.com/en/demo/a-photo.jpg
24 https://plonedemo.kitconcept.com/en/demo/a-video.mp4
25 https://plonedemo.kitconcept.com/en/frontpage
26 https://plonedemo.kitconcept.com/my-document
>>>
```

## Wrangling the Registry

And if you have the permissions, you can read and write to the registry as if it were a dictionary:

```python
>>> plone = Session('admin', 'admin', 'http://127.0.0.1:8080/Plone')
>>> plone.registry['plone.allowed_sizes']
['large 768:768',
 'preview 400:400',
 'mini 200:200',
 'thumb 128:128',
 'tile 64:64',
 'icon 32:32',
 'listing 16:16']
>>> plone.registry['plone.allowed_sizes'] = ['supersize_me 3840:2160']
>>> plone.registry['plone.allowed_sizes']
['supersize_me 3840:2160']
>>>
```

## But my requests.Session does almost the same!

```python
>>> vanilla = requests.Session()
>>> vanilla.auth = ('admin', 'admin')
>>> vanilla.headers['accept'] = 'application/json'
>>> ROOT = 'http://127.0.0.1:8080/Plone'
>>> # these two lines make it almost as short as Affen...
>>> [t['title'] for t in vanilla.get(f'{ROOT}/@types').json()]
['Collection', 'Event', 'File', 'Folder', 'Image', 'Link', 'News Item', 'Page']
>>> # see? f-strings were such a great idea!
>>> # Affen is hardly shorter
>>> [t['title'] for t in plone.get('@types').json()]
['Collection', 'Event', 'File', 'Folder', 'Image', 'Link', 'News Item', 'Page']
>>>
```

Sure, until you accidentally reuse the session for requests to a different
host. It's so conveniently close, and seems to behave like `requests.get`. So
your mypy powered IDE didn't catch it. In fact, it provided handy
autocompletion, so it looked like the Right Thing™.

```python
>>> vanilla.get('https://httpbin.org/headers').json()['headers']['Authorization']
'Basic YWRtaW46YWRtaW4='
>>>
```

OOPS, did we just send our 'Authorization' header to the nice people of httpbin.org?
An Affen Session will throw a fit when you try to do that:

```python
>>> plone.get('https://httpbin.org/headers').json()
Traceback (most recent call last):
    ...
ValueError: Making requests to other hosts than http://127.0.0.1:8080/Plone/ may leak credentials. Use a different requests.Session for those or change root

>>> # and even when whe change the api root
>>> plone.root = 'https://httpbin.org'
>>> plone.get('headers').json()['headers']['Authorization']
Traceback (most recent call last):
    ...
KeyError: 'Authorization'
>>> # it won't send the secrets
```
