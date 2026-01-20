import json
import os
import traceback
import xml.etree.ElementTree as ET
import zipfile

from ..utils.model_settings import ModelSettings
from ..utils.path_manager import PathManager, get_resource_path


class PowerpointPipeline:
    def __init__(
        self,
        verbose: bool = False,
        extract_namespaces: bool = False,
        pipeline_config: dict = None,
        namespaces: dict = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
            "p14": "http://schemas.microsoft.com/office/powerpoint/2010/main",
            "a16": "http://schemas.microsoft.com/office/drawing/2014/main",
            "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
            "v": "urn:schemas-microsoft-com:vml",
        },
    ):

        self.verbose = verbose
        self.extract_namespaces = extract_namespaces
        self.namespaces = namespaces
        self.pipeline_config = pipeline_config
        self.get_config()

    def get_config(self):
        if self.pipeline_config:
            self.config = self.pipeline_config
        else:
            # Load config file from packaged resource if no runtime config provided
            config_path = get_resource_path("slidemob/config.json")
            with open(config_path) as f:
                self.config = json.load(f)

        self.root_folder = self.config["root_folder"]
        self.pptx_folder = self.config["pptx_folder"]
        self.pptx_path = self.config["pptx_name"]
        self.extract_path = self.config["extract_folder"]
        self.output_folder = self.config["output_folder"]
        self.output_pptx = self.config["output_pptx"]
        self.target_language = self.config["target_language"]

        self.extract_namespaces = self.extract_namespaces
        self.namespaces = self.namespaces
        # Initialize model settings
        model_settings = ModelSettings()
        # Load GUI config
        self.reduce_slides = model_settings.reduce_slides
        self.update_language = model_settings.update_language
        self.fresh_extract = model_settings.fresh_extract
        self.translation_strategy = model_settings.translation_strategy

        # Copy relevant attributes from model settings
        self.translation_client = model_settings.translation_client
        self.mapping_client = model_settings.mapping_client
        self.translation_model = model_settings.translation_model
        self.mapping_model = model_settings.mapping_model
        self.translation_method = model_settings.translation_method
        self.mapping_method = model_settings.mapping_method
        self.translation_api_url = model_settings.translation_api_url
        self.mapping_api_url = model_settings.mapping_api_url
        self.translation_headers = model_settings.translation_headers
        self.mapping_headers = model_settings.mapping_headers
        self.style_instructions = model_settings.style_instructions

        # load reasoning model list from reasoning_model_list.json
        reasoning_model_list_path = get_resource_path("slidemob/utils/reasoning_model_list.json")
        with open(reasoning_model_list_path) as f:
            self.reasoning_model_list = json.load(f)

        if self.translation_model in self.reasoning_model_list:
            self.translation_reasoning_model = True
        else:
            self.translation_reasoning_model = False

        if self.mapping_model in self.reasoning_model_list:
            self.mapping_reasoning_model = True
        else:
            self.mapping_reasoning_model = False

        self.paths = PathManager(input_file=self.pptx_path)  # overall msanaged paths

        if self.verbose:
            print(f"\tPPTX path: {self.pptx_path}")
        if self.verbose:
            print(f"\tExtract path: {self.extract_path}")
        if self.verbose:
            print(f"\tOutput folder: {self.output_folder}")

    @staticmethod
    def parse_slide_selection(selection_str: str) -> set[int]:
        """Parse a slide selection string (e.g., '1,3,5-7,12') into a set of slide numbers."""
        if not selection_str or not selection_str.strip():
            return set()
            
        selected_slides = set()
        parts = selection_str.replace(" ", "").split(",")
        
        for part in parts:
            if "-" in part:
                try:
                    start, end = map(int, part.split("-"))
                    selected_slides.update(range(start, end + 1))
                except ValueError:
                    continue
            else:
                try:
                    selected_slides.add(int(part))
                except ValueError:
                    continue
                    
        return selected_slides

    def find_slide_files(self) -> list[str]:
        """Find all slide XML files in the folder structure, filtered by selected slides if applicable."""
        slide_files = []
        
        # Get selected slides from config if they exist
        selection_str = self.config.get("selected_slides", "")
        selected_slides = self.parse_slide_selection(selection_str)
        
        for root, _, files in os.walk(self.extract_path):
            for file in files:
                if file.startswith("slide") and file.endswith(".xml"):
                    number_part = file[5:-4]
                    if number_part.isdigit():
                        slide_num = int(number_part)
                        if not selected_slides or slide_num in selected_slides:
                            slide_files.append(os.path.join(root, file))
        
        # Verify if all selected slides exist
        if selected_slides:
            all_slide_nums = set()
            for root, _, files in os.walk(self.extract_path):
                for file in files:
                    if file.startswith("slide") and file.endswith(".xml"):
                        num = file[5:-4]
                        if num.isdigit():
                            all_slide_nums.add(int(num))
            
            missing_slides = selected_slides - all_slide_nums
            if missing_slides:
                print(f"Warning: The following selected slides do not exist: {sorted(list(missing_slides))}")

        return sorted(slide_files)

    def extract_paragraphs(self, xml_file: str) -> list[ET.Element]:
        """Extract everything inparagraphs from the XML file."""
        tree = ET.parse(xml_file)
        root = tree.getroot()
        return root.findall(".//a:p", self.namespaces)

    def extract_text_runs(self, xml_file: str) -> tuple[list[ET.Element], set]:
        """Extract text elements that need translation."""
        tree = ET.parse(xml_file)
        root = tree.getroot()
        text_elements = []
        original_text_elements = set()

        # Create a backup with the original text elements
        for paragraph in root.findall(".//a:p", self.namespaces):
            for run in paragraph.findall(".//a:r", self.namespaces):
                run_props = run.find(".//a:rPr", self.namespaces)
                lang = run_props.get("lang") if run_props is not None else "en-GB"

                for original_text_element in run.findall(".//a:t", self.namespaces):
                    if (
                        original_text_element.text
                        and original_text_element.text.strip()
                    ):
                        original_text_elements.add(original_text_element.text.strip())

        # Process paragraphs while preserving structure
        for paragraph in root.findall(".//a:p", self.namespaces):
            text_parts = []
            lang = None
            for text_element in paragraph.findall(".//a:t", self.namespaces):
                run_props = text_element.find(".//a:rPr", self.namespaces)
                if run_props is not None:
                    lang = run_props.get("lang", "en-GB")
                if text_element.text and text_element.text.strip():
                    text_parts.append(text_element.text.strip())

            if text_parts:
                text_element = ET.Element("a:t")
                text_element.text = " ".join(text_parts)
                text_element.set("lang", lang or "en-GB")
                text_elements.append(text_element)

        print("Text elements found:")
        for element in text_elements:
            print(f"- {element.text.strip()} | lang: {element.get('lang')}")
        return text_elements, original_text_elements

    def extract_pptx(self) -> str:
        """Extract a PPTX file into its XML components."""
        os.makedirs(self.extract_path, exist_ok=True)

        # Clear the extract folder if it's not empty
        if os.path.exists(self.extract_path) and os.listdir(self.extract_path):
            for item in os.listdir(self.extract_path):
                item_path = os.path.join(self.extract_path, item)
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    import shutil

                    shutil.rmtree(item_path)

        with zipfile.ZipFile(self.pptx_path, "r") as pptx:
            pptx.extractall(self.extract_path)

        # Get namespaces right after extraction
        if self.extract_namespaces:
            self.namespaces = self.get_namespace()
        return self.extract_path

    def get_namespace(self) -> dict:
        """Get the namespaces from the first slide XML using text processing."""
        slide_path = os.path.join(self.extract_path, "ppt/slides/slide1.xml")

        try:
            with open(slide_path, encoding="utf-8") as file:
                content = file.read()

            # Find the root element opening tag
            start_idx = content.find("<p:sld")
            end_idx = content.find(">", start_idx)
            if start_idx == -1 or end_idx == -1:
                print("Could not find root element")
                return {}

            # Extract the root element declaration
            root_declaration = content[start_idx:end_idx]

            # Find all xmlns declarations
            namespaces = {}
            import re

            # Pattern to match xmlns:prefix="uri" or xmlns="uri"
            pattern = r'xmlns(?::([^=]+))?="([^"]+)"'
            matches = re.finditer(pattern, root_declaration)

            for match in matches:
                prefix = match.group(1)  # This might be None for default namespace
                uri = match.group(2)
                if prefix:
                    namespaces[prefix] = uri
                else:
                    namespaces["default"] = uri

            print("\tExtracted namespaces:", namespaces)
            return namespaces

        except Exception as e:
            print(f"\tError extracting namespaces: {e}")
            return {}

    def compose_pptx(self, source_path: str, output_pptx: str):
        """Compose a PPTX file from a directory containing the XML structure."""
        self.extract_path

        os.makedirs(os.path.dirname(self.output_pptx), exist_ok=True)
        try:
            with zipfile.ZipFile(
                output_pptx, "w", compression=zipfile.ZIP_DEFLATED
            ) as zf:
                for root, _, files in os.walk(source_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_path)
                        zf.write(file_path, arcname)
        except Exception as e:
            print(f"Error composing PPTX: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return False
        return True
