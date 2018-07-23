from yarl import URL

from inpanzee.base import BaseKongObject
from inpanzee.resources import Service, Upstream, Consumer, Plugin, Certificate, SNI

"""
docker run -d --name kong \
    --link kong-database:kong-database \
    -e "KONG_DATABASE=postgres" \
    -e "KONG_PG_HOST=kong-database" \
    -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
    -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
    -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
    -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
    -e "KONG_ADMIN_LISTEN=0.0.0.0:8001" \
    -e "KONG_ADMIN_LISTEN_SSL=0.0.0.0:8444" \
    -p 8000:8000 \
    -p 8443:8443 \
    -p 8001:8001 \
    -p 8444:8444 \
    kong
"""

empty = object()


class Kong(BaseKongObject):
    fields = ()

    child_resource_classes = (Service, Upstream, Consumer,
                              Plugin, SNI, Certificate)

    def __init__(self, *, scheme: str, host: str, port: int):
        """
        Initialize kong instance

        :param scheme: scheme of kong url
        :type scheme: str
        :param host: host to the kong admin apis
        :type host: str
        :param port: port to kong admin apis
        :type port: int
        """
        super().__init__()

        self._scheme = scheme
        self._host = host
        self._port = port

        self.origin = URL.build(scheme=self._scheme, host=self._host, port=self._port)

    @property
    def detail_endpoint(self):
        return str(self.origin)

    def info(self):
        return self._get(self.detail_endpoint)

    def status(self):
        return self._get(str(self.origin.with_path('/status')))
