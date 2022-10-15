# Overview of Nautobot SSoT vSphere

## Configuration Settings

`VSPHERE_TYPE`

- This is the default Cluster Type that will be created in Nautobot and associated to every Cluster discovered.

`ENFORCE_CLUSTER_GROUP_TOP_LEVEL`

- `Diffsync` has a concept of `Top Level`. This application defaults to the `ClusterGroup` as Top Level, which translates to a vSphere DataCenter. This can be changed to have a Cluster in vSphere be the Top Level and ignore DataCenters.

`VSPHERE_VM_STATUS_MAP, VSPHERE_IP_STATUS_MAP, VSPHERE_VM_INTERFACE_MAP`

- These are dictionary (maps) that translate the vSphere value to something Nautobot can understand. You must be sure that the values provided are valid before manipulating these maps.

```bash
- `VSPHERE_VM_STATUS_MAP` Defaults to {"POWERED_OFF": "Offline", "POWERED_ON": "Active", "SUSPENDED": "Suspended"}
- `VSPHERE_IP_STATUS_MAP` Defaults to {"PREFERRED": "Active", "UNKNOWN": "Reserved"}
- `VSPHERE_VM_INTERFACE_MAP` Defaults to {"NOT_CONNECTED": False, "CONNECTED": True}
```

`PRIMARY_IP_SORT_BY`

- Virtual Machines can have many different IP Addresses associated to many interfaces. As there is no overall business logic that will satisfy which IP will be used as the Primary IP of a Virtual Machine in Nautobot, there is an option to decide by lowest or highest. The total number of IP's are gathered, sorted and assigned to the VM based on the value of this setting. Anything other than `Lowest` will assign the highest IP value found on the Virtual Machine.

`DEFAULT_USE_CLUSTERS` and `DEFAULT_CLUSTER_NAME`

- This experimental feature allows users of vSphere which contain no `Clusters` in their environment. The `DEFAULT_USE_CLUSTERS` needs to be set to `False` and a name of your choosing would be assigned to `DEFAULT_CLUSTER_NAME`. A `Cluster` is a requirement of a `Virtual Machine` in Nautobot.

`DEFAULT_IGNORE_LINK_LOCAL`

- Defaults to `True` and drops any link-local address found on a vSphere vm that has an IPv6 address assigned.
