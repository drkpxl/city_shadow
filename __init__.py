"""
Shadow City Generator
A tool for creating 3D-printable city maps from OpenStreetMap data.

This package provides tools to convert OpenStreetMap GeoJSON data into
3D-printable city models with artistic styling options.
"""

from .lib.converter import EnhancedCityConverter
from .lib.preprocessor import GeoJSONPreprocessor
from .lib.preview import OpenSCADIntegration

__version__ = "0.1.0"
__author__ = "Shadow City Generator Team"
__license__ = "MIT"

__all__ = ["EnhancedCityConverter", "GeoJSONPreprocessor", "OpenSCADIntegration"]
