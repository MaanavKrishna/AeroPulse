"""Standalone SVG charts the API serves as files (social images, downloads). The website
draws its own interactive charts in web/ (Next.js)."""
from .base import LEVEL_NAMES, level_index
from .ribbon import ribbon_standalone

__all__ = ["LEVEL_NAMES", "level_index", "ribbon_standalone"]
