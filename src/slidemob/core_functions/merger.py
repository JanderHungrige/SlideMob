from lxml import etree as ET
from .base_class import PowerpointPipeline
import os
import traceback

class RunMerger:
    def __init__(self, namespaces):
        self.namespaces = namespaces

    def merge_runs(self, paragraph):
        """Merge neighboring runs in a paragraph if they have the same parameters."""
        runs = paragraph.findall('.//w:r', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
        i = 0
        while i < len(runs) - 1:
            current_run = runs[i]
            next_run = runs[i + 1]

            # Check if runs can be merged (have same properties)
            if self.runs_are_similar(current_run, next_run):
                # Get the text content
                current_text = current_run.findtext('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}) or ''
                next_text = next_run.findtext('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}) or ''
                
                # Update text of current run
                text_element = current_run.find('.//w:t', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
                if text_element is not None:
                    text_element.text = current_text + next_text
                
                # Remove the next run from its actual parent
                next_run_parent = next_run.getparent()
                if next_run_parent is not None:
                    next_run_parent.remove(next_run)
                
                # Don't increment i since we removed a run
                runs = paragraph.findall('.//w:r', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
            else:
                i += 1

    def runs_are_similar(self, run1, run2):
        """Check if two runs are mergeable based on their parameters."""
        # Compare text properties
        props1 = run1.find('w:rPr', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
        props2 = run2.find('w:rPr', namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
        
        if props1 is None or props2 is None:
            return False
        
        # Compare relevant attributes
        attrs_to_compare = ['lang', 'sz', 'b', 'i', 'u']
        return all(props1.get(attr) == props2.get(attr) for attr in attrs_to_compare)

    def process_paragraphs(self, root):
        """Process all paragraphs in the XML tree."""
        paragraphs = root.findall('.//a:p', self.namespaces)
        for paragraph in paragraphs:
            self.merge_runs(paragraph)

class SlideRunMerger(PowerpointPipeline):
    def __init__(self):
        super().__init__()
        self.merger = None  # Will be initialized after namespace detection

    def process_slides(self, folder_path: str):
        """Process all slides in the presentation to merge runs."""
        try:
            slide_files = self.find_slide_files(folder_path)
            
            for slide_file in sorted(slide_files):
                print(f"\nProcessing {os.path.basename(slide_file)}...")
                print(f"Processing slide {slide_files.index(slide_file) + 1} of {len(slide_files)}...")
                
                # Parse XML while preserving structure
                tree = ET.parse(slide_file)
                root = tree.getroot()
                
                # Extract namespaces from the root element
                namespaces = {}
                for key, value in root.attrib.items():
                    if key.startswith('xmlns:'):
                        prefix = key.split(':')[1]
                        namespaces[prefix] = value
                
                # Initialize merger with namespaces if not already done
                if self.merger is None:
                    self.merger = RunMerger(self.namespaces)
                
                # Process the slides
                self.merger.process_paragraphs(root)
                
                # Register namespaces
                for prefix, uri in namespaces.items():
                    ET.register_namespace(prefix, uri)
                for prefix, uri in self.namespaces.items():
                    ET.register_namespace(prefix, uri)
                
                # Write back XML
                with open(slide_file, 'wb') as f:
                    tree.write(f, encoding='UTF-8', xml_declaration=True)
                    
        except Exception as e:
            print(f"Error processing slides: {e}")
            print("Full traceback:")
            print(traceback.format_exc())