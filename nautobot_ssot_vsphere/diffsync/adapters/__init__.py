"""Collection of adapters."""
from .adapter_nautobot import NautobotDiffSync
from .adapter_vsphere import VsphereDiffSync

__all__ = ("NautobotDiffSync", "VsphereDiffSync")
