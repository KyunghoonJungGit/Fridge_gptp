"""
@description
Marks 'python_client' as a Python package. Exposes the FridgeClient class and possibly other helpers.

Key features:
1. Helps Python code discover and import 'FridgeClient' from client.py
2. Typically empty or with limited top-level imports.
3. For now, we do not do a wildcard import here to keep a clean namespace.

@dependencies
- None directly, but references client.py if needed.

@notes
- This is required so 'pip install .' can treat this as a valid Python package.
"""
