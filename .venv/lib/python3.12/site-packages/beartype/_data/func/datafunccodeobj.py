#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright (c) 2014-2026 Beartype authors.
# See "LICENSE" for further details.

'''
Project-wide **code object globals** (i.e., global constants describing code
objects of callables, classes, and modules).

This private submodule is *not* intended for importation by downstream callers.
'''

# ....................{ STRINGS                            }....................
CODE_OBJECT_BASENAME_MODULE_OR_EVAL = '<module>'
'''
Arbitrary string constant unconditionally assigned to both the ``co_name`` *and*
``co_qualname`` attributes of the code objects of all pure-Python modules (i.e.,
the top-most lexical scope of each module in the current call stack) *and*
pure-Python code snippets dynamically executed by the :func:`exec` and
:func:`eval` builtins.

This constant enables callers to reliably differentiate between code objects
encapsulating:

* Module, :func:`exec`, and :func:`eval` scopes, whose ``co_name`` variable is
  this constant.
* Class and callable scopes, whose ``co_name`` variable is *not* this constant.
'''


CODE_OBJECT_FILENAME_EVAL = '<string>'
'''
Arbitrary string constant unconditionally assigned to the ``co_filename``
attribute of the code objects of all pure-Python code snippets dynamically
executed by the :func:`exec` and :func:`eval` builtins.

This constant enables callers to reliably differentiate between code objects
encapsulating:

* :func:`exec` and :func:`eval` scopes, whose ``co_filename`` variable is this
  constant.
* Module, class, and callable scopes, whose ``co_filename`` variable is *not*
  this constant.
'''
