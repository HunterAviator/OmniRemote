"""
OmniRemote Device Catalog - Main Entry Point

This module provides backward compatibility with the old catalog API
while using the new organized catalog structure in the catalog/ subfolder.
"""
from __future__ import annotations

# Import everything from the new catalog module
from .catalog import (
    # Data classes
    DeviceProfile,
    IRCode,
    RFCode,
    NetworkCommand,
    ControlMethod,
    IRProtocol,
    
    # Helper functions
    nec,
    nec_ext,
    samsung,
    sony,
    rc5,
    rc6,
    panasonic,
    jvc,
    
    # Brand logos
    BRAND_LOGOS,
    
    # Registry functions
    register_profile,
    get_profile,
    get_profiles_by_category,
    get_profiles_by_brand,
    search_catalog,
    list_all_profiles,
    get_categories,
    get_brands,
    
    # Private registry access (for panel.py compatibility)
    _CATALOG,
    _CATALOG_BY_CATEGORY,
    _CATALOG_BY_BRAND,
)

# Legacy compatibility aliases
DEVICE_CATALOG = _CATALOG
CATALOG_BY_CATEGORY = _CATALOG_BY_CATEGORY
CATALOG_BY_BRAND = _CATALOG_BY_BRAND

def get_catalog_device(device_id: str) -> DeviceProfile | None:
    """Legacy alias for get_profile."""
    return get_profile(device_id)

def list_catalog() -> list[dict]:
    """Legacy alias for list_all_profiles."""
    return list_all_profiles()
