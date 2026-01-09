import traceback

from ..core_functions.base_class import PowerpointPipeline
from ..core_functions.translator import SlideTranslator


class PowerPointTranslator:
    def __init__(self, progress_callback=None, stop_check_callback=None, pipeline_config: dict = None):
        self.progress_callback = progress_callback
        self.stop_check_callback = stop_check_callback
        self.pipeline_config = pipeline_config

    def translate_presentation(self):
        """Main method to handle the full translation process"""
        try:
            self.settings = PowerpointPipeline(pipeline_config=self.pipeline_config)
            self.translator = SlideTranslator(pipeline_settings=self.settings)

            # Extract PPTX if needed
            if self.settings.fresh_extract:
                self.settings.extract_pptx()

            # Get namespaces
            namespaces = self.settings.get_namespace()
            success = self.translator.process_slides(
                self.progress_callback, self.stop_check_callback
            )
            if not success:
                return False

            # Compose final PPTX
            self.settings.compose_pptx(
                self.settings.extract_path, self.settings.output_pptx
            )
            return True

        except Exception as e:
            import sys
            import traceback
            print(f"Error translating presentation: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            return False
