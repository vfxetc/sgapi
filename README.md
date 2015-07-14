# SGAPI: A low-level Shotgun API

This project is a lower-level Python implementation of the Shotgun API. The canonical API, `shotgun_api3`, [can be found on Shotgun's GitHub][shotgun_api3].

This project exists because we wanted to have a little more control over the details of the connection, threading, datetime handling, etc., but monkey-patching the `shotgun_api3` was deemed too unsafe. Ergo, we have a minimal API that does the few things that we need it to do at a low level.


[shotgun_api3]: https://github.com/shotgunsoftware/python-api
