"""S11 重复键与 S12 未来时间戳：可被 pytest 收集的断言版。

上一版是 `def main()` 的脚本，`pytest` 收集 0 条——等于没测。这里改成
`test_*` 函数并在同一进程里断言，避免"跑了一遍但没人读结果"。
"""
import json
import pathlib
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
FIX = HERE / "fixtures"
sys.path.insert(0, str(HERE))
from iverify import independent_verify  # noqa: E402


def _run(pkg):
    p = subprocess.run([sys.executable, str(HERE / "ivcli.py"), str(pkg)],
                       capture_output=True, text=True, encoding="utf-8")
    return json.loads(p.stdout), p.returncode


def _dupkey_copy(dst):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(FIX / "clean.uibc", dst)
    mf = dst / "manifest.json"
    raw = mf.read_text(encoding="utf-8")
    assert raw.lstrip().startswith("{")
    mf.write_text(raw.replace("{", '{"dup_probe": 1, "dup_probe": 2,', 1), encoding="utf-8")


def test_clean_fixture_is_not_refused(tmp_path):
    pkg = tmp_path / "clean.uibc"
    shutil.copytree(FIX / "clean.uibc", pkg)
    out, rc = _run(pkg)
    assert out["checks"]["V10"] == "PASS"
    assert out["checks"]["V11"] == "PASS"


def test_duplicate_member_is_refused(tmp_path):
    pkg = tmp_path / "dupkey.uibc"
    _dupkey_copy(pkg)
    out, rc = _run(pkg)
    assert out["checks"]["V10"] == "FAIL", out
    assert out["result"] == "FAIL"
    assert rc == 1


def test_duplicate_member_changes_verdict_vs_clean(tmp_path):
    clean = tmp_path / "clean.uibc"
    dup = tmp_path / "dup.uibc"
    shutil.copytree(FIX / "clean.uibc", clean)
    _dupkey_copy(dup)
    assert independent_verify(str(clean))["checks"]["V10"] == "PASS"
    assert independent_verify(str(dup))["checks"]["V10"] == "FAIL"


def test_future_timestamp_is_failed(tmp_path):
    pkg = tmp_path / "future.uibc"
    shutil.copytree(FIX / "clean.uibc", pkg)
    lc = pkg / "lifecycle.json"
    doc = json.loads(lc.read_text(encoding="utf-8"))
    doc["events"][-1]["timestamp"] = "2099-01-01T00:00:00Z"
    lc.write_text(json.dumps(doc), encoding="utf-8")
    out = independent_verify(str(pkg))
    assert out["checks"]["V11"] == "FAIL"
    assert any("future-timestamp" in p for p in out["timestampProblems"])


def test_past_timestamp_tolerated(tmp_path):
    pkg = tmp_path / "past.uibc"
    shutil.copytree(FIX / "clean.uibc", pkg)
    out = independent_verify(str(pkg))
    assert out["checks"]["V11"] == "PASS"


def test_pass_carries_scope(tmp_path):
    """凡是 PASS 都必须带 established/notEstablished；带不了就不许白给 PASS。"""
    pkg = tmp_path / "clean.uibc"
    shutil.copytree(FIX / "clean.uibc", pkg)
    out = independent_verify(str(pkg))
    if out["result"] == "PASS":
        assert out["scope"], "PASS 未带范围声明"
        assert out["scope"]["notEstablished"], "PASS 未声明未建立的项"
        overlap = set(out["scope"]["established"]) & set(out["scope"]["notEstablished"])
        assert not overlap, overlap
