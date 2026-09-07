"""
Wraps the pre-existing scripts/test_*.py end-to-end scripts as real
pytest tests, so `pytest` from backend/ is a single command that
exercises this codebase's FULL prior coverage (gesture recognition,
adaptive learning, feedback, recommendations, learning analytics,
instructor assignments, etc.) alongside the newly-authored idiomatic
tests in this directory — not a replacement for them.

These scripts were written before this test suite existed, each as a
standalone script with its own PASS/FAIL counter (see any of them for
the pattern) rather than pytest test functions with assert statements.
Rewriting fifteen of them into fully idiomatic pytest was judged not
worth the risk of introducing a transcription bug into working,
already-battle-tested checks — wrapping them as subprocesses instead
preserves their exact existing behavior byte-for-byte while still
making them real, CI-runnable pytest failures (a non-zero exit fails
the test, and stdout/stderr are attached to the failure for debugging).
Each script already calls Base.metadata.create_all(bind=engine) and
manages its own seed data (get-or-create by email, delete-then-reseed),
so no fixture from conftest.py is needed here beyond the DATABASE_URL
isolation conftest.py already set up before this module was imported.

scripts/_smoketest_msasl.py is deliberately excluded — its own
docstring calls it a "THROWAWAY smoke test, not part of the real
pipeline."
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BACKEND_ROOT / "scripts"

LEGACY_SCRIPTS = sorted(
    p.name for p in SCRIPTS_DIR.glob("test_*.py") if p.name != "_smoketest_msasl.py"
)

# These three read real JPEGs out of data/asl_alphabet/asl_alphabet_test/
# — a large raw image dataset that, like the MS-ASL video clips
# elsewhere in this project, isn't checked into git and isn't present in
# every environment this suite might run in (it wasn't present in the
# cloud sandbox this suite was authored in). Skipped rather than failed
# when that directory is missing, since a missing dataset is an
# environment fact, not a code defect — on a machine that has the real
# dataset (e.g. the project's own dev machine), these run for real.
DATASET_DEPENDENT_SCRIPTS = {"test_gesture_recognition.py", "test_hand_tracking.py", "test_sign_assessment.py"}
ASL_ALPHABET_TEST_DIR = BACKEND_ROOT / "data" / "asl_alphabet" / "asl_alphabet_test"


@pytest.mark.parametrize("script_name", LEGACY_SCRIPTS)
def test_legacy_script(script_name):
    if script_name in DATASET_DEPENDENT_SCRIPTS and not ASL_ALPHABET_TEST_DIR.exists():
        pytest.skip(f"data/asl_alphabet/asl_alphabet_test/ not present in this environment — needed by {script_name}")

    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name)],
        cwd=str(BACKEND_ROOT),
        env=os.environ,  # carries the DATABASE_URL conftest.py already set
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"{script_name} exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout[-4000:]}\n"
        f"--- stderr ---\n{result.stderr[-4000:]}"
    )
