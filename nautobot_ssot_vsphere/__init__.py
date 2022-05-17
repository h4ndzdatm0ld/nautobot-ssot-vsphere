"""Plugin declaration for nautobot_ssot_vsphere."""
# Metadata is inherited from Nautobot. If not including Nautobot in the environment, this should be added
from nautobot.core.signals import nautobot_database_ready
from nautobot.extras.plugins import PluginConfig

from .signals import nautobot_database_ready_callback

try:
    from importlib import metadata
except ImportError:
    # Python version < 3.8
    import importlib_metadata as metadata

__version__ = metadata.version(__name__)


class NautobotSsotVsphereConfig(PluginConfig):
    """Plugin configuration for the nautobot_ssot_vsphere plugin."""

    name = "nautobot_ssot_vsphere"
    verbose_name = "Nautobot SSoT vSphere"
    version = __version__
    author = "h4ndzdatm0ld"
    description = "Nautobot SSoT vSphere."
    base_url = "nautobot-ssot-vsphere"
    required_settings = [
        "VSPHERE_URI",
        "VSPHERE_VERIFY_SSL",
        "VSPHERE_PASSWORD",
        "VSPHERE_USERNAME",
    ]
    min_version = "1.2.0"
    max_version = "1.9999"
    default_settings = {
        "VSPHERE_VM_STATUS_MAP": {"POWERED_OFF": "Offline", "POWERED_ON": "Active"},
        "VSPHERE_VM_INTERFACE_MAP": {"NOT_CONNECTED": False, "CONNECTED": True},
        "ENFORCE_CLUSTER_GROUP_TOP_LEVEL": True,
        "VSPHERE_IP_STATUS_MAP": {"PREFERRED": "Active", "UNKNOWN": "Reserved"},
        "PRIMARY_IP_SORT_BY": "Lowest",
        "VSPHERE_TYPE": "VMWare vSphere",
    }
    caching_config = {}

    def ready(self):
        """Ready signal."""
        super().ready()
        nautobot_database_ready.connect(nautobot_database_ready_callback, sender=self)


config = NautobotSsotVsphereConfig  # pylint:disable=invalid-name
