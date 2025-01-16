from pathlib import Path
from ..core.base_class import PowerpointPipeline
from .translator_pipeline import PowerPointTranslator
from .polisher_pipeline import PowerPointPolisher
from ..utils.path_manager import PathManager
from .run_merger_pipeline import PowerPointRunMerger
import traceback

class TestPipeline(PowerpointPipeline):
    def __init__(self, path_manager: PathManager, verbose: bool=False):
        super().__init__()

        # Initialize components
        self.translator = PowerPointTranslator(target_language=self.target_language, Further_StyleInstructions="None", update_language=False, fresh_extract=True, verbose=verbose)
        self.polisher = PowerPointPolisher()
        self.verbose = verbose
        self.paths = path_manager
        self.run_merger = PowerPointRunMerger()

    def run(self) -> bool:
        try:
            if self.verbose:
                print(f"Starting translation pipeline for: {self.paths.input_file}")
                print(f"Target language: {self.target_language}")

            # # Extract PPTX
            # if self.verbose:
            #     print("\nExtracting PPTX...")
            # self.extract_pptx()

            if self.verbose:
                print("\nMerging similar runs...")
            success = self.run_merger.merge_runs_in_presentation()
            if not success:
                return False

            if self.verbose:
                print("\nTranslating slides...")
            success = self.translator.translate_presentation()

            if self.verbose and success:
                print(f"\nTranslation complete! Output saved to: {self.output_folder}")
            return success

        except Exception as e:
            print(f"Error in pipeline: {str(e)}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
