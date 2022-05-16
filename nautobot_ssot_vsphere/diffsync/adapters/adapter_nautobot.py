"""Adapter for Nautobot objects."""
#  pylint: disable=too-many-arguments
# Load method is packed with conditionals  #  pylint: disable=too-many-branches
from collections import defaultdict
from typing import Any, ClassVar

from diffsync import DiffSync
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError, Q
from nautobot.extras.models import Tag
from nautobot.ipam.models import IPAddress
from nautobot.virtualization.models import (
    Cluster,
    ClusterGroup,
    VirtualMachine,
    VMInterface,
)

from nautobot_ssot_vsphere.diffsync import defaults
from nautobot_ssot_vsphere.diffsync.adapters.shared import DiffSyncModelAdapters
from nautobot_ssot_vsphere.utilities.nautobot_utils import create_ssot_tag


class NautobotDiffSync(DiffSyncModelAdapters):
    """Nautobot adapter for DiffSync."""

    objects_to_delete = defaultdict(list)

    _cluster: ClassVar[Any] = Cluster
    _clustergroup: ClassVar[Any] = ClusterGroup
    _virtualmachine: ClassVar[Any] = VirtualMachine
    _vminterface: ClassVar[Any] = VMInterface
    _ipaddress: ClassVar[Any] = IPAddress

    def __init__(
        self,
        job,
        sync,
        sync_vsphere_tagged_only: bool,
        cluster_filter: Cluster,
        *args,
        **kwargs,
    ):
        """Initialize the NautobotDiffSync."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync
        self.sync_vsphere_tagged_only = sync_vsphere_tagged_only
        self.cluster_filter = cluster_filter

    @transaction.atomic
    def sync_complete(self, source: DiffSync, *args, **kwargs):
        """Clean up function for DiffSync sync.

        Once the sync is complete, this function runs deleting any objects
        from Nautobot that need to be deleted in a specific order.

        Args:
            source (DiffSync): DiffSync
        """
        for grouping in ("_ipaddress", "_vminterface", "_virtualmachine", "_cluster", "_clustergroup"):
            for nautobot_object in self.objects_to_delete[grouping]:
                try:
                    self.job.log_info(obj=nautobot_object, message=f"Deleting object {nautobot_object}")
                    nautobot_object.delete()
                except ProtectedError:
                    self.job.log_failure(obj=nautobot_object, message="Deletion failed protected object")
                except IntegrityError:
                    self.job.log_failure(
                        obj=nautobot_object, message=f"Deletion failed due to IntegrityError with {nautobot_object}"
                    )
            self.objects_to_delete[grouping] = []
        return super().sync_complete(source, *args, **kwargs)

    def get_initial_cluster(self, ssot_tag: Tag):
        """Identify the site objects based on user defined job inputs.

        Args:
            ssot_tag (Tag): Tag used for filtering
        """
        # Simple check / validate Tag is present.
        if self.sync_vsphere_tagged_only:
            cluster_objects = Cluster.objects.filter(tags__slug=ssot_tag.slug)
            if self.cluster_filter:
                cluster_objects = Cluster.objects.filter(Q(name=self.cluster_filter.name) & Q(tags__slug=ssot_tag.slug))
                if not cluster_objects:
                    self.job.log_warning(
                        message=f"{self.cluster_filter.name} was used to filter, alongside SSoT Tag. {self.cluster_filter.name} is not tagged."  # NOQA
                    )
        elif not self.sync_vsphere_tagged_only:
            if self.cluster_filter:
                cluster_objects = Cluster.objects.filter(name=self.cluster_filter.name)
            else:
                cluster_objects = Cluster.objects.all()

        return cluster_objects

    def load_clustergroups(self):
        """Load Cluster Groups.

        This can be impacted by the Cluster Filter.
        """
        if self.cluster_filter:
            cluster_groups = ClusterGroup.objects.filter(clusters=self.cluster_filter)
        else:
            cluster_groups = ClusterGroup.objects.all()
        self.job.log_debug(message=f"Found {cluster_groups.count()} Nautobot ClusterGroup objects")
        for diffsync_clustergroup in cluster_groups:
            self.get_or_instantiate(self.diffsync_clustergroup, {"name": diffsync_clustergroup.name})

    def load_virtual_machines(self):
        """Load Nautobot Virtual Machines."""
        virtual_machines = VirtualMachine.objects.all()
        self.job.log_debug(f"Found {virtual_machines.count()} Virtual Machine objects")
        for virtual_machine in virtual_machines:
            diffsync_virtualmachine, _ = self.get_or_instantiate(
                self.diffsync_virtual_machine,
                {"name": virtual_machine.name},
                {
                    "vcpus": virtual_machine.vcpus if virtual_machine.vcpus else None,
                    "memory": virtual_machine.memory if virtual_machine.memory else None,
                    "disk": virtual_machine.disk if virtual_machine.disk else None,
                    "status": virtual_machine.status.name,
                    "cluster": virtual_machine.cluster.name,
                    "primary_ip4": virtual_machine.primary_ip4.host if bool(virtual_machine.primary_ip4) else None,
                    "primary_ip6": virtual_machine.primary_ip6.host if bool(virtual_machine.primary_ip6) else None,
                },
            )
            diffsync_cluster = self.get(self.diffsync_cluster, virtual_machine.cluster.name)
            diffsync_cluster.add_child(diffsync_virtualmachine)

            # Load Virtual Machine Interfaces
            self.load_vm_interfaces(virtual_machine, diffsync_virtualmachine)

    def load_ipaddress(self, nautobot_vm_interface, diffsync_vminterface, diffsync_vm_object):
        """Load Interface IP Addresses."""
        for ip_address in nautobot_vm_interface.ip_addresses.all():
            diffsync_ipaddress, _ = self.get_or_instantiate(
                self.diffsync_ipaddress,
                {"ip_address": ip_address.host, "prefix_length": ip_address.prefix_length},
                {
                    "state": ip_address.status.name,
                    "mac_address": diffsync_vminterface.mac_address,
                    "vm_interface_name": diffsync_vminterface.name,
                    "vm_name": diffsync_vm_object.name,
                },
            )
            diffsync_vminterface.add_child(diffsync_ipaddress)

    def load_vm_interfaces(self, nautobot_virtual_machine, diffsync_vm_object):
        """Load VM Interfaces."""
        for vm_interface in nautobot_virtual_machine.interfaces.all():
            diffsync_vminterface, _ = self.get_or_instantiate(
                self.diffsync_vminterface,
                {"name": vm_interface.name, "virtual_machine": nautobot_virtual_machine.name},
                {"enabled": vm_interface.enabled, "mac_address": str(vm_interface.mac_address).lower()},
            )
            diffsync_vm_object.add_child(diffsync_vminterface)
            self.load_ipaddress(vm_interface, diffsync_vminterface, diffsync_vm_object)

    def load_clusters(self, ssot_tag):
        """Load Clusters."""
        cluster_objects = self.get_initial_cluster(ssot_tag)
        self.job.log_debug(message=f"Found {cluster_objects.count()} Nautobot Cluster objects")

        for cluster_record in cluster_objects:
            diffsync_cluster, _ = self.get_or_instantiate(
                self.diffsync_cluster,
                {"name": cluster_record.name},
                {
                    "cluster_type": cluster_record.type.name,
                    "group": cluster_record.group.name if cluster_record.group else None,
                },
            )

            if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
                # Merge child into parent ClusterGroup
                if cluster_record.group:
                    cluster_group_parent = self.get(self.diffsync_clustergroup, cluster_record.group.name)
                    cluster_group_parent.add_child(diffsync_cluster)
                elif defaults.DEFAULT_USE_CLUSTERS:
                    self.job.log_warning(
                        message=f"{cluster_record}, is missing association to a Cluster Group. Please correct to ensure proper sync. `ENFORCE_CLUSTER_GROUP_TOP_LEVEL` is enabled.",  # NOQA
                        obj=cluster_record,
                    )

    def load_data(self):
        """Add Nautobot Site objects as DiffSync Location models."""
        ssot_tag = create_ssot_tag()
        # Load DataCenters first.
        # if defaults.DEFAULT_USE_CLUSTERS:
        self.load_clustergroups()
        # Load Clusters. This can used to filter by TAG or Cluster to minimize
        # The number of Virtual Machines from vSphere coming into Nautobot.
        self.load_clusters(ssot_tag)
        # Load Virtual Machine
        self.load_virtual_machines()

    def load(self):
        """Load data from Nautobot."""
        self.load_data()
