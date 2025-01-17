import os
import json
import dotenv
from openai import OpenAI
from typing import List, Tuple
import xml.etree.ElementTree as ET
from utils.path_manager import PathManager, get_initial_config_path
import zipfile
dotenv.load_dotenv()
import traceback


class PowerpointPipeline:
    def __init__(self, 
                 model: str="gpt-4o", 
                 pydentic_model: str="gpt-4-turbo-preview",
                 translation_client:str="OpenAI", 
                 mapping_client:str="HuggingFace",
                 verbose: bool=False,
                 extract_namespaces: bool=False,
                 namespaces: dict={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
                                   'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
                                   'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
                                   'p14':"http://schemas.microsoft.com/office/powerpoint/2010/main",
                                   'a16':"http://schemas.microsoft.com/office/drawing/2014/main",
                                   'mc':"http://schemas.openxmlformats.org/markup-compatibility/2006",
                                   'v':"urn:schemas-microsoft-com:vml"
                                   },
                 ):
        #load config file
        with open(get_initial_config_path(), "r") as f:
            self.config = json.load(f)

        self.root_folder = self.config["root_folder"]
        self.pptx_folder = self.config["pptx_folder"]
        self.pptx_path = self.config["pptx_name"]
        self.extract_path = self.config["extract_folder"]
        self.output_folder = self.config["output_folder"]
        self.output_pptx = self.config["output_pptx"]
        self.target_language = self.config["target_language"]
     
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.huggingface_api_key = os.getenv("HUGGINGFACE")
        self.model = model
        self.pydentic_model=pydentic_model
        self.translation_client = translation_client
        self.mapping_client = mapping_client
        self.extract_namespaces = extract_namespaces
        self.namespaces =namespaces 

        self.paths = PathManager(input_file=self.pptx_path) #overall msanaged paths

        if verbose: print(f"\tPPTX path: {self.pptx_path}")
        if verbose: print(f"\tExtract path: {self.extract_path}")
        if verbose: print(f"\tOutput folder: {self.output_folder}")


        if self.translation_client == "OpenAI":
            self.translation_client = OpenAI(api_key=self.openai_api_key)
        elif self.translation_client == "HuggingFace":
            self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-13b-chat-hf"
            self.huggingface_headers = {"Authorization": "Bearer " + self.huggingface_api_key}
        else:
            print("\tClient not supported for translation(So far only OpenAI and HuggingFace are supported)")
        pass

        if self.mapping_client == "OpenAI":
            self.mapping_client = OpenAI(api_key=self.openai_api_key)
        elif self.mapping_client == "HuggingFace":
            self.HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-2-13b-chat-hf"
            self.huggingface_headers = {"Authorization": "Bearer " + self.huggingface_api_key}
        else:
            print("\tClient not supported for mapping(So far only HuggingFace is supported)")
      
    def find_slide_files(self, root_folder: str) -> List[str]:
        """Find all slide XML files in the folder structure."""
        slide_files = []
        for root, _, files in os.walk(root_folder):
            for file in files:
                if file.startswith('slide') and file.endswith('.xml'):
                    number_part = file[5:-4]
                    if number_part.isdigit():
                        slide_files.append(os.path.join(root, file))
        return sorted(slide_files)
        

    def extract_paragraphs(self, xml_file: str) -> List[ET.Element]:
        """Extract everything inparagraphs from the XML file."""
        tree = ET.parse(xml_file)
        root = tree.getroot()
        return root.findall('.//a:p', self.namespaces)

    def extract_text_runs(self, xml_file: str) -> Tuple[List[ET.Element], set]:
        """Extract text elements that need translation."""
        tree = ET.parse(xml_file)
        root = tree.getroot()
        text_elements = []
        original_text_elements = set()
  
        # Create a backup with the original text elements
        for paragraph in root.findall('.//a:p', self.namespaces):
            for run in paragraph.findall('.//a:r', self.namespaces):
                run_props = run.find('.//a:rPr', self.namespaces)
                lang = run_props.get('lang') if run_props is not None else 'en-GB' 

                for original_text_element in run.findall('.//a:t', self.namespaces):
                    if original_text_element.text and original_text_element.text.strip():
                        original_text_elements.add(original_text_element.text.strip())

        # Process paragraphs while preserving structure
        for paragraph in root.findall('.//a:p', self.namespaces):
            text_parts = []
            lang = None
            for text_element in paragraph.findall('.//a:t', self.namespaces):
                run_props = text_element.find('.//a:rPr', self.namespaces)
                if run_props is not None:
                    lang = run_props.get('lang', 'en-GB')
                if text_element.text and text_element.text.strip():
                    text_parts.append(text_element.text.strip())
            
            if text_parts:
                text_element = ET.Element('a:t')
                text_element.text = ' '.join(text_parts)
                text_element.set('lang', lang or 'en-GB')
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
        
        with zipfile.ZipFile(self.pptx_path, 'r') as pptx:
            pptx.extractall(self.extract_path)
        
        # Get namespaces right after extraction
        if self.extract_namespaces:
            self.namespaces = self.get_namespace()
        return self.extract_path

    def get_namespace(self) -> dict:
        """Get the namespaces from the first slide XML using text processing."""
        slide_path = os.path.join(self.extract_path, 'ppt/slides/slide1.xml')
        
        try:
            with open(slide_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            # Find the root element opening tag
            start_idx = content.find('<p:sld')
            end_idx = content.find('>', start_idx)
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
                    namespaces['default'] = uri
            
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
            with zipfile.ZipFile(output_pptx, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
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