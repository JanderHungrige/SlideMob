from .base_class import PowerpointPipeline
from pydantic import BaseModel
import xml.etree.ElementTree as ET
import json
from typing import List
import os

class PolishResponse(BaseModel):
    polished_text: str

class SlidePolisher(PowerpointPipeline):
    def __init__(self, 
                 Further_StyleInstructions: str = "None"): 

        super().__init__()

            
        self.Further_StyleInstructions = ""
        if Further_StyleInstructions != "None":
            self.Further_StyleInstructions = f" Here are some further wording style instructions: {self.Further_StyleInstructions}"
        else:
            self.Further_StyleInstructions = ""

    def polish_text(self, text: str) -> str:
        """Polsish text while preserving approximate length and formatting."""
        prompt = f"""Polish and improve the text following this instructions: 
        IMPORTANT: If the text is already good, just return it as is.
        IMPORTANT: If the text is to short, just return it as is.
        IMPORTANT: For the new text you must not return any other text than the pure polished text.
        Maintain similar total character length and preserve any special formatting or technical terms. 
        Keep technical terms. 
        Keep role names in the translation (e.g., DataScientist, CEO, etc.).
        Keep names of companies in the translation (e.g., Apple, Microsoft, etc.).
        Keep names of products in the translation (e.g., iPhone, Windows, LegalAI, etc.).
        Make the text sharp, concise and business-like.
        {self.Further_StyleInstructions}
        IMPORTANT: For the new polished text you must not return any other text than the pure polished text. Rather than mentioning that you could not improve the text, just return the text as is.
        IMPORTANT: Use the -> format_polished_text tool to return the polished text and the original text for the final response.
        Here is the text to improve:
        {text}
        """

        pydentic_prompt_addition = f"Respond with a JSON object containing only a 'polished_text' field with the polished version of this text"
        
        if self.model == "gpt-4": #non pydentic model
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional editor."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                )
                return response.choices[0].message.content.strip()

            except Exception as e:
                print(f"Polishing error: {e}")
                return text
        else: #pydentic model   
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional editor."},
                        {"role": "user", "content": prompt + pydentic_prompt_addition}
                    ],
                    tools=[{
                        "type": "function",
                        "function": {
                        "name": "format_polished_text",
                        "description": "Format the polished text as JSON",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "original_text": {
                                    "type": "string",
                                    "description": "The original text"
                                },
                                "polished_text": {
                                    "type": "string",
                                    "description": "The polished version of the input text"
                                }
                            },
                            "required": ["original_text", "polished_text"]
                        }
                        }
                    }],
                    tool_choice={"type": "function", "function": {"name": "format_polished_text"}},
                    temperature=0.3,
                    response_format={ "type": "json_object" }
                )
                polished_response = PolishResponse.model_validate_json(
                    response.choices[0].message.content
                )
                return polished_response.polished_text.strip()
    
            except Exception as e:
                if "Error code: 400" in str(e):
                    print(f"ERROR We use Pydentic, therefore the model must support json output (e.g., gpt-4-turbo-preview)| Translation error: {e}")
                else:
                    print(f"Polishing error: {e}")    
                return text

    def create_maping(self, text_elements: List[ET.Element], original_text_elements: set) -> dict:
        """Create a mapping between original text and their translations."""
        polish_mapping = {text: "" for text in original_text_elements}
        
        for element in text_elements:
            original_text = element.text.strip()
            print(f"\tLLM fed text: {original_text}")
            if original_text:
                polished_text = self.polish_text(original_text)
                print(f"\tOriginal paragraph: {original_text}")
                print(f"\tPolished paragraph: {polished_text}\n")
                
                prompt = f"""Match each original text segment with its corresponding part from the polished text.
                Original segments: {[text for text in original_text_elements]}
                Full original text: {original_text}
                Full polished text: {polished_text}
                
                Return a JSON object where keys are the original segments and values are their corresponding polished text.
                Only include segments that appear in the original text."""
                
                try:
                    response = self.client.chat.completions.create(
                        model=self.pydentic_model,
                        messages=[
                            {"role": "system", "content": "You are a professional editor."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    
                    segment_mappings = json.loads(response.choices[0].message.content)
                    
                    for orig_text, trans_text in segment_mappings.items():
                        if orig_text in polish_mapping:
                            polish_mapping[orig_text] = trans_text
                            
                except Exception as e:
                    print(f"\tError matching segments: {e}")
        
        print(f"\tMapping: {polish_mapping}")
        return polish_mapping

    def process_slides(self, folder_path: str):
        """Main function to process all slides in the presentation."""
        slide_files = self.find_slide_files(folder_path)
        
        for slide_file in slide_files:
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
            
            # Extract and create translation mapping
            text_elements, original_text_elements = self.extract_text_runs(slide_file)
            mapping = self.create_maping(text_elements, original_text_elements)
            
            # Update text while preserving XML structure and whitespace
            for original_text, polished_text in mapping.items():
                if not polished_text.strip():  # Skip empty translations
                    continue
                #Update Text
                for element in root.findall('.//a:t', self.namespaces):
                    if element.text and element.text.strip() == original_text:
                        if polished_text.strip():  # If we have a valid translation
                            # Preserve any leading/trailing whitespace from the original
                            leading_space = ''
                            trailing_space = ''
                            if element.text.startswith(' '):
                                leading_space = ' '
                            if element.text.endswith(' '):
                                trailing_space = ' '
                            # Update text
                            element.text = leading_space + polished_text.strip() + trailing_space

                        else:
                            # Find the parent run ('a:r') element and remove it
                            parent_run = element.getparent()
                            if parent_run is not None:
                                parent_paragraph = parent_run.getparent()
                                if parent_paragraph is not None:
                                    parent_paragraph.remove(parent_run)

            # Register extracted namespaces
            for prefix, uri in namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Register our known namespaces
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Write back XML while preserving declaration and namespaces
            with open(slide_file, 'wb') as f:
                tree.write(f, encoding='UTF-8', xml_declaration=True)