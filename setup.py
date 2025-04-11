"""
@description
A minimal setuptools configuration to package the 'python_client' as 'fridge_client_lib'.

Key features:
1. Exposes the python_client folder as a Python package
2. 'pip install .' will install it system-wide or in a virtual environment
3. The examples/ directory is included as well but typically not installed as modules

@dependencies
- setuptools

@notes
- In a production context, you'd specify a more complete setup: version, author, license, dependencies, etc.
"""

import setuptools

setuptools.setup(
    name="fridge_client_lib",
    version="0.1.0",
    author="Lab Team",
    description="A Python client for remote fridge monitoring and control",
    packages=["python_client"],
    # If we want to include the examples in the sdist but not as installable code:
    # we might set `include_package_data=True` and use MANIFEST.in, but we keep it minimal here.
    install_requires=[
        "requests>=2.20.0"
    ],
    python_requires=">=3.6",
)
