"""S11 / S12 / scope — unittest only.

仓库 CI 用 `python -m unittest discover`，**没有 pytest**。上一版引入了
pytest（`tmp_path` fixture），在 main 上直接让 "Run fixtures" 步骤 ImportError。
这里改为纯标准库 unittest，任何环境都能跑。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE.parent / "fixtures"
sys.path.insert(0, str(HERE.parent))
from iverify import independent_verify  # noqa: E402


def _run_cli(pkg):
    p = subprocess.run([sys.executable, str(HERE.parent / "ivcli.py"), str(pkg)],
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(p.stdout), p.returncode


class TestS11S12Scope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="uibc-iv-")
        self.clean = os.path.join(self.tmp, "clean.uibc")
        shutil.copytree(str(FIX / "clean.uibc"), self.clean)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _dupkey(self):
        pkg = os.path.join(self.tmp, "dupkey.uibc")
        shutil.copytree(str(FIX / "clean.uibc"), pkg)
        mf = os.path.join(pkg, "manifest.json")
        with open(mf, encoding="utf-8") as f:
            raw = f.read()
        self.assertTrue(raw.lstrip().startswith("{"))
        with open(mf, "w", encoding="utf-8") as f:
            f.write(raw.replace("{", '{"dup_probe": 1, "dup_probe": 2,', 1))
        return pkg

    def test_clean_fixture_passes_s11_and_s12(self):
        out, _ = _run_cli(self.clean)
        self.assertEqual(out["checks"]["V10"], "PASS")
        self.assertEqual(out["checks"]["V11"], "PASS")

    def test_duplicate_member_is_refused(self):
        out, rc = _run_cli(self._dupkey())
        self.assertEqual(out["checks"]["V10"], "FAIL")
        self.assertEqual(out["result"], "FAIL")
        self.assertEqual(rc, 1)

    def test_duplicate_member_differs_from_clean(self):
        self.assertEqual(independent_verify(self.clean)["checks"]["V10"], "PASS")
        self.assertEqual(independent_verify(self._dupkey())["checks"]["V10"], "FAIL")

    def test_future_timestamp_is_failed(self):
        pkg = os.path.join(self.tmp, "future.uibc")
        shutil.copytree(str(FIX / "clean.uibc"), pkg)
        lc = os.path.join(pkg, "lifecycle.json")
        with open(lc, encoding="utf-8") as f:
            doc = json.load(f)
        doc["events"][-1]["timestamp"] = "2099-01-01T00:00:00Z"
        with open(lc, "w", encoding="utf-8") as f:
            json.dump(doc, f)
        out = independent_verify(pkg)
        self.assertEqual(out["checks"]["V11"], "FAIL")
        self.assertTrue(any("future-timestamp" in p for p in out["timestampProblems"]))

    def test_past_timestamp_tolerated(self):
        out = independent_verify(self.clean)
        self.assertEqual(out["checks"]["V11"], "PASS")

    def test_pass_carries_scope(self):
        out = independent_verify(self.clean)
        if out["result"] == "PASS":
            self.assertTrue(out["scope"], "PASS 未带范围声明")
            self.assertTrue(out["scope"]["notEstablished"], "PASS 未声明未建立项")
            overlap = set(out["scope"]["established"]) & set(out["scope"]["notEstablished"])
            self.assertFalse(overlap)


if __name__ == "__main__":
    unittest.main(verbosity=2)
