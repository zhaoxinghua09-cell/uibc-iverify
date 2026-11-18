import json, os, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLI = os.path.join(ROOT, "ivcli.py")
FIX = os.path.join(ROOT, "fixtures")


def run(pkg):
    p = subprocess.run([sys.executable, CLI, pkg], capture_output=True, text=True, encoding="utf-8")
    out = json.loads(p.stdout) if p.stdout.strip() else {}
    return p.returncode, out


class Fixtures(unittest.TestCase):
    def test_clean_is_inconclusive_without_a_key(self):
        # A seal is present but no key is supplied, so S6 cannot resolve.
        # INCONCLUSIVE is the correct verdict here, not PASS.
        code, out = run(os.path.join(FIX, "clean.uibc"))
        self.assertEqual(out.get("result"), "INCONCLUSIVE")
        self.assertEqual(code, 2)

    def test_tampered_fails_on_content_hash(self):
        code, out = run(os.path.join(FIX, "tampered.uibc"))
        self.assertEqual(out.get("result"), "FAIL")
        self.assertEqual(code, 1)
        # V4 is this implementation's content-hash check; the reference names
        # the same check S4. The two are expected to agree, not to be identical.
        self.assertEqual(out["checks"].get("V4"), "FAIL")

    def test_keyswap_inconclusive_without_pinning(self):
        # Key substitution cannot be detected without the owner key: the
        # attacker's seal verifies against the attacker's own key.
        code, out = run(os.path.join(FIX, "malicious-keyswap.uibc"))
        self.assertEqual(out.get("result"), "INCONCLUSIVE")
        self.assertEqual(code, 2)

    def test_unreadable_path_is_not_a_verdict(self):
        code, out = run(os.path.join(FIX, "does-not-exist"))
        self.assertEqual(code, 3)
        self.assertEqual(out, {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
