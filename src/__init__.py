"""
StructureMaster - Main Package
A comprehensive tool for project structure analysis, generation, and documentation.
"""

__version__ = '1.0.0'
__author__ = 'StructureMaster Team'
__license__ = 'MIT'

from .config import Config
from .utils import Utils

__all__ = [
    'Config',
    'Utils',
    '__version__',
    '__author__',
    '__license__',
]
