#!/usr/bin/env python3
"""Fail if any requirement in requirements.txt has no upper bound.

Why: Render builds with no cache and installs the newest version that matches each
specifier. In Session 9 an unbounded `SQLAlchemy>=2.0` pulled 2.1, which switched
postgresql:// to the psycopg (v3) driver and broke the deploy. Every dependency
needs a ceiling (`<N`, `==`, `~=`) so a new major can't land without a PR.
"""
import pathlib
import re
import sys

REQ = pathlib.Path(__file__).resolve().parent.parent / "requirements.txt"
UPPER = re.compile(r"(<|==|~=)")


def main() -> int:
    bad = []
    for n, raw in enumerate(REQ.read_text().splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("-"):
            # -r/-c includes would hide unbounded deps from this check
            bad.append(f"  requirements.txt:{n}: {line}  (includes not supported; inline them)")
            continue
        spec = line.split(";", 1)[0]  # ignore environment markers like python_version < "3.14"
        if not UPPER.search(spec):
            bad.append(f"  requirements.txt:{n}: {line}")
    if bad:
        print("Requirements without an upper bound (add `,<NEXT_MAJOR`):")
        print("\n".join(bad))
        return 1
    print("requirements: all pinned with an upper bound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
