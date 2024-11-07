import os
import json
import dotenv
from openai import OpenAI
from typing import List, Tuple
import xml.etree.ElementTree as ET
dotenv.load_dotenv()

class PowerpointPipeline:
    def __init__(self, 
                 model: str="gpt-4", 
                 pydentic_model: str="gpt-4-turbo-preview", 
                 client:str="OpenAI", 
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
        with open("config.json", "r") as f:
            config = json.load(f)
        
        self.root_folder = config["root_folder"]
        self.pptx_folder = config["pptx_folder"]
        self.pptx_name = config["pptx_name"]
        self.extract_folder = config["extract_folder"]
        self.output_folder = config["output_folder"]


        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = model
        self.pydentic_model=pydentic_model
        self.client = client
        self.extract_namespaces = extract_namespaces
        self.namespaces =namespaces 

        self.pptx_path = os.path.join(self.root_folder, self.pptx_folder, self.pptx_name)
        if verbose: print(f"\tPPTX path: {self.pptx_path}")
        self.extract_path = os.path.join(self.root_folder, self.extract_folder)
        if verbose: print(f"\tExtract path: {self.extract_path}")
        self.output_folder = os.path.join(self.root_folder, self.output_folder)
        if verbose: print(f"\tOutput folder: {self.output_folder}")
        self.output_pptx_name = f'translated_{self.pptx_name}'
        if verbose: print(f"\tOutput PPTX name: {self.output_pptx_name}")
        
        if client == "OpenAI":
            self.client = OpenAI(api_key=self.openai_api_key)
        else:
            print("\tClient not supported (So far only OpenAI is supported)")
        pass
      
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
        pass

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