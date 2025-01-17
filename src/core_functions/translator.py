from lxml import etree as ET
from openai import OpenAI
from googletrans import Translator
import asyncio
from pydantic import BaseModel
import json
from langdetect import detect
from typing import List
from .base_class import PowerpointPipeline
import os
import re
import traceback
from utils.promts import translation_prompt_0, translation_prompt_1

class TranslationResponse(BaseModel):
    translation: str

class SlideTranslator(PowerpointPipeline):
    def __init__(self, 
                 target_language: str = "German",
                 Further_StyleInstructions: str = "None",
                 update_language: bool = False,
                 reduce_slides: bool = False,
                 verbose: bool = False,
                 translation_method: str = "OpenAI"): 

        super().__init__()

        self.target_language = target_language
        self.Further_StyleInstructions = Further_StyleInstructions
        self.update_language = update_language
        self.reduce_slides = reduce_slides
        self.verbose = verbose
        self.translation_method = translation_method
        # Load language codes mapping
        config_languages_path = os.path.join(self.root_folder, "src", "config_languages.json")
        with open(config_languages_path, "r") as f:
            self.language_codes = json.load(f)

    def analyze_text(self, text: str) -> str:  
        if not text or text.isspace():
            return "not_translatable"
            
        text = text.strip()
        # Check if empty or just whitespace
        if not text:
            return "not_translatable"
            
        # Check if it's just numbers, basic punctuation, plus/minus signs, and spaces
        if re.match(r'^[+\-\d\s%.,()]+$', text):
            return "not_translatable"
            
        # Check if it's just special characters
        if re.match(r'^[^a-zA-Z0-9\s]*$', text):
            return "not_translatable"
        
        # Check if it's just numbers  and special character(e.g., 10%)
        if re.match(r'^[\d\s%.,]+$', text):  
            return "not_translatable"
            
        # If we get here, the text contains some actual content
        return "translatable"      

    def translate_text_OpenAI(self, text: str) -> str:
        # result = self.analyze_text(text)
        # if result == "not_translatable":
        #     return text  # Return original text without translation
        
        """Translate text while preserving approximate length and formatting."""
        chosen_prompt=1
        prompt_0 = translation_prompt_0(text, self.target_language, self.Further_StyleInstructions)
        prompt_1 = translation_prompt_1(text, self.target_language, self.Further_StyleInstructions)
                
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": prompt_1}
                    ],
                    temperature=0.1
                )
                
        except Exception as e:
            print(f"Translation error. Something wrong with the LLM: {e}")
            return text

        try:
            if chosen_prompt==0:
                return response.choices[0].message.content.strip()
            
            if chosen_prompt==1:
                content = response.choices[0].message.content.strip()
                # Extract text between <translation> tags
                translation_match = re.search(r'<translation>\s*(.*?)\s*</translation>', content, re.DOTALL)
                if translation_match:
                    if self.verbose:
                        print(f"\tTranslation match: {translation_match.group(1).strip()}")
                    return translation_match.group(1).strip()

        except Exception as e:
            print(f"Response.strip() error: {e} for text: {text} with result {response.choices[0].message.content}")
            print("Full traceback:")
            print(traceback.format_exc())        

    def translate_text_google(self, text: str) -> str:
        # First find the matching language code from the languages list
        target_lang_code = None
        for lang in self.language_codes.get('languages', []):
            if lang['language'].startswith(self.target_language):
                target_lang_code = lang['code']
                break
        
        if not target_lang_code:
            print(f"Warning: Could not find language code for {self.target_language}, defaulting to 'en-US'")
            target_lang_code = 'en-US'
        
        # Map the PowerPoint language code to Google translate code
        google_lang_code = self.language_codes.get('language_google_codes', {}).get(target_lang_code)
        
        if not google_lang_code:
            print(f"Warning: Could not find Google translate code for {target_lang_code}, defaulting to 'en'")
            google_lang_code = 'en'

        async def translate_text():
            async with Translator() as translator:
                self.result = await translator.translate(text, dest=google_lang_code)
        
        asyncio.run(translate_text())
        return self.result.text

    def create_translation_map(self, text_elements: List[ET.Element], original_text_elements: set) -> dict:
        """Create a mapping between original text and their translations."""
        translation_map = {text: "" for text in original_text_elements}
        for element in text_elements:
            if element.text is not None:  
                self.original_text = element.text.strip()
                source_lang = element.get('lang', 'en-GB') 
            else:
                continue

            if self.original_text is not None:
                # Check if the text is only a number (float or integer) with optional spaces
                if re.match(r'^\s*-?\d*\.?\d+\s*$', self.original_text):
                    translated_text = self.original_text
                    # Update translation map for the current original text
                    if self.original_text in translation_map:
                        translation_map[self.original_text] = translated_text
                else:
                    if self.translation_method == "OpenAI":
                        translated_text = self.translate_text_OpenAI(self.original_text)
                    elif self.translation_method == "Google":
                        translated_text = self.translate_text_google(self.original_text)
                    if self.verbose:     
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
                                {"role": "system", "content": "You are a professional text alignment expert, editor and translator."},
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
                        print(f"\tError matching segments for translation map: {e}")
                        print("Full traceback:")
                        print(traceback.format_exc())
        if self.verbose:
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
        reduce_slides = False

        for slide_file in sorted(slide_files):
            if self.reduce_slides:
                if os.path.basename(slide_file) not in selected_slides:
                    continue

            if self.verbose:
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