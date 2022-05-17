"""Test vSphere client."""
# pylint: disable=protected-access
import os
from unittest.mock import patch

import requests
import responses
from nautobot.utilities.testing import TestCase
from requests import Session

from nautobot_ssot_vsphere.tests.fixtures import json_fixture, real_path
from nautobot_ssot_vsphere.utilities import VsphereClient

FIXTURES = os.environ.get("FIXTURE_DIR", real_path)


class TestVsphere(TestCase):
    """Test Base vSphere Client and Calls."""

    @patch.object(Session, "post")
    def setUp(self, mock_session):  # pylint:disable=arguments-differ
        """Setup."""
        mock_session.return_value = "some_response"
        self.vsphere_uri = "https://vcenter.local"
        self.username = "administrator@vcenter.local"
        self.password = "P@ssW0rD"  # nosec
        self.verify_ssl = False
        self.client = VsphereClient(self.vsphere_uri, self.username, self.password, self.verify_ssl)

    def test_init_success(self):  # pylint: disable=R0201
        """Assert proper initialization of client."""
        self.assertEqual(self.client.uri, "https://vcenter.local")
        self.assertTrue(isinstance(self.client.session, requests.Session))
        self.assertFalse(self.client.session.verify)
        self.assertEqual(
            self.client.session.headers,
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    def test_init_missing_uri(self):
        """Assert proper initialization of client, raise ValErr from creds/uri."""
        self.assertRaises(ValueError, VsphereClient, "")

    def test_init_uri_not_str(self):
        """Assert proper initialization of client, failure from uri not a str."""
        self.assertRaises(AttributeError, VsphereClient, 1, "user", "pass", False)

    def test_ssl_not_verify(self):
        """Test verify SSL False."""
        self.assertFalse(self.client.session.verify)

    @responses.activate
    def test_get_vms(self):
        """Test Get VMs API Call."""
        endpoint = f"{self.vsphere_uri}/rest/vcenter/vm"
        json_response = json_fixture(f"{FIXTURES}/get_vms.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_vms().json()["value"][0]["memory_size_MiB"], 32768)

    @responses.activate
    def test_get_vms_from_cluster(self):
        """Test Get VMs from cluster API Call."""
        cluster = "domain-c1001"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/vm?filter.clusters={cluster}"
        json_response = json_fixture(f"{FIXTURES}/get_vms_from_cluster.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_vms_from_cluster(cluster).json()["value"][1]["name"], "Nautobot")

    @responses.activate
    def test_get_vms_from_dc(self):
        """Test Get VMs from DC API Call."""
        datacenter = "datacenter-62"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/vm?filter.datacenters={datacenter}"
        json_response = json_fixture(f"{FIXTURES}/get_vms_from_dc.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_vms_from_dc(datacenter).json()["value"][2]["power_state"], "POWERED_ON")

    @responses.activate
    def test_get_datacenters(self):
        """Test Get DC's API Call."""
        endpoint = f"{self.vsphere_uri}/rest/vcenter/datacenter"
        json_response = json_fixture(f"{FIXTURES}/get_datacenters.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_datacenters().json()["value"][0]["name"], "CrunchyDatacenter")

    @responses.activate
    def test_get_clusters(self):
        """Test Get Clusters API Call."""
        endpoint = f"{self.vsphere_uri}/rest/vcenter/cluster"
        json_response = json_fixture(f"{FIXTURES}/get_clusters.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_clusters().json()["value"][0]["name"], "HeshLawCluster")

    @responses.activate
    def test_get_cluster_details(self):
        """Test Get Clusters Detail API Call."""
        cluster_name = "domain-c1001"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/cluster/{cluster_name}"
        json_response = json_fixture(f"{FIXTURES}/get_cluster_details.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(
            self.client.get_cluster_details(cluster_name).json()["value"]["resource_pool"], "resgroup-1002"
        )

    @responses.activate
    def test_get_dc_details(self):
        """Test Get DC Details API Call."""
        datacenter = "datacenter-62"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/datacenter/{datacenter}"
        json_response = json_fixture(f"{FIXTURES}/get_dc_details.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(
            self.client.get_datacenter_details(datacenter).json()["value"]["datastore_folder"], "group-s65"
        )

    @responses.activate
    def test_get_vm_interfaces(self):
        """Test Get VM Interface Details API Call."""
        vm_id = "vm-1012"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/vm/{vm_id}/guest/networking/interfaces"
        json_response = json_fixture(f"{FIXTURES}/get_vm_interfaces.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_vm_interfaces(vm_id).json()["value"][0]["mac_address"], "00:0c:29:48:fa:fe")

    @responses.activate
    def test_get_vm_details(self):
        """Test Get VM Details API Call."""
        vm_id = "vm-1012"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/vm/{vm_id}"
        json_response = json_fixture(f"{FIXTURES}/get_vm_details.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_vm_details(vm_id).json()["value"]["cpu"]["count"], 4)

    @responses.activate
    def test_get_host_from_clusters(self):
        """Test Get host from clusters API Call."""
        cluster = "domain-c1001"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/host/?filter.clusters={cluster}"
        json_response = json_fixture(f"{FIXTURES}/get_host_from_cluster.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_host_from_cluster(cluster).json()["value"][0]["host"], "host-1007")

    @responses.activate
    def test_get_host_details(self):
        """Test Get host details API Call."""
        host = "host-1007"
        endpoint = f"{self.vsphere_uri}/rest/vcenter/host/?filter.hosts={host}"
        json_response = json_fixture(f"{FIXTURES}/get_host_details.json")

        responses.add(
            responses.GET,
            endpoint,
            json=json_response,
            status=200,
        )
        self.assertEqual(self.client.get_host_details(host).json()["value"][0]["name"], "crunchy-esxi.heshlaw.local")
