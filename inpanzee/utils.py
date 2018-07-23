from yarl import URL


def unpack_url(value, unpack_into=None):
    if unpack_into is None:
        unpack_into = {}

    _url = URL(value)
    unpack_into['host'] = _url.host
    unpack_into['protocol'] = _url.scheme
    unpack_into['port'] = _url.port
    unpack_into['path'] = _url.path

    return unpack_into
