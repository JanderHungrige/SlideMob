import os
import pytest
from slidemob.utils.path_manager import PathManager


def test_path_manager():
    """Test PathManager initialization"""
    test_input = "test.pptx"
    pm = PathManager(test_input)

    # Test that input file path is correct
    assert pm.input_file.endswith(test_input)

    # Test that output file has correct prefix and suffix
    assert os.path.basename(pm.output_pptx).startswith("translated_")
    assert os.path.basename(pm.output_pptx).endswith(test_input)


def test_path_manager_with_output():
    """Test PathManager initialization with output file"""
    test_input = "test.pptx"
    test_output = "output.pptx"
    pm = PathManager(test_input, test_output)

    # Test that input file path is correct
    assert pm.input_file.endswith(test_input)

    # Test that output file has correct prefix and input filename
    assert os.path.basename(pm.output_pptx).startswith("translated_")
    assert os.path.basename(pm.output_pptx).endswith(
        test_input
    )  # Note: we expect input filename, not output filename


def test_ensure_directories(temp_test_dir):
    """Test directory creation"""
    test_input = os.path.join(temp_test_dir, "test.pptx")
    pm = PathManager(test_input)
    pm.ensure_directories()
    assert os.path.exists(pm.extracted_dir)
    assert os.path.exists(pm.output_dir)
