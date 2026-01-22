import traceback

from ..core_functions.base_class import PowerpointPipeline
from ..core_functions.translator import SlideTranslator


class PowerPointTranslator:
    def __init__(self, progress_callback=None, stop_check_callback=None, log_callback=None, pipeline_config: dict = None):
        self.progress_callback = progress_callback
        self.stop_check_callback = stop_check_callback
        self.log_callback = log_callback
        self.pipeline_config = pipeline_config

    def translate_presentation(self):
        """Main method to handle the full translation process"""
        try:
            # Debug: Verify pipeline_config contains target_language
            if self.pipeline_config:
                target_lang = self.pipeline_config.get("target_language", "NOT SET")
                print(f"\n[DEBUG] PowerPointTranslator received pipeline_config with target_language: '{target_lang}'")
            else:
                print(f"\n[WARNING] PowerPointTranslator received None pipeline_config!")
            
            self.settings = PowerpointPipeline(pipeline_config=self.pipeline_config)
            
            # Debug: Verify settings has correct target_language
            print(f"[DEBUG] PowerpointPipeline.settings.target_language: '{self.settings.target_language}'")
            
            self.translator = SlideTranslator(pipeline_settings=self.settings)

            # Extract PPTX if needed
            if self.settings.fresh_extract:
                self.settings.extract_pptx()

            # Get namespaces
            namespaces = self.settings.get_namespace()
            success = self.translator.process_slides(
                self.progress_callback, self.stop_check_callback, self.log_callback
            )
            if not success:
                return False

            # Compose final PPTX
            compose_success = self.settings.compose_pptx(
                self.settings.extract_path, self.settings.output_pptx
            )
            if not compose_success:
                print("Warning: Failed to compose final PPTX file")
                return False
            return True

        except Exception as e:
            import sys
            import traceback
            print(f"Error translating presentation: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            return False
