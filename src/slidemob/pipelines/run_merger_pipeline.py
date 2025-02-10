import os
import traceback

from lxml import etree as ET

from ..core_functions.base_class import PowerpointPipeline
from ..core_functions.merger import RunMerger


class PowerPointRunMerger(PowerpointPipeline):
    def __init__(self, fresh_extract: bool = True):
        super().__init__()

        self.fresh_extract = fresh_extract
        self.merger = None  # Will be initialized after namespace detection

    def merge_runs_in_presentation(self):
        """Main method to handle the run merging process"""
        try:
            # Extract PPTX if needed
            if self.fresh_extract:
                self.extract_pptx()

            # Get namespaces
            namespaces = self.get_namespace()
            self.merger = RunMerger(namespaces)

            # Process slides
            slide_files = self.find_slide_files(self.extract_path)

            for slide_file in sorted(slide_files):
                print(f"\nProcessing {os.path.basename(slide_file)}...")
                tree = ET.parse(slide_file)
                root = tree.getroot()

                # Process all paragraphs in the slide
                self.merger.process_paragraphs(root)

                # Write back XML
                with open(slide_file, "wb") as f:
                    tree.write(f, encoding="UTF-8", xml_declaration=True)

            # Compose final PPTX
            self.compose_pptx(self.extract_path, self.output_pptx)
            return True

        except Exception as e:
            print(f"Error merging runs in presentation: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
