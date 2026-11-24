#!/usr/bin/env python3
"""CLI for the independent verifier.

    python ivcli.py PACKAGE-DIR [--key HEX]

PATCH: --key supplies the owner key (hex) so HMAC seals can resolve; without
it a symmetric seal stays INCONCLUSIVE. Ed25519 seals are publicly verifiable
and need no key. Original CLI had no key option, so HMAC-sealed packages could
never reach PASS.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iverify import independent_verify  # noqa: E402

EXIT = {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}


def main() -> int:
    args = list(sys.argv[1:])
    key = None
    if "--key" in args:
        i = args.index("--key")
        try:
            key = bytes.fromhex(args[i + 1])
        except Exception:
            sys.stderr.write("--key must be hex\n")
            return 3
        del args[i:i + 2]
    if len(args) != 1:
        sys.stderr.write(__doc__)
        return 3
    pkg = args[0]
    if not os.path.isdir(pkg):
        sys.stderr.write("not a directory: %s\n" % pkg)
        return 3
    try:
        out = independent_verify(pkg, key=key)
    except Exception as exc:  # a package that cannot be read is not a FAIL verdict
        sys.stderr.write("unreadable: %s\n" % exc)
        return 3
    print(json.dumps(out, indent=1, sort_keys=False))
    return EXIT.get(out.get("result"), 3)


if __name__ == "__main__":
    raise SystemExit(main())
