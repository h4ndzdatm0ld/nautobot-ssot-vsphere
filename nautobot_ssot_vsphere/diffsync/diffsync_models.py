#  pylint: disable=inconsistent-return-statements
"""Diffsync Models."""
from typing import Any, List, Optional

from diffsync import DiffSyncModel
from django.db import IntegrityError
from django.utils.text import slugify
from nautobot.extras.models.statuses import Status
from nautobot.ipam.models import IPAddress
from nautobot.virtualization.models import (
    Cluster,
    ClusterGroup,
    ClusterType,
    VirtualMachine,
    VMInterface,
)
from netutils.mac import is_valid_mac

from nautobot_ssot_vsphere.diffsync import defaults
from nautobot_ssot_vsphere.utilities import tag_object


class DiffSyncExtras(DiffSyncModel):
    """Additional components to mix and subclass from with `DiffSyncModel`."""

    def ordered_delete(self, nautobot_object: Any):
        """Add to `objects_to_delete` for ordered deletion.

        Args:
            nautobot_object (Any): Any type of Nautobot object
            safe_delete_status (Optional[str], optional): Status name, optional
            as some objects don't have status field. Defaults to None.
        """
        # This allows private class naming of nautobot objects to be ordered for delete()
        # Example definition in adapter class var: _site = Site
        self.diffsync.objects_to_delete[f"_{nautobot_object.__class__.__name__.lower()}"].append(
            nautobot_object
        )  # pylint: disable=protected-access
        super().delete()
        return self


class DiffSyncClusterGroup(DiffSyncExtras):
    """Virtual Machine DiffSync model."""

    _modelname = "diffsync_clustergroup"
    _identifiers = ("name",)
    _attributes = ()

    if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
        _children = {"diffsync_cluster": "clusters"}
        clusters: Optional[List["DiffSyncCluster"]] = list()  # pylint: disable=use-list-literal

    name: str

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create ClusterGroup."""
        try:
            clustergroup, _ = ClusterGroup.objects.get_or_create(
                name=ids["name"],
                slug=slugify(ids["name"]),
            )
            tag_object(clustergroup)
        except IntegrityError:
            diffsync.job.log_warning(message=f"ClusterGroup {ids['name']} already exists.")
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete Cluster Group in Nautobot."""
        try:
            self.ordered_delete(ClusterGroup.objects.get(name=self.name))
            return self
        except ClusterGroup.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match Cluster Group by name, {self.name}")


class DiffSyncCluster(DiffSyncExtras):
    """Cluster DiffSync model."""

    _modelname = "diffsync_cluster"
    _identifiers = ("name",)
    _attributes = ("cluster_type", "group")
    _children = {"diffsync_virtual_machine": "virtualmachines"}

    name: str
    cluster_type: str
    group: Optional[str]

    virtualmachines: List["DiffSyncVirtualMachine"] = list()  # pylint: disable=use-list-literal

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create Objects in Nautobot."""
        try:
            _default_vsphere_type, _ = ClusterType.objects.get_or_create(
                name=defaults.DEFAULT_VSPHERE_TYPE
            )  # pylint: disable=invalid-name
            tag_object(_default_vsphere_type)
            cluster, _ = Cluster.objects.get_or_create(
                name=ids["name"],
                type=_default_vsphere_type,
            )
            if attrs["group"]:
                clustergroup, _ = ClusterGroup.objects.get_or_create(name=attrs["group"])
                cluster.group = clustergroup
            tag_object(cluster)
        except IntegrityError:
            diffsync.job.log_warning(message=f"ClusterGroup {ids['name']} already exists.")
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete device in Nautobot."""
        try:
            self.ordered_delete(Cluster.objects.get(name=self.name))
            return self
        except Cluster.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match Cluster by name, {self.name}")

    def update(self, attrs):
        """Update devices in Nautbot based on Source."""
        cluster = Cluster.objects.get(name=self.name)
        _default_vsphere_type, _ = ClusterType.objects.get_or_create(name=defaults.DEFAULT_VSPHERE_TYPE)
        if attrs.get("group"):
            clustergroup, _ = ClusterGroup.objects.get_or_create(name=attrs["group"])
            cluster.group = clustergroup
        if attrs.get("cluster_type"):
            cluster.type = _default_vsphere_type
        tag_object(cluster)


