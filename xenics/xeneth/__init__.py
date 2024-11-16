"""
xeneth.capi package

Wrapper for XenEth C SDK
"""
from xenics.xeneth.capi.enums import XEnumerationFlags, XDeviceStates, XGetFrameFlags
from xenics.xeneth.xcamera import XCamera
from xenics.xeneth.discovery import enumerate_devices

print("Xeneth packages imported locally")
print("This message printed from './xeneth/__init__.py'")

# Export essentials for the high level API
__all__ = ['XEnumerationFlags', 'XDeviceStates',
     'enumerate_devices', 'XCamera', 'XGetFrameFlags']
