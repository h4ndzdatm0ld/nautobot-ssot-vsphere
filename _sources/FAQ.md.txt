# Frequently Asked Questions

## A diff always appears even if virtual machines are created. Why?

- The `Top Level` DiffSync object is the `Cluster Group` which translates to a a vSphere `DataCenter`. A DataCenter can house many `Clusters`. The problem happens when Cluster created in Nautobot, do not belong to a `ClusterGroup`. If this is the case, they will never be registered into the common DiffSync model, thus appearing as a diff.

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

### Measurements of Capacity (Disks)

The disk total is an aggregate of all virtual disks available on the virtual machine.