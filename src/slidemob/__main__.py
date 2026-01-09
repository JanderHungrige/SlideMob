#!/usr/bin/env python3
"""Entry point for the slidemob package."""
import argparse
import os
import sys
import tkinter as tk

from openai import OpenAI

from slidemob.gui.main_gui import SlideMobGUI
from slidemob.pipelines.test_pipeline import TestPipeline
from slidemob.utils.config import create_config
from slidemob.utils.path_manager import PathManager


def check_rate_limits():
    """Check OpenAI API rate limits by making a minimal API call."""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": "hi"}]
        )
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
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="SlideMob PowerPoint Processor")
    parser.add_argument("--testing", action="store_true", help="Run in test mode")
    parser.add_argument("--input", type=str, help="Input PPTX file")
    parser.add_argument(
        "--language", type=str, default="English", help="Target language"
    )
    args = parser.parse_args()

    if args.testing:
        input_file = (
            args.input
            if args.input
            else os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "Testpptx/CV_Jan_Werth_DE_2024-10-23.pptx",
            )
        )
        path_manager = PathManager(input_file)
        create_config(path_manager=path_manager, target_language=args.language)
        pipeline = TestPipeline(path_manager=path_manager, verbose=True)
        try:
            success = pipeline.run()
            if success:
                print("Translation completed successfully!")
            else:
                print("Translation failed!")
        except Exception as e:
            print(f"Error in pipeline: {e!s}")
    else:
        try:
            root = tk.Tk()
            app = SlideMobGUI(root)
            root.mainloop()
        except Exception as e:
            import traceback
            import sys
            # Attempt to show error in message box if GUI fails
            try:
                import tkinter.messagebox as mb
                mb.showerror("Application Error", f"The application failed to start:\n\n{e}\n\n{traceback.format_exc()}")
            except:
                print(f"Critical error: {e}", file=sys.stderr)
                print(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
