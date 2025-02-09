import pytest
from slidemob.main import check_rate_limits, main
import os
from unittest.mock import patch, MagicMock

def test_check_rate_limits_no_api_key():
    """Test check_rate_limits when no API key is set"""
    with patch.dict(os.environ, {}, clear=True):
        check_rate_limits()  # Should handle missing API key gracefully

def test_main_parser():
    """Test argument parser in main"""
    with patch('argparse.ArgumentParser.parse_args') as mock_args:
        # Test --check-limits flag
        mock_args.return_value = MagicMock(
            check_limits=True,
            testing=False,
            input=None,
            language='German'
        )
        main()  # Should run without errors

def test_path_manager():
    """Test PathManager initialization"""
    from slidemob.utils.path_manager import PathManager
    test_input = "test.pptx"
    pm = PathManager(test_input)
    assert pm.input_file.endswith(test_input)
    assert "translated_test.pptx" in pm.output_pptx 