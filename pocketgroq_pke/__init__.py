"""
PocketgroqPKE - Procedural Knowledge Extractor for PocketGroq
"""

from .types import Step, Procedure
from .extractor import ProceduralExtractor

__version__ = '0.1.0'
__all__ = ['ProceduralExtractor', 'Step', 'Procedure']

# Version compatibility check
import pkg_resources
pocketgroq_version = pkg_resources.get_distribution('pocketgroq').version
if pkg_resources.parse_version(pocketgroq_version) < pkg_resources.parse_version('0.5.5'):
    import warnings
    warnings.warn(
        'PocketgroqPKE requires PocketGroq >= 0.5.5. '
        f'Found version {pocketgroq_version}. Some features may not work correctly.',
        RuntimeWarning
    )
