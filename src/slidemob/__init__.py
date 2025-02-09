"""SlideMob package."""
from importlib.metadata import version

try:
    __version__ = version("slidemob")
except Exception:
    __version__ = "unknown"
