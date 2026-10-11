#!/usr/bin/env python3
# --------------------( LICENSE                            )--------------------
# Copyright (c) 2014-2026 Beartype authors.
# See "LICENSE" for further details.

'''
**Beartype slow cave** (i.e., private subset of the public :mod:`beartype.cave`
subpackage profiled to *not* be efficiently importable at :mod:`beartype`
startup and thus *not* safely importable throughout the internal
:mod:`beartype` codebase).

This submodule currently imports from expensive third-party packages on
importation (e.g., :mod:`numpy`) despite :mod:`beartype` itself *never*
requiring those imports. Until resolved, that subpackage is considered tainted.
'''

# ....................{ TODO                               }....................
#FIXME: Excise this submodule away, please. This submodule was a horrendous idea
#and has plagued the entire "beartype.cave" subpackage with unnecessary slowdown
#at import time. It's simply time for this to go, please.

# ....................{ IMPORTS                            }....................
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# WARNING: To avoid polluting the public module namespace, external attributes
# should be locally imported at module scope *ONLY* under alternate private
# names (e.g., "from argparse import ArgumentParser as _ArgumentParser" rather
# than merely "from argparse import ArgumentParser").
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

from argparse import (
    ArgumentParser,
    _SubParsersAction,
)

# ....................{ TYPES ~ lib                        }....................
# Types conditionally dependent upon the importability of third-party
# dependencies. These types are subsequently redefined by try-except blocks
# below and initially default to "UnavailableType" for simple types.

# ....................{ TYPES ~ stdlib : argparse          }....................
ArgParserType = ArgumentParser
'''
Type of argument parsers parsing all command-line arguments for either
top-level commands *or* subcommands of those commands.
'''


ArgSubparsersType = _SubParsersAction
'''
Type of argument subparser containers parsing subcommands for parent argument
parsers parsing either top-level commands *or* subcommands of those commands.
'''
