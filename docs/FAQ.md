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

The plugin was built with vSphere environments that use Clusters within Datacenters. However, there is a way to change the default behavior to allow sync against vSphere environments that do not use Clusters. Changing `DEFAULT_USE_CLUSTERS` to False in the Nautobot -> `nautobot_ssot_vsphere` plugin config dictionary, as well as `ENFORCE_CLUSTER_GROUP_TOP_LEVEL` to False. This will sync VM's and their attributes only.

> This is experimental. Also, the syncs may not behave as expected if these settings are changed once the sync has been completed with a different `Top Level` designation.

The sync behavior can be modified in several ways and the logic that enforces the diffsync `Top Level` lives in `adapters.shared.adapter_shared.py`

```python
if defaults.DEFAULT_USE_CLUSTERS:
    if defaults.ENFORCE_CLUSTER_GROUP_TOP_LEVEL:
        top_level = ["diffsync_clustergroup"]
    else:
        top_level = ["diffsync_cluster", "diffsync_clustergroup"]
else:
    top_level = ["diffsync_virtual_machine"]
```

## Is there a way to sync `hosts` into Nautobot `Device` model?

The information that is able to be retrieved from vSphere API is very limited in detail and would not be enough to satisfy creating a `Device` object in Nautobot. I'm open to suggestion's or PR's to find a solution. This would require quite a bit of default settings if we were to try to fill in the gaps, which could simply pollute the data in Nautobot excessively. 

## Warning Error: `{{ cluster_name }}, is missing association to a Cluster Group. Please correct to ensure proper sync. ENFORCE_CLUSTER_GROUP_TOP_LEVEL is enabled.`

Diffsync Top Level can be manipulated via configuration options for the Plugin. If an existent Cluster is found in Nautobot during a sync job without association to the Cluster Group, the sync won't update correctly. Either manually add the ClusterGroup to the Cluster in the UI, change the `ENFORCE_CLUSTER_GROUP_TOP_LEVEL` to `False` and use the `Cluster` as the top level or as last resort, remove the Cluster from Nautobot and start a fresh sync from vSphere with this application. 