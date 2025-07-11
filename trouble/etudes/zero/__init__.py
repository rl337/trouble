# This file makes 'trouble/etudes/zero' a Python package.

# Expose the EtudeZero class for easier discovery/import if needed,
# though the registry's discovery mechanism should find it in etude_impl.py.
from .etude_impl import EtudeZero

print("trouble.etudes.zero package loaded, EtudeZero available.")
