# Frequently Asked Questions

## A diff always appears even if virtual machines are created. Why?

- The `Top Level` DiffSync object is the `Cluster Group` which translates to a vSphere `DataCenter`. A DataCenter can house many `Clusters`. The problem happens when a Cluster created in Nautobot, does not belong to a `ClusterGroup`. If this is the case, they will never be registered into the common DiffSync model, thus appearing as a diff.

The expectations of hierarchy within Nautobot are graphed in a tree format below

```bash
ClusterGroup (DataCenter)
├── Cluster (Cluster)
│   └── VirtualMachine (VirtualMachine)
│       ├── VMInterface-1 (NIC Interface)
│       └── VMInterface-2 (NIC Interface)
└── Cluster-2 (Cluster)
    └── VirtualMachine-2  (VirtualMachine)
        └── VMInterface-1 (NIC Interface)
```

A configuration setting `ENFORCE_CLUSTER_GROUP_TOP_LEVEL` is defaulted to true, enforcing this pattern. If you'd like to allow `Clusters` to be the `Top Level`, simply set this setting to False.

## Measurements of Capacity (Disks)

The disk total is an aggregate of all virtual disks available on the virtual machine.

## I use vSphere, but I don't have any Clusters. I only have VM's under hosts.

The plugin was built with vSphere environments that use Clusters within Datacenters. However, there is a way to change the default bevahiour to allow sync against vSphere environments that do not use Clusters. Changing `DEFAULT_USE_CLUSTERS` to False in the Nautobot -> `nautobot_ssot_vsphere` plugin config dictionary, as well as `ENFORCE_CLUSTER_GROUP_TOP_LEVEL` to False. This will sync VM's and their attributes only.

> This is experimental. Also, the syncs may not behave as expected if these settings are changed once the sync has been completed with a different `Top Level` designation.

The sync behaviour can be modified in several ways and the logic that enforces the diffsync `Top Level` lives in `adapters.shared.adapter_shared.py`

```python
if defaults.DEFAULT_USE_CLUSTERS:
    if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
        top_level = ["diffsync_clustergroup"]
    else:
        top_level = ["diffsync_cluster", "diffsync_clustergroup"]
else:
    top_level = ["diffsync_virtual_machine"]
```