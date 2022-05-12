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

Currently, this application is expecting to get cluster information from vSphere API and populate the DiffSync Models. At this time, there is no way around it. Contributions are welcome to override or provide a default cluster and bypass the API call. Nautobot does expect a Virtual Machine to live in a cluster, but that may change in the future. A solution to this would be good, happy to collaborate.
