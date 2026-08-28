from pathlib import Path
import pytest
from pipeline import run


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_pipeline_on_generated_sample(tmp_path):
    data = ROOT / "data_test"
    if not data.exists():
        pytest.skip("Run generator at a small scale into data_test to enable integration test")
    db = run(data, tmp_path / "output")
    assert db.exists()

