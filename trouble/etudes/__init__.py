# This file makes 'trouble/etudes' a Python package.

# You can explicitly import etude modules or classes here if automatic discovery
# proves too complex or unreliable, or to control the order/availability.
# For example:
# from .zero import etude_impl as zero_etude
# from .one import etude_impl as one_etude

# The EtudeRegistry's discover_etudes method will attempt to dynamically
# find Etude subclasses in this package.

# To make discovery more robust, each etude sub-package (e.g., trouble.etudes.zero)
# should ensure its main Etude class (e.g., EtudeZero) is imported into its
# own __init__.py (e.g., trouble/etudes/zero/__init__.py).

# Example: trouble/etudes/zero/__init__.py could contain:
# from .etude_impl import EtudeZero
# This way, when EtudeRegistry iterates through modules in 'trouble.etudes',
# importing 'trouble.etudes.zero' would make EtudeZero available for inspection.

# For now, this __init__.py can remain simple. The discovery logic is in EtudeRegistry.
print("trouble.etudes package loaded.")
