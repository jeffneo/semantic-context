"""qlsc-parse: turns SQL text from a query log into shapes and parse records.

T1 `fingerprint` (per distinct text, cheap) and T2 `resolve` (per shape, against a
catalog snapshot). Stateless; see plans/M1_PARSER.md for the contract.
"""

import sqlglot

__version__ = "0.1.0"
PARSER_ID = f"qlsc-parse/{__version__} sqlglot/{sqlglot.__version__}"
import sqlglot.parser  # noqa: E402

# sqlglot[c] replaces sqlglot's own modules with mypyc-compiled extension modules
COMPILED = not sqlglot.parser.__file__.endswith(".py")

from .catalog import Catalog  # noqa: E402
from .fingerprint import fingerprint  # noqa: E402
from .resolve import resolve  # noqa: E402

__all__ = ["Catalog", "fingerprint", "resolve", "PARSER_ID", "__version__"]
