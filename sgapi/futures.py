import threading


class Future(threading.Thread):

    """Really cheap version of concurrent.futures."""

    @classmethod
    def submit(cls, func, *args, **kwargs):
        future = cls(func, args, kwargs)
        future._thread.start()
        return future

    def __init__(self, func, args=None, kwargs=None):
        self._func = func
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._thread = threading.Thread(target=self._eval)

    def _eval(self):
        try:
            self._result = self._func(*self._args, **self._kwargs)
            self._exc = None
        except Exception as e:
            self._result = None
            self._exc = e

    def result(self):
        self._thread.join()
        if self._exc:
            raise self._exc
        else:
            return self._result

