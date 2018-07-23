import logging
import requests

logger = logging.getLogger(__name__)


class RequestsBase:
    session = requests.Session()

    def _get(self, url):
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()

    def _post(self, url, data):
        r = self.session.post(url, json=data)
        r.raise_for_status()
        return r.json()

    def _patch(self, url, data):
        r = self.session.patch(url, json=data)
        r.raise_for_status()
        return r.json()

    def _delete(self, url):
        r = self.session.delete(url)
        r.raise_for_status()
        return r

    def _list(self, resource_list_url):
        next_url = resource_list_url
        while next_url:
            response_body = self._get(next_url)
            for resource in response_body.get('data', []):
                yield resource
            next_url = response_body.get('next', None)

def _list_helper(resource_class):
    def _wrapped(self):
        resource_list = self._list(f"{self.detail_endpoint}/{resource_class.resource_endpoint()}")
        for r in resource_list:
            r = resource_class(self, **r)
            self.child_resource[resource_class.resource_endpoint()].add(r)
            yield r
    return _wrapped


def _add_helper(resource_class):
    def _wrapped(self, **kwargs):
        new_resource = resource_class(self, **kwargs)
        self.child_resource[resource_class.resource_endpoint()].add(new_resource)
        return new_resource
    return _wrapped


def _get_helper(resource_class):
    def _wrapped(self, id):
        new_resource = resource_class(self, id=id)
        new_resource.pull()
        self.child_resource[resource_class.resource_endpoint()].add(new_resource)
        return new_resource
    return _wrapped

class KongMetaClass(type):

    def __new__(mcs, name, bases, namespace, **kwargs):
        # set children methods for class
        for child in namespace.get('child_resource_classes', []):
            namespace.update({f"list_{child.resource_endpoint()}": _list_helper(child)})
            namespace.update({f"add_{child.resource_endpoint()[:-1]}": _add_helper(child)})
            namespace.update({f"get_{child.resource_endpoint()[:-1]}": _get_helper(child)})
        return super().__new__(mcs, name, bases, namespace)

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(**kwargs)

        # set parent
        try:
            parent = args[0]
            instance.parent_resource = parent
            instance.origin = parent.origin
        except IndexError:
            instance.parent_resource = None

        return instance


class BaseKongObject(RequestsBase, metaclass=KongMetaClass):
    child_resource_classes = ()

    def __init__(self, *args, **kwargs):
        super().__init__()
        for attr in self.fields + self.extra_fields:
            setattr(self, attr, kwargs.pop(attr, None))

        self.child_resource = {c.resource_endpoint(): set() for c in self.child_resource_classes}

    @classmethod
    def resource_endpoint(cls):
        return f"{cls.__name__.lower()}s"

    @property
    def list_endpoint(self):
        if self.parent_resource is not None:
            return f"{self.parent_resource.detail_endpoint}/{self.resource_endpoint()}"
        else:
            return f"{self.resource_endpoint()}"

    @property
    def detail_endpoint(self):
        if self.id is not None:
            return f"{self.list_endpoint}/{self.id}"
        else:
            raise AssertionError(f"'id' is not set this {self.__class__.__name__.lower()} resource. "
                                 f"Must save before attempting this.")

    def save(self, force_create=False, children=False):
        data = {attr: getattr(self, attr) for attr in self.fields}
        try:
            if not self.id or force_create:
                r = self._post(self.list_endpoint, data)
            else:
                r = self._patch(self.list_endpoint, data)
        except requests.HTTPError as e:
            error_response = e.response.json()
            raise AssertionError(error_response.get('fields') or error_response)
        else:
            for k, v in r.items():
                if k in self.fields:
                    setattr(self, k, v)

    def pull(self):
        if self.id:
            r = self._get(self.detail_endpoint)
            for k, v in r.items():
                if k in self.fields:
                    setattr(self, k, v)
        else:
            raise AssertionError("id is not set.")

    def delete(self):
        try:
            self._delete(self.detail_endpoint)
        except requests.HTTPError as e:
            error_response = e.response.json()
            raise AssertionError(error_response)
        else:
            self.id = None

    def __repr__(self):
        """
        Representation of this object. Should be able to evaluate to produce the same object.

        :return: str
        """
        params = []

        for attr in self.fields + self.extra_fields:
            value = getattr(self, attr, None)
            if isinstance(value, str):
                params.append(f'{attr}="{value}"')
            else:
                params.append(f'{attr}={value}')
        params = ", ".join(params)
        return f"{self.__module__}.{self.__class__.__name__}({params})"

    def __eq__(self, other):
        for attr in self.fields:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __hash__(self):
        hash_values = [f"{self.__class__.__name__.lower()}"]

        if getattr(self, 'id', None):
            hash_values.append(getattr(self, 'id'))
        else:
            for attr in sorted(self.fields):
                hash_values.append(attr)
                hash_values.append(str(getattr(self, attr)) or "null")
        return hash(":".join(hash_values))

