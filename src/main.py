import tkinter as tk
from slidemob.gui.main_gui import SlideMobGUI
from slidemob.pipelines.test_pipeline import TestPipeline
import os
import argparse  # Add this import
from slidemob.utils.config import create_config
from slidemob.utils.path_manager import PathManager
from slidemob.pipelines.run_merger_pipeline import PowerPointRunMerger


# from slidemob.utils.errorhandler import setup_error_logging

# # Initialize error logging
# setup_error_logging()

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
    args = parser.parse_args()


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
        # GUI
        root = tk.Tk()
        app = SlideMobGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()