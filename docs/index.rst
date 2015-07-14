SGAPI: A lower-level Shotgun API
================================


This project is a lower-level Python implementation of the Shotgun API.
The canonical Python API (``shotgun_api3``) can be found on `Shotgun's
GitHub page <https://github.com/shotgunsoftware/python-api>`_

This project exists because we wanted to have a little more control over
the details of the connection, threading, time handling, etc.,
but monkey-patching the ``shotgun_api3`` was deemed too unsafe.
Ergo, we have a minimal API that does the few things that we need it
to do at a low level.

Extra things that we implement include:

- forgiving filters which understand any of the 3 filter dialects;

- asynchronous paging during find via `threads=<number of threads>`.




Installation
------------

From `GitHub <https://github.com/westernx/sgapi>`_::

    pip install -e git+git@github.com:westernx/sgapi#egg=sgapi



Basic Usage
-----------

::

    >>> from sgapi import Shotgun

    >>> # Basic instantiation is the same:
    >>> sg = Shotgun(server_url, script_name, api_key)

    >>> # Info is the same:
    >>> sg.info()
    {
        's3_uploads_enabled': True, 
        'totango_site_id': '123',
        'version': [6, 0, 3],
        'totango_site_name': 'com_shotgunstudio_example'
    }

    >>> # Finding can be the same:
    >>> sg.find_one('Task', [('id', 'is', 1234)])
    {'type': 'Task', 'id': 1234}

    >>> # You can also iterate over entities while requests run in a thread:
    >>> for e in sg.find('Task', [...], threads=3, per_page=100):
    ...     process_entity(e)

    >>> # Or you can manually construct requests:
    >>> sg.call('find', {...})





Python API
----------

``sgapi``
^^^^^^^^^

.. automodule:: sgapi

.. autoclass:: sgapi.Shotgun
    :members:

``sgapi.filters``
^^^^^^^^^^^^^^^^^
.. automodule:: sgapi.filters
    :members:


