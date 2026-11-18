# uibc-iverify — a second, code-independent verifier

A standalone checker for UIBC evidence packages, written from the specification rather than
from the reference implementation: **zero imports from `uibc-core`**, different internal
structure and different check identifiers on purpose.

The point of a second implementation is narrow and testable: if two differently structured
implementations disagree on a package, the specification is ambiguous there. Agreement is a
determinism signal about the spec, nothing more.

## Run it

```bash
python ivcli.py fixtures/clean.uibc
python -m unittest discover -s tests -p "test_*.py" -v
```

Output is one JSON object — `implementer`, `result`, `checks`. Exit codes:
`0` PASS, `1` FAIL, `2` INCONCLUSIVE, `3` the package could not be read (a read failure is
not a verdict).

## What the fixtures show

| fixture | expected result | why |
|---|---|---|
| `clean.uibc` | `INCONCLUSIVE` | a seal is present but no key is supplied, so S6-equivalent cannot resolve |
| `tampered.uibc` | `FAIL` | one evidence byte changed; the content hash no longer matches |
| `malicious-keyswap.uibc` | `INCONCLUSIVE` | the attacker's seal verifies against the attacker's own key; only pinning the owner key catches it |

`INCONCLUSIVE` is a result, not a failure to compute: it means the check could not be
resolved with the material supplied.

## Scope of "independent" — read this before citing it

- **Code-independent**: no shared code with `uibc-core`, written from the spec text. The
  check identifiers are this repository's own (`V1`–`V9`; the reference names the same
  concepts `S1`–`S6`).
- **Not organisationally independent**: authored by the same maintainer as the reference
  implementation, sharing the same trust root. Agreement between the two therefore
  demonstrates specification determinism, not third-party assurance.
- **Known gap**: no published mapping from `V*` to `S*` check identifiers. Top-level
  verdicts are compared; per-check comparison across implementations is not yet possible
  from this repository alone. That gap is listed here rather than omitted.

This is not a conformance suite and not a security audit. It checks a package against the
evidence boundary the specification states; it does not claim the agent was correct, safe,
or wise, that the recorded inputs were true or complete, or that any real-world outcome
followed.

The verifier is read-only: it opens files and computes hashes, and writes nothing.

## Provenance

`iverify.py` is carried from the reference repository's `independent_verifier/` directory
and is maintained here so that it can be read, run and criticised without cloning the
implementation it is meant to check. Licence: Apache-2.0 (see `LICENSE`).
