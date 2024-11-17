from lxml import etree as ET
from openai import OpenAI
from pydantic import BaseModel
import json
from langdetect import detect
from typing import List
from .base_class import PowerpointPipeline
import os
import re
import traceback
from ..utils.promts import translation_prompt_0, translation_prompt_1

class TranslationResponse(BaseModel):
    translation: str

class SlideTranslator(PowerpointPipeline):
    def __init__(self, 
                 target_language: str,
                 Further_StyleInstructions: str = "None",
                 update_language: bool = False): 

        super().__init__()

        self.target_language = target_language
        self.Further_StyleInstructions = Further_StyleInstructions
        self.update_language = update_language
        # Load language codes mapping
        with open("config_languages.json", "r") as f:
            self.language_codes = json.load(f)

    def analyze_text(self, text: str) -> str:  # Added self parameter and type hint
        if not text or text.isspace():
            return "Unusable"
            
        text = text.strip()
        # Check if empty or just whitespace
        if not text:
            return "Unusable"
            
        # Check if it's just numbers, basic punctuation, plus/minus signs, and spaces
        if re.match(r'^[+\-\d\s%.,()]+$', text):
            return "Unusable"
            
        # Check if it's just special characters
        if re.match(r'^[^a-zA-Z0-9\s]*$', text):
            return "Unusable"
        
        # Check if it's just numbers  and special character(e.g., 10%)
        if re.match(r'^[\d\s%.,]+$', text):  
            return "Unusable"
            
        # If we get here, the text contains some actual content
        return "Usable"      

    def translate_text(self, text: str) -> str:

        # result = self.analyze_text(text)
        # if result == "Unusable":
        #     return text  # Return original text without translation
        

        """Translate text while preserving approximate length and formatting."""
        chosen_prompt=0
        prompt_0 = translation_prompt_0(text, self.target_language, self.Further_StyleInstructions)
        prompt_1 = translation_prompt_1(text, self.target_language, self.Further_StyleInstructions)
                
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": prompt_0}
                    ],
                    temperature=0.3
                )
                
                # if not response.choices[0]:
                #     print(f"No response from LLM with this text: {text}")
                #     return text
                # elif not response.choices[0].message:
                #     print(f"No message in response from LLM with this text: {text}")
                #     return text
                # elif not response.choices[0].message.content:
                #     print(f"No content in response from LLM with this text: {text}")
                #     return text
                # return response.choices[0].message.content.strip()
            try:
                if chosen_prompt==0:
                    return response.choices[0].message.content.strip()
                
                if chosen_prompt==1:
                    content = response.choices[0].message.content.strip()
                    # Extract text between <translation> tags
                    translation_match = re.search(r'<translation>\s*(.*?)\s*</translation>', content, re.DOTALL)
                    if translation_match:
                        return translation_match.group(1).strip()

            except Exception as e:
                print(f"Response.strip() error: {e} for text: {text} with result {response.choices[0].message.content}")
                print("Full traceback:")
                print(traceback.format_exc())        
        except Exception as e:
            print(f"Translation error: {e}")
            print("Full traceback:")
            print(traceback.format_exc())

            
        # else: #pydentic model   
        #     try:
        #         response = self.client.chat.completions.create(
        #             model=self.model,
        #             messages=[
        #                 {"role": "system", "content": "You are a professional translator."},
        #                 {"role": "user", "content": prompt + pydentic_prompt_addition}
        #             ],
        #             tools=[{
        #             "type": "function",
        #             "function": {
        #                 "name": "format_translation_text",
        #                 "description": "Format the translation text as JSON",
        #                 "parameters": {
        #                     "type": "object",
        #                     "properties": {
        #                         "translation": {
        #                             "type": "string",
        #                             "description": "The translation of the input text"
        #                         }
        #                     },
        #                     "required": ["translation"]
        #                 }
        #                 }
        #             }],
        #             tool_choice={"type": "function", "function": {"name": "format_translation_text"}},
                
        #             temperature=0.3,
        #             response_format={ "type": "json_object" }
        #         )
                # translation_response = TranslationResponse.model_validate_json(
                #     response.choices[0].message.content
                # )
            #     return translation_response.translation.strip()
    
            # except Exception as e:
            #     if "Error code: 400" in str(e):
            #         print(f"ERROR We use Pydentic, therefore the model must support json output (e.g. gpt-4-turbo-preview)| Translation error: {e}")
            #     else:
            #         print(f"Translation error: {e}")  
            #         print("Full traceback:")
            #         print(traceback.format_exc())  
            #     return text

    def create_translation_map(self, text_elements: List[ET.Element], original_text_elements: set) -> dict:
        """Create a mapping between original text and their translations."""
        translation_map = {text: "" for text in original_text_elements}
        
        for element in text_elements:
            self.original_text = element.text.strip()
            source_lang = element.get('lang', 'en-GB')
            #print(f"\tLLM fed text: {original_text}")
            if self.original_text:
                translated_text = self.translate_text(self.original_text)
                print(f"\tOriginal paragraph: {self.original_text}")
                print(f"\tTranslated paragraph: {translated_text}\n")
                
                prompt = f"""Match each original text segment with its corresponding part from the translation.
                Original segments: {[text for text in original_text_elements]}
                Full original text: {self.original_text}
                Full translation: {translated_text}
                
                Return a JSON object where keys are the original segments and values are their corresponding translations.
                Only include segments that appear in the original text."""
                
                try:
                    response = self.client.chat.completions.create(
                        model=self.pydentic_model,
                        messages=[
                            {"role": "system", "content": "You are a professional text alignment expert."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        response_format={"type": "json_object"}
                    )
                    
                    segment_mappings = json.loads(response.choices[0].message.content)
                    
                    for orig_text, trans_text in segment_mappings.items():
                        if orig_text in translation_map:
                            translation_map[orig_text] = trans_text
                            
                except Exception as e:
                    print(f"\tError matching segments: {e}")
                    print("Full traceback:")
                    print(traceback.format_exc())
        
        print(f"\tTranslation map: {translation_map}")
        return translation_map

    def detect_pptx_language(self, text: str) -> str:
        """Detect language and return PowerPoint language code."""
        # Handle empty or whitespace-only text
        if not text or text.isspace():
            return "en-US"
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Check if text is only numbers, punctuation, or special characters
        if all(char.isdigit() or char in '.,!?;:+-*/=()[]{}%$#@&' for char in text):
            return "en-US"
        
        try:
            # Detect language
            detected_lang = detect(text)
            # Convert to PowerPoint language code
            pptx_lang = self.language_codes.get(detected_lang, "en-US")  # default to en-US if not found
            return pptx_lang
        except Exception as e:
            print(f"\tLanguage detection error: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return "en-US"  # default to en-US on error

    def process_slides(self, folder_path: str):
        """Main function to process all slides in the presentation."""
        slide_files = self.find_slide_files(folder_path)
        selected_slides = ["slide2.xml", "slide3.xml", "slide4.xml"]

        for slide_file in sorted(slide_files):
            if os.path.basename(slide_file) not in selected_slides:
                continue

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
            translation_map = self.create_translation_map(text_elements, original_text_elements) # FYI: in here there is also the translation happening
            
            # Update text while preserving XML structure and whitespace
            for original_text, translation in translation_map.items():
                if not translation.strip():  # Skip empty translations
                    continue
                #Update Text
                for element in root.findall('.//a:t', self.namespaces):
                    if element.text and element.text.strip() == original_text:
                        if translation.strip():  # If we have a valid translation
                            # Preserve any leading/trailing whitespace from the original
                            leading_space = ''
                            trailing_space = ''
                            if element.text.startswith(' '):
                                leading_space = ' '
                            if element.text.endswith(' '):
                                trailing_space = ' '
                            # Update text
                            element.text = leading_space + translation.strip() + trailing_space

                        else:
                            # Find the parent run ('a:r') element and remove it
                            parent_run = element.getparent()
                            if parent_run is not None:
                                parent_paragraph = parent_run.getparent()
                                if parent_paragraph is not None:
                                    parent_paragraph.remove(parent_run)

                if self.update_language:
                    # Detect and update language
                    for run in root.findall('.//a:r', self.namespaces):
                        text_elem = run.find('a:t', self.namespaces)
                        if text_elem.text is not None:
                            try:
                                detected_lang = self.detect_pptx_language(text_elem.text.strip())
                                # Find and update the language attribute in the corresponding rPr element
                                #parent_run = text_elem.getparent()
                                rPr = run.find('a:rPr', self.namespaces)
                                if rPr is not None:
                                    rPr.set('lang', detected_lang)
                                    print(f"\tUpdated language for '{translation.strip()}' to {detected_lang}")
                            except Exception:
                                continue
                        # else:
                        #     # Create rPr element if it doesn't exist
                        #     rPr = ET.SubElement(run, f"{{{self.namespaces['a']}}}rPr")
                        #     rPr.set('lang', detected_lang)
                        #     print(f"created property language for '{translation.strip()}' to {detected_lang}")                                    

            # Register extracted namespaces
            for prefix, uri in namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Register our known namespaces
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Write back XML while preserving declaration and namespaces
            with open(slide_file, 'wb') as f:
                tree.write(f, encoding='UTF-8', xml_declaration=True)