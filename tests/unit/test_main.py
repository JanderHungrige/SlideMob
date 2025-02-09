import pytest
from slidemob.main import check_rate_limits, main
import os
from unittest.mock import patch, MagicMock
import tkinter as tk


def test_check_rate_limits_no_api_key():
    """Test check_rate_limits when no API key is set"""
    with patch.dict(os.environ, {}, clear=True):
        check_rate_limits()  # Should handle missing API key gracefully


def test_main_testing_mode():
    """Test main function in testing mode"""
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(testing=True, input=None, language="German")
        main()  # Should run without errors


@pytest.mark.skip(reason="GUI tests need special handling")
def test_main_gui_mode():
    """Test main function in GUI mode"""
    with patch("argparse.ArgumentParser.parse_args") as mock_args:
        mock_args.return_value = MagicMock(
            testing=False, input=None, language="English"
        )
        root = tk.Tk()  # Create root window first
        try:
            main()
        finally:
            root.destroy()  # Clean up


def test_path_manager():
    """Test PathManager initialization"""
    from slidemob.utils.path_manager import PathManager

    test_input = "test.pptx"
    pm = PathManager(test_input)
    assert pm.input_file.endswith(test_input)
    assert "translated_test.pptx" in pm.output_pptx
