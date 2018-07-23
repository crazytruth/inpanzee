from yarl import URL
from inpanzee.base import BaseKongObject
from inpanzee.utils import unpack_url


class Route(BaseKongObject):
    """
    https://docs.konghq.com/0.14.x/admin-api/#route-object
    """
    fields = ('id', 'protocols', 'methods', 'hosts', 'paths', 'strip_path', 'preserve_host',)

    def get_service(self):
        url = self.origin.with_path(f"{self.resource_endpoint()}/{self.id}/service")
        self.parent_resource = Service(**self._get(str(url)))
        return self.parent_resource


class Service(BaseKongObject):
    fields = ('id', 'host', 'port', 'protocol', 'path', 'retries', 'connect_timeout',
                 'write_timeout', 'read_timeout')

    child_resource_classes = (Route,)

    def __init__(self, **kwargs):
        if 'url' in kwargs and kwargs.get('url', None):
            unpack_url(kwargs.pop('url'), kwargs)

        super(Service, self).__init__(**kwargs)

    @property
    def url(self):
        return str(URL.build(scheme=self['protocol'], host=self['host'], port=self['port'], path=self['path']))

    @url.setter
    def url(self, value):
        unpacked = unpack_url(value)
        for k, v in unpacked.items():
            setattr(self, k, v)


class Target(BaseKongObject):
    non_fields = ('health', )
    fields = ('id', 'target', 'weight',)

    def set_healthy(self):
        self.post(f"{self.detail_endpoint}/healthy")

    def set_unhealthy(self):
        self.post(f"{self.detail_endpoint}/unhealthy")


class Upstream(BaseKongObject):
    fields = ('id', 'name', 'hash_on', 'hash_fallback', 'healthchecks', 'slots')
    child_resource_classes = (Target,)

    def health(self):
        resource_list = self._list(f"{self.detail_endpoint}/health")
        for r in resource_list:
            r = Target(self, **r)
            self.child_resource[Target.resource_endpoint()].add(r)
            yield r

    def list_all_targets(self):
        resource_list = self._list(f"{self.detail_endpoint}/targets/all")
        for r in resource_list:
            r = Target(self, **r)
            self.child_resource[Target.resource_endpoint()].add(r)
            yield r


class Consumer(BaseKongObject):
    fields = ('id', 'username', 'custom_id')


class Plugin(BaseKongObject):
    fields = ('id', 'name', 'config', 'consumer_id', 'service_id', 'route_id', 'enabled')


class SNI(BaseKongObject):
    fields = ('id', 'name')


class Certificate(BaseKongObject):
    fields = ('id', 'cert', 'key')