class DiffSyncVMInterface(DiffSyncExtras):
    """VMInterface DiffSync Model."""

    _modelname = "diffsync_vminterface"
    _identifiers = ("name", "virtual_machine")
    _attributes = ("enabled", "mac_address")
    _children = {"diffsync_ipaddress": "ip_addresses"}

    name: str
    virtual_machine: str
    enabled: bool
    mac_address: Optional[str]

    ip_addresses: List["DiffSyncIpAddress"] = list()  # pylint: disable=use-list-literal

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VirtualMachine VMInterface in Nautobot."""
        try:
            vm_interface, _ = VMInterface.objects.get_or_create(
                name=ids["name"],
                enabled=attrs["enabled"],
                virtual_machine=VirtualMachine.objects.get(name=ids["virtual_machine"]),
                mac_address=attrs["mac_address"],
            )
            tag_object(vm_interface)
        except IntegrityError as error:
            diffsync.job.log_warning(
                message=f"Virtual Machine Interface {ids['name']} already exists. {error}", obj=vm_interface
            )
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete VMInterfaces from Virtual Machine."""
        try:
            if is_valid_mac(self.mac_address):
                interface = VMInterface.objects.get(
                    name=self.name,
                    virtual_machine=VirtualMachine.objects.get(name=self.virtual_machine),
                    mac_address=self.mac_address,
                )
            else:
                interface = VMInterface.objects.get(
                    name=self.name,
                    virtual_machine=VirtualMachine.objects.get(name=self.virtual_machine),
                )
            self.ordered_delete(interface)
            return self
        except VMInterface.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match VMInterface by name, {self.name}")

    def update(self, attrs):
        """Update VMInterface on Virtual Machine."""
        try:
            vm_interface = VMInterface.objects.get(
                name=self.name,
                virtual_machine=VirtualMachine.objects.get(name=self.virtual_machine),
            )
            vm_interface.enabled = attrs["enabled"]

            if attrs.get("mac_address"):
                vm_interface.mac_address = attrs["mac_address"]
            # Tag and Update time stamp on object
            tag_object(vm_interface)
            # Call the super().update() method to update the in-memory DiffSyncModel instance
            return super().update(attrs)
        except VirtualMachine.DoesNotExist:
            self.diffsync.job.log_warning(
                f"Unable to match VM Interface by name, {self.name} and VM {self.virtual_machine}"
            )


class DiffSyncIpAddress(DiffSyncExtras):
    """VMInterface DiffSync Model."""

    _modelname = "diffsync_ipaddress"
    _identifiers = ("ip_address", "prefix_length")
    _attributes = ("state", "mac_address", "vm_interface_name", "vm_name")

    ip_address: str
    prefix_length: int
    state: str
    mac_address: str
    vm_interface_name: Optional[str]
    vm_name: Optional[str]

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create IP Address in Nautobot."""
        try:

            virtual_machine = VirtualMachine.objects.get(name=attrs["vm_name"])
            interface = VMInterface.objects.get(
                name=attrs["vm_interface_name"],
                virtual_machine=virtual_machine,
            )
            ip_address, _ = IPAddress.objects.get_or_create(
                address=f"{ids['ip_address']}/{ids['prefix_length']}",
                status=Status.objects.get_for_model(IPAddress).get(name=attrs["state"]),
            )
            interface.ip_addresses.add(ip_address)
            interface.validated_save()

            # Set Virtual Machine Primary IP through IP - > Interface - > VM
            primary_ip_attr = f"primary_ip{ip_address.address.version}"
            diffsync_vm = diffsync.get(diffsync.diffsync_virtual_machine, {"name": virtual_machine.name})
            if ids["ip_address"] == diffsync_vm.primary_ip4:
                setattr(interface.parent, primary_ip_attr, ip_address)
                interface.parent.save()
                interface.save()
                diffsync.job.log_debug(message=f"{primary_ip_attr} IP Set to {ip_address} on interface {interface}")

            if ids["ip_address"] == diffsync_vm.primary_ip6:
                setattr(interface.parent, primary_ip_attr, ip_address)
                interface.parent.save()
                interface.save()
                diffsync.job.log_debug(message=f"{primary_ip_attr} IP Set to {ip_address} on interface {interface}")

            tag_object(ip_address)

        except IntegrityError as error:
            diffsync.job.log_warning(message=f"IP Address {ids['ip_address']} already exists. {error}", obj=ip_address)

        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete VMInterfaces from Virtual Machine."""
        try:
            self.ordered_delete(
                IPAddress.objects.get(
                    host=self.ip_address,
                    prefix_length=self.prefix_length,
                ),
            )
            return self
        except IPAddress.DoesNotExist:
            self.diffsync.job.log_warning(
                f"Unable to match IPAddress by host {self.ip_address} and Prefix Length {self.prefix_length}"
            )

    def update(self, attrs):
        """Update VMInterface on Virtual Machine."""
        try:
            ip_address = IPAddress.objects.get(
                host=self.ip_address,
                prefix_length=self.prefix_length,
            )
            if attrs.get("status"):
                ip_address.status = Status.objects.get(attrs["state"])

            # Tag and Update time stamp on object
            tag_object(ip_address)
            # Call the super().update() method to update the in-memory DiffSyncModel instance
            return super().update(attrs)
        except IPAddress.DoesNotExist:
            self.diffsync.job.log_warning(
                f"Unable to match IPAddress by host {self.ip_address} and Prefix Length {self.prefix_length}"
            )


