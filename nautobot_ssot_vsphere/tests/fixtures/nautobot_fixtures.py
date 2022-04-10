"""Nautobot Object Fixtures."""
from django.utils.text import slugify
from nautobot.dcim.models import DeviceRole, Region, Site
from nautobot.extras.models import Status
from nautobot.tenancy.models import Tenant
from nautobot.virtualization.models import Cluster  # VMInterface,
from nautobot.virtualization.models import ClusterGroup, ClusterType, VirtualMachine


def create_cluster_group(name: str = "Development Cluster Group"):
    """Create ClusterGroup.

    Args:
        name (str, optional): _description_. Defaults to "Development Cluster Group".

    Returns:
        ClusterGroup: ClusterGroup
    """
    clustergroup, _ = ClusterGroup.objects.get_or_create(
        name=name, slug=slugify(name), description="Development Cluster Description"
    )
    return clustergroup


def create_cluster_type(name: str = "VMWare vSphere"):
    """Create Cluster Type.

    Args:
        name (str, optional): _description_. Defaults to "VMWare vSphere".

    Returns:
        _type_: _description_
    """
    cluster_type, _ = ClusterType.objects.get_or_create(
        name=name, slug=slugify(name), description="Development Cluster Type"
    )
    return cluster_type


def create_cluster(
    name: str = "Development Cluster",
    cluster_type: str = "VMWare vSphere",
    diffsync_clustergroup: str = "Development DataCenter",
):
    """Create Cluster.

    Args:
        name (str, optional): _description_. Defaults to "Development Cluster".
        cluster_type (str, optional): _description_. Defaults to "VMWare vSphere".
        diffsync_clustergroup (str, optional): _description_. Defaults to "Development DataCenter".

    Returns:
        _type_: _description_
    """
    tenant, _ = Tenant.objects.get_or_create(name="Dev", slug="dev")
    region_name = "US-West-1"
    region, _ = Region.objects.get_or_create(name=region_name, slug=slugify(region_name))
    site_name = "Development Site"
    site, _ = Site.objects.get_or_create(name=site_name, slug=slugify(site_name), region=region)
    cluster, _ = Cluster.objects.get_or_create(
        name=name,
        type=create_cluster_type(name=cluster_type),
        group=create_cluster_group(name=diffsync_clustergroup),
        tenant=tenant,
        site=site,
    )
    return cluster


def create_env():
    """Create Env."""
    cluster = create_cluster()
    tenant, _ = Tenant.objects.get_or_create(name="Dev", slug="dev")
    role_name = "Development Role"
    role, _ = DeviceRole.objects.get_or_create(name=role_name, slug=slugify(role_name), color="ff0000")
    status = Status.objects.get(name="Active")
    for virtual_machine in range(10):
        VirtualMachine.objects.get_or_create(
            cluster=cluster,
            tenant=tenant,
            status=status,
            role=role,
            name=f"Development-VM-{virtual_machine}",
            vcpus=2,
            memory=4096,
            disk=100,
        )
