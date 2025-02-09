import tkinter as tk
from .gui.main_gui import SlideMobGUI
from .pipelines.test_pipeline import TestPipeline
import os
import argparse
from .utils.config import create_config
from .utils.path_manager import PathManager
from .pipelines.run_merger_pipeline import PowerPointRunMerger
from openai import OpenAI
from .core_functions.base_class import PowerpointPipeline


# from slidemob.utils.errorhandler import setup_error_logging

# # Initialize error logging
# setup_error_logging()

def check_rate_limits():
    """Check OpenAI API rate limits by making a minimal API call."""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "hi"}]
        )
        
        # Access response headers through response._raw_response
        headers = response._raw_response.headers
        print("\nOpenAI Rate Limits:")
        print(f"Requests/min: {headers.get('x-ratelimit-limit-requests')}")
        print(f"Tokens/min: {headers.get('x-ratelimit-limit-tokens')}")
        print(f"Remaining Requests: {headers.get('x-ratelimit-remaining-requests')}")
        print(f"Remaining Tokens: {headers.get('x-ratelimit-remaining-tokens')}")
        print(f"Reset Timestamp: {headers.get('x-ratelimit-reset-tokens')}\n")
        
    except Exception as e:
        print(f"Error checking rate limits: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='SlideMob PowerPoint Translation Tool - Automatically translate your PowerPoint presentations',
        epilog='Without arguments, the GUI will be launched. However, to run without the GUI, you can use --testing | Example: python main.py --testing --input presentation.pptx --language French'
    )
    
    parser.add_argument(
        '--testing', 
        action='store_true',
        help='Run in testing mode instead of GUI mode'
    )
    parser.add_argument(
        '--input', 
        type=str,
        help='Path to the input PPTX file (default: uses test presentation if in testing mode)'
    )
    parser.add_argument(
        '--language', 
        type=str, 
        default='German',
        choices=['German', 'French', 'Spanish', 'Italian','English'],  # Add your supported languages
        help='Target language for translation (default: %(default)s)'
    )
    parser.add_argument(
        '--check-limits',
        action='store_true',
        help='Check OpenAI API rate limits'
    )
    args = parser.parse_args()

    if args.check_limits:
        check_rate_limits()
        return

    if args.testing:
        input_file = args.input if args.input else os.path.join(os.path.dirname(__file__), "Testpptx/CV_Jan_Werth_DE_2024-10-23.pptx")
        
        path_manager = PathManager(input_file)

        # Wite the args into the config file
        create_config(
            path_manager=path_manager,
            target_language=args.language
        )
        
        pipeline = TestPipeline(path_manager=path_manager, verbose=True)
        
        try:
            success = pipeline.run()
            if success:
                print("Translation completed successfully!")
            else:
                print("Translation failed!")
        except Exception as e:
            print(f"Error in pipeline: {str(e)}")

    else:
        #check_rate_limits()
        # GUI
        root = tk.Tk()
        app = SlideMobGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()