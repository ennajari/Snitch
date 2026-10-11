#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright (c) 2014-2026 Beartype authors.
# See "LICENSE" for further details.

'''
Project-wide **script globals** (i.e., global constants describing executable
and typically unimportable third-party Python scripts).

This private submodule is *not* intended for importation by downstream callers.
'''

# ....................{ CONSTANTS ~ strings                }....................
SCRIPT_MODULE_NAME = '__main__'
'''
Fully-qualified name of the **script module** (i.e., arbitrary module name
assigned to scripts run outside of a package context).
'''
