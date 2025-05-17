# This is the setup script for building and installing the Python package
# It tells setuptools how to package and install your code

from setuptools import setup, find_packages  # Import packaging utilities

# Call to setup() defines the package metadata and contents
setup(
    name="employee_events",          # The name of the package (used when installing or importing)
    version="0.1.0",                 # Version number (can be incremented for future updates)
    packages=find_packages(),        # Automatically find and include all packages/modules
)
