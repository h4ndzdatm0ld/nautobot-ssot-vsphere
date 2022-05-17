"""Diff sync shared adapter class attritbutes to synchronize applications."""
from diffsync import DiffSync

from nautobot_ssot_vsphere.diffsync import defaults, diffsync_models


class DiffSyncModelAdapters(DiffSync):
    """Shared adapter for DiffSync Models."""

    diffsync_virtual_machine = diffsync_models.DiffSyncVirtualMachine
    diffsync_clustergroup = diffsync_models.DiffSyncClusterGroup
    diffsync_cluster = diffsync_models.DiffSyncCluster
    diffsync_vminterface = diffsync_models.DiffSyncVMInterface
    diffsync_ipaddress = diffsync_models.DiffSyncIpAddress

    if defaults.DEFAULT_USE_CLUSTERS:
        if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
            top_level = ["diffsync_clustergroup"]
        else:
            top_level = ["diffsync_cluster", "diffsync_clustergroup"]
    else:
        top_level = ["diffsync_virtual_machine"]
