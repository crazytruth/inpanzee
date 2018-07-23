"""Tests for `inpanzee` package."""

import pytest
import inpanzee

from inpanzee.client import Kong
from inpanzee.resources import Service


@pytest.fixture
def kong_client():
    return Kong(scheme='http', host='localhost', port=8001)


def test_kong_client():
    """Sample pytest test function with the pytest fixture as an argument."""
    k = Kong(scheme='http', host='localhost', port=8001)
    k.info()


def test_kong_child_list_resources(kong_client):
    assert list(kong_client.list_services()) == []

def test_kong_child_add_resources(kong_client):
    assert isinstance(kong_client.add_service(), Service)

def test_kong_add_route_to_service(kong_client):
    s = kong_client.add_service()
    r = s.add_route()

def test_resource_representation(kong_client):
    s = kong_client.add_service()
    s1 = eval(repr(s))
    assert s == s1

def test_kong_get_resource(kong_client):
    s = kong_client.get_service("cff4d89e-082d-4117-862b-8eb264415688")

    assert isinstance(s, Service)


def test_save_resource(kong_client):
    s = kong_client.add_service()
    s.save()

