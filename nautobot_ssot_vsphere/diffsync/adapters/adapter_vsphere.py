"""Adapter for VM Ware vSphere objects."""
#  pylint: disable=too-many-arguments
# Load method is packed with conditionals  #  pylint: disable=too-many-branches
import ipaddress
from typing import List

from nautobot_ssot_vsphere.diffsync import defaults
from nautobot_ssot_vsphere.diffsync.adapters.shared import DiffSyncModelAdapters
from nautobot_ssot_vsphere.utilities.vsphere_client import VsphereClient


def create_ipaddr(address: str):
    """Create an IPV4 or IPV4 object."""
    try:
        ip_address = ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError:
        ip_address = ipaddress.IPv6Address(address)
    return ip_address


def get_disk_total(disks: List):
    """Calculcate total disk capacity."""
    total = 0
    for disk in disks:
        total += disk["value"]["capacity"]
    return int(total / 1024.0**3)


class VsphereDiffSync(DiffSyncModelAdapters):
    """Nautobot adapter for DiffSync."""

    def __init__(self, job, sync, client: VsphereClient, cluster_filter, *args, **kwargs):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.client = client
        self.cluster_filter = cluster_filter if cluster_filter else None

    def load_cluster_groups(self):
        """Load Cluster Groups (DataCenters)."""
        clustergroups = self.client.get_datacenters().json()["value"]
        for clustergroup in clustergroups:
            self.get_or_instantiate(self.diffsync_clustergroup, {"name": clustergroup["name"]})
        return clustergroups

    def load_virtualmachines(self, cluster, diffsync_cluster):
        """Load Virtual Machines."""
        virtual_machines = self.client.get_vms_from_cluster(cluster["cluster"]).json()["value"]
        for virtual_machine in virtual_machines:
            virtual_machine_details = self.client.get_vm_details(virtual_machine["vm"]).json()["value"]
            diffsync_virtualmachine, _ = self.get_or_instantiate(
                self.diffsync_virtual_machine,
                {"name": virtual_machine["name"]},
                {
                    "vcpus": virtual_machine["cpu_count"],
                    "memory": virtual_machine["memory_size_MiB"],
                    "disk": get_disk_total(virtual_machine_details["disks"]),
                    "status": defaults.DEFAULT_VM_STATUS_MAP[virtual_machine_details["power_state"]],
                    "cluster": cluster["name"],
                },
            )
            diffsync_cluster.add_child(diffsync_virtualmachine)
            self.load_vm_interfaces(
                vsphere_virtual_machine=virtual_machine_details,
                vm_id=virtual_machine["vm"],
                diffsync_virtualmachine=diffsync_virtualmachine,
            )

    def load_ip_addresses(self, vsphere_vm_interfaces, mac_address, diffsync_vminterface):
        """Load VM IP Addresses into Interfaces.

        Compare the current NIC MAC to grab any IP's associated.
        """
        ipv4_addresses = []
        ipv6_addresses = []
        for interface in vsphere_vm_interfaces.json()["value"]:
            if not isinstance(interface, dict):
                continue
            current_mac = interface["mac_address"].lower() if interface.get("mac_address") else None
            if not current_mac == mac_address:
                continue
            # Capture all IP Addresses
            for ip_address in interface["ip"]["ip_addresses"]:
                # Convert to IP Object if IPV4 or IPV6 and add to list by version
                addr = create_ipaddr(ip_address["ip_address"])
                if addr.version == 4:
                    ipv4_addresses.append(addr)
                else:
                    ipv6_addresses.append(addr)

                diffsync_ipaddress, _ = self.get_or_instantiate(
                    self.diffsync_ipaddress,
                    {"ip_address": ip_address["ip_address"], "prefix_length": ip_address["prefix_length"]},
                    {
                        "state": defaults.DEFAULT_IP_STATUS_MAP[ip_address["state"]],
                        "mac_address": current_mac,
                        "nic": interface.get("nic"),
                        "vm_interface_name": diffsync_vminterface.name,
                        "vm_name": diffsync_vminterface.virtual_machine,
                    },
                )
                diffsync_vminterface.add_child(diffsync_ipaddress)

        return ipv4_addresses, ipv6_addresses

    def load_primary_ip(
        self, ipv4_addresses: List, ipv6_addresses: List, diffsync_virtualmachine
    ):  # pylint:disable=R0201
        """Determine Primary IP of Virtual Machine."""
        # Sort and choose a primary_ip by default config setting
        ipv4_addresses.sort()
        ipv6_addresses.sort()

        # Sort and choose either Lowest or Last item in the list
        if defaults.PRIMARY_IP_SORT_BY == "Lowest":
            if ipv4_addresses:
                diffsync_virtualmachine.primary_ip4 = str(ipv4_addresses[0])
            if ipv6_addresses:
                diffsync_virtualmachine.primary_ip6 = str(ipv6_addresses[0])
        else:
            if ipv4_addresses:
                diffsync_virtualmachine.primary_ip4 = str(ipv4_addresses[-1])

            if ipv6_addresses:
                diffsync_virtualmachine.primary_ip6 = str(ipv6_addresses[-1])

        # self.job.log_debug(
        #     message=f"Assigning {diffsync_virtualmachine.primary_ip6} as primary to {diffsync_virtualmachine.name}"
        # )

    def load_vm_interfaces(self, vsphere_virtual_machine, vm_id, diffsync_virtualmachine):
        """Load VM Interfaces."""
        nics = vsphere_virtual_machine["nics"]
        # Get all IPAdders from ALL Nics on Virtual Machine
        addrs4 = []
        addrs6 = []

        for nic in nics:
            nic_mac = nic["value"]["mac_address"].lower()
            diffsync_vminterface, _ = self.get_or_instantiate(
                self.diffsync_vminterface,
                {"name": nic["value"]["label"], "virtual_machine": diffsync_virtualmachine.name},
                {
                    "enabled": defaults.VSPHERE_VM_INTERFACE_MAP[nic["value"]["state"]],
                    "mac_address": nic_mac,
                },
            )
            diffsync_virtualmachine.add_child(diffsync_vminterface)
            # Get detail interfaces w/ ip's from VM - Only if VM is Enabled
            if vsphere_virtual_machine["power_state"] == "POWERED_ON":
                vm_interfaces = self.client.get_vm_interfaces(vm_id=vm_id)
                # Load any IP addresses associated to this NIC/MAC
                ipv4_addresses, ipv6_addresses = self.load_ip_addresses(
                    vm_interfaces,
                    nic_mac,
                    diffsync_vminterface,
                )
                [addrs4.append(str(addr)) for addr in ipv4_addresses]  # pylint: disable=expression-not-assigned
                [addrs6.append(str(addr)) for addr in ipv6_addresses]  # pylint: disable=expression-not-assigned

        # Sort through all IP's on
        self.load_primary_ip(addrs4, addrs6, diffsync_virtualmachine)

    def load_data(self):
        """Load all clusters from vSphere."""
        # load all cluster groups (datacenters)
        clustergroups = self.load_cluster_groups()
        for clustergroup in clustergroups:
            clusters = self.client.get_clusters_from_dc(clustergroup["datacenter"]).json()["value"]
            self.job.log_debug(message=f"Found vSphere Clusters {clusters}")
            for cluster in clusters:
                diffsync_cluster, _ = self.get_or_instantiate(
                    self.diffsync_cluster,
                    {"name": cluster["name"]},
                    {
                        "cluster_type": defaults.DEFAULT_VSPHERE_TYPE,
                        "group": clustergroup["name"],
                    },
                )
                cluster_group_parent = self.get(self.diffsync_clustergroup, clustergroup["name"])
                if self.cluster_filter and cluster["name"] == self.cluster_filter.name:
                    self.job.log_debug(message=f"Found Cluster from filter {cluster}")
                    self.add(diffsync_cluster)
                    if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
                        cluster_group_parent.add_child(diffsync_cluster)
                    # Load virtual machines that belong to a cluster
                    self.load_virtualmachines(cluster, diffsync_cluster)
                    break
                if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
                    cluster_group_parent.add_child(diffsync_cluster)
                # Load virtual machines that belong to a cluster
                self.load_virtualmachines(cluster, diffsync_cluster)

    def load_standalone_vms(self):
        """Load all VM's from vSphere."""
        virtual_machines = self.client.get_vms().json()["value"]
        for virtual_machine in virtual_machines:
            virtual_machine_details = self.client.get_vm_details(virtual_machine["vm"]).json()["value"]
            diffsync_virtualmachine, _ = self.get_or_instantiate(
                self.diffsync_virtual_machine,
                {"name": virtual_machine["name"]},
                {
                    "vcpus": virtual_machine["cpu_count"],
                    "memory": virtual_machine["memory_size_MiB"],
                    "disk": get_disk_total(virtual_machine_details["disks"]),
                    "status": defaults.DEFAULT_VM_STATUS_MAP[virtual_machine_details["power_state"]],
                    "cluster": defaults.DEFAULT_CLUSTER_NAME,
                },
            )
            self.load_vm_interfaces(
                vsphere_virtual_machine=virtual_machine_details,
                vm_id=virtual_machine["vm"],
                diffsync_virtualmachine=diffsync_virtualmachine,
            )

    def load(self):
        """Load data from vSphere."""
        if defaults.DEFAULT_USE_CLUSTERS:
            self.load_data()
        else:
            self.job.log_warning(message="Not syncing Clusters or Cluster Groups per user settings")
            self.job.log_warning(message="`DEFAULT_USE_CLUSTERS` set to `False`")
            self.load_standalone_vms()
