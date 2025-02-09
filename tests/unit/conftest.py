import pytest
import os
import tempfile


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname


@pytest.fixture
def sample_pptx_path(temp_test_dir):
    """Create a dummy PPTX file path"""
    return os.path.join(temp_test_dir, "test.pptx")