class DiffSyncVirtualMachine(DiffSyncExtras):
    """Virtual Machine DiffSync model."""

    _modelname = "diffsync_virtual_machine"
    _identifiers = ("name",)
    # Handle Hypervisors users that do not use clusters.
    if defaults.DEFAULT_USE_CLUSTERS:
        _attributes = ("status", "vcpus", "memory", "disk", "cluster", "primary_ip4", "primary_ip6")
        cluster: str
    else:
        _attributes = ("status", "vcpus", "memory", "disk", "primary_ip4", "primary_ip6")
    _children = {"diffsync_vminterface": "interfaces"}

    name: str
    status: Optional[str]
    vcpus: Optional[int]
    memory: Optional[int]
    disk: Optional[int]
    primary_ip4: Optional[str]
    primary_ip6: Optional[str]

    interfaces: List["DiffSyncVMInterface"] = list()  # pylint: disable=use-list-literal

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create VirtualMachine in Nautobot."""
        try:
            status = Status.objects.get(name=attrs["status"])
            if defaults.DEFAULT_USE_CLUSTERS:
                cluster = Cluster.objects.get(name=attrs["cluster"])
            else:
                _default_vsphere_type, _ = ClusterType.objects.get_or_create(
                    name=defaults.DEFAULT_VSPHERE_TYPE
                )  # pylint: disable=invalid-name
                tag_object(_default_vsphere_type)
                cluster, _ = Cluster.objects.get_or_create(
                    name=defaults.DEFAULT_CLUSTER_NAME,
                    type=_default_vsphere_type,
                )
                tag_object(cluster)
            virtual_machine, _ = VirtualMachine.objects.get_or_create(
                name=ids["name"],
                status=status,
                cluster=cluster,
                vcpus=attrs["vcpus"],
                memory=attrs["memory"],
                disk=attrs["disk"],
            )
            tag_object(virtual_machine)
        except IntegrityError as error:
            diffsync.job.log_warning(message=f"Virtual Machine {ids['name']} already exists. {error}")
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def delete(self) -> Optional["DiffSyncModel"]:
        """Delete Virtual Machine."""
        try:
            self.ordered_delete(VirtualMachine.objects.get(name=self.name))
            return self
        except VirtualMachine.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match VirtualMachine by name, {self.name}")

    def update(self, attrs):
        """Update Virtual Machine."""
        try:
            virtual_machine = VirtualMachine.objects.get(name=self.name)
            if attrs.get("status"):
                vm_status = Status.objects.get(name=attrs.get("status"))
                virtual_machine.status = vm_status
            if attrs.get("vcpus"):
                virtual_machine.vcpus = attrs["vcpus"]
            if attrs.get("memory"):
                virtual_machine.memory = attrs["memory"]
            if attrs.get("disk"):
                virtual_machine.disk = attrs["disk"]
            if defaults.DEFAULT_USE_CLUSTERS:
                if attrs.get("cluster"):
                    if virtual_machine.cluster.name != attrs["cluster"]:
                        virtual_machine.cluster = attrs["cluster"]
            if attrs.get("primary_ip4") or attrs.get("primary_ip6"):
                for interface in virtual_machine.interfaces.all():
                    for ip_address in interface.ip_addresses.all():
                        primary_ip_attr = f"primary_ip{ip_address.address.version}"
                        if not ip_address.host == attrs.get(primary_ip_attr):
                            continue
                        setattr(interface.parent, primary_ip_attr, ip_address)
                        interface.parent.save()
                        interface.save()

            # Tag and Update time stamp on object
            tag_object(virtual_machine)
            # Call the super().update() method to update the in-memory DiffSyncModel instance
            return super().update(attrs)
        except VirtualMachine.DoesNotExist:
            self.diffsync.job.log_warning(f"Unable to match VirtualMachine by name, {self.name}")


if defaults.DEFAULT_USE_CLUSTERS:
    DiffSyncClusterGroup.update_forward_refs()
    DiffSyncCluster.update_forward_refs()
    DiffSyncVirtualMachine.update_forward_refs()
    DiffSyncVMInterface.update_forward_refs()
    DiffSyncIpAddress.update_forward_refs()
else:
    DiffSyncVirtualMachine.update_forward_refs()
    DiffSyncVMInterface.update_forward_refs()
    DiffSyncIpAddress.update_forward_refs()
