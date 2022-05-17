"""Extending vSphere SDK."""
import logging
from typing import Dict

import requests
from nautobot.core.settings_funcs import is_truthy

from nautobot_ssot_vsphere.diffsync import defaults

LOGGER = logging.getLogger(__name__)
# %load_ext autoreload
# %autoreload 2
# from nautobot_ssot_vsphere.utilities import VsphereClient
# test = VsphereClient()
# test.get_vm_interfaces("vm-1012")


class VsphereClient:
    """Class for interacting with VMWare vSphere."""

    def __init__(
        self,
        vsphere_uri: str = defaults.VSPHERE_URI,
        username: str = defaults.VSPHERE_USERNAME,
        password: str = defaults.VSPHERE_PASSWORD,
        verify_ssl: bool = is_truthy(defaults.VSPHERE_VERIFY_SSL),
    ):  # pylint: disable=W0235
        """Init."""
        if not all([vsphere_uri, username, password]):
            raise ValueError(
                "Missing required parameters for vSphere API access - check environment and plugin configuration"
            )
        self.uri = vsphere_uri.strip().strip("/")
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings(  # pylint: disable=no-member
                requests.packages.urllib3.exceptions.InsecureRequestWarning  # pylint: disable=no-member
            )
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.rest_client = self.session.post(f"{self.uri}/rest/com/vmware/cis/session", auth=(username, password))
        LOGGER.debug("vSphere Client authenticated and session established.")

    def _request(self, method: str, path: str, **kwargs):
        """Return a response object after making a request to by other methods.

        Args:
            method (str): Request method to call in self.session.
            path (str): uri path to call.

        Returns:
            :class:`~requests.Response`: Response from the API.
        """
        url = requests.compat.urljoin(self.uri, path)
        return self.session.request(method, url, **kwargs)

    def get_vms(self) -> Dict:
        """Get VMs."""
        return self._request("GET", f"{self.uri}/rest/vcenter/vm")

    def get_vms_from_cluster(self, cluster: str) -> Dict:
        """Get VMs."""
        return self._request("GET", f"{self.uri}/rest/vcenter/vm?filter.clusters={cluster}")

    def get_vms_from_dc(self, datacenter: str) -> Dict:
        """Get VMs."""
        return self._request("GET", f"{self.uri}/rest/vcenter/vm?filter.datacenters={datacenter}")

    def get_datacenters(self) -> Dict:
        """Get datacenters."""
        return self._request("GET", f"{self.uri}/rest/vcenter/datacenter")

    def get_datacenter_details(self, datacenter: str) -> Dict:
        """Get datacenters."""
        return self._request("GET", f"{self.uri}/rest/vcenter/datacenter/{datacenter}")

    def get_clusters(self) -> Dict:
        """Get Clusters."""
        return self._request("GET", f"{self.uri}/rest/vcenter/cluster")

    def get_clusters_from_dc(self, datacenter: str) -> Dict:
        """Get Clusters."""
        return self._request("GET", f"{self.uri}/rest/vcenter/cluster?filter.datacenters={datacenter}")

    def get_cluster_details(self, cluster_name: str) -> Dict:
        """Get Clusters."""
        return self._request("GET", f"{self.uri}/rest/vcenter/cluster/{cluster_name}")

    def get_vm_details(self, vm_id: str) -> Dict:
        """Get all VMs details."""
        return self._request("GET", f"{self.uri}/rest/vcenter/vm/{vm_id}")

    def get_host_from_cluster(self, cluster: str) -> Dict:
        """Get hosts from cluster."""
        return self._request("GET", f"{self.uri}/rest/vcenter/host/?filter.clusters={cluster}")

    def get_host_details(self, host: str) -> Dict:
        """Get host details."""
        return self._request("GET", f"{self.uri}/rest/vcenter/host/?filter.hosts={host}")

    def get_vm_interfaces(self, vm_id: str) -> Dict:
        """Get all VM interfaces."""
        return self._request("GET", f"{self.uri}/rest/vcenter/vm/{vm_id}/guest/networking/interfaces")
