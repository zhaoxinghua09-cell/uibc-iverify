#!/usr/bin/env python3
"""CLI for the independent verifier.

    python ivcli.py <package-dir>

Prints one JSON object (implementer, result, checks) and exits:
  0 PASS  1 FAIL  2 INCONCLUSIVE  3 could not read the package
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iverify import independent_verify  # noqa: E402

EXIT = {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}


def main() -> int:
    if len(sys.argv) != 2:
        sys.stderr.write(__doc__)
        return 3
    pkg = sys.argv[1]
    if not os.path.isdir(pkg):
        sys.stderr.write("not a directory: %s\n" % pkg)
        return 3
    try:
        out = independent_verify(pkg)
    except Exception as exc:  # a package that cannot be read is not a FAIL verdict
        sys.stderr.write("unreadable: %s\n" % exc)
        return 3
    print(json.dumps(out, indent=1, sort_keys=False))
    return EXIT.get(out.get("result"), 3)


if __name__ == "__main__":
    raise SystemExit(main())
