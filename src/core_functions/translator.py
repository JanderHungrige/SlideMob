from lxml import etree as ET
import requests
from googletrans import Translator
import asyncio
from pydantic import BaseModel
import json
from langdetect import detect
from typing import List, Optional
from .base_class import PowerpointPipeline
import os
import re
import traceback
from utils.promts import (translation_prompt_openai_0, translation_prompt_openai_1, 
                         translation_prompt_llama2_0, translation_prompt_llama2_1,
                         mapping_prompt_openai, mapping_prompt_llama2,
                         translation_prompt_deepseek_0, mapping_prompt_deepseek)

class TranslationResponse(BaseModel):
    translation: str

class SlideTranslator(PowerpointPipeline):
    def __init__(self, 
                 target_language: str = "German",
                 Further_StyleInstructions: str = "None",
                 update_language: bool = False,
                 reduce_slides: bool = False,
                 verbose: bool = False,
                 translation_method: str = "OpenAI",
                 mapping_method: str = "OpenAI",
                 pipeline_settings: Optional[PowerpointPipeline] = None): 

        # Initialize parent class (PowerpointPipeline)
        super().__init__(translation_client=translation_method, mapping_client=mapping_method,
                         model_settings=pipeline_settings)
        
        if pipeline_settings:
            # Copy settings from the provided PowerpointPipeline instance
            self.trans_client = pipeline_settings.trans_client
            self.map_client = pipeline_settings.map_client
            self.translation_model = pipeline_settings.translation_model
            self.translation_client = pipeline_settings.translation_client
            self.mapping_client = pipeline_settings.mapping_client
            self.mapping_model = pipeline_settings.mapping_model

            
            # Copy additional settings
            for attr in ['HUGGINGFACE_API_URL', 'huggingface_headers', 
                        'LMSTUDIO_API_URL', 'lmstudio_model', 'lmstudio_headers',
                        'mapping_model']:
                if hasattr(pipeline_settings, attr):
                    setattr(self, attr, getattr(pipeline_settings, attr))

        self.target_language = target_language
        self.Further_StyleInstructions = Further_StyleInstructions
        self.update_language = update_language
        self.reduce_slides = reduce_slides
        self.verbose = verbose
        self.translation_method = translation_method
        self.mapping_method = mapping_method

        # Load language codes mapping
        config_languages_path = os.path.join(self.root_folder, "src", "config_languages.json")
        with open(config_languages_path, "r") as f:
            self.language_codes = json.load(f)

        # Model settings are already initialized in the parent class (PowerpointPipeline)
        # We can access them directly since they were set up by ModelSettings
        if translation_method == "OpenAI":
            self.model = self.model  # From parent class via ModelSettings
        elif translation_method == "LMStudio":
            self.LMSTUDIO_API_URL = self.LMSTUDIO_API_URL  # From parent class
            self.lmstudio_model = self.lmstudio_model
            self.lmstudio_headers = self.lmstudio_headers
            # Check model type
            if re.search(r'\bllama\b', self.lmstudio_model.lower()):
                self.model_type = "llama"
            elif re.search(r'\bdeepseek\b', self.lmstudio_model.lower()):
                self.model_type = "deepseek"
            else:
                self.model_type = "unknown"
        elif translation_method == "HuggingFace":
            self.HUGGINGFACE_API_URL = self.HUGGINGFACE_API_URL  # From parent class

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
                    elif self.translation_method == "HuggingFace":
                        translated_text = self.translate_text_huggingface(self.original_text)
                    elif self.translation_method == "LMStudio":
                        translated_text = self.translate_text_lmstudio(self.original_text)
    
                    if self.verbose:     
                        print(f"\tOriginal paragraph: {self.original_text}")
                        print(f"\tTranslated paragraph: {translated_text}\n")

                    translation_map = self._create_mapping_map(original_text_elements, translated_text, translation_map)
        return translation_map

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
        prompt_0 = translation_prompt_openai_0(text, self.target_language, self.Further_StyleInstructions)
        prompt_1 = translation_prompt_openai_1(text, self.target_language, self.Further_StyleInstructions)
                
        try:
            response = self.trans_client.chat.completions.create(
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
    
    def translate_text_huggingface(self, text: str) -> str:
        prompt_0 = translation_prompt_llama2_0(text, self.target_language, self.Further_StyleInstructions)
        prompt_1 = translation_prompt_llama2_1(text, self.target_language, self.Further_StyleInstructions)

        payload = {"inputs": prompt_0}
        response = requests.post(self.HUGGINGFACE_API_URL, headers=self.huggingface_headers, json=payload)
                        
        # Extract and validate JSON from the response
        try:
            response_text = response.json()[0]["generated_text"]
            # Find JSON content between the last [/INST] and the end
            content = response_text.split("[/INST]")[-1].strip()
            translation_match = re.search(r'<translation>\s*(.*?)\s*</translation>', content, re.DOTALL)
            if translation_match:
                if self.verbose:
                    print(f"\tTranslation match: {translation_match.group(1).strip()}")
                return translation_match.group(1).strip()
                        
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing Hugging Face response: {e}")
            print(f"Raw response: {response.text}")
            # Return empty mapping as fallback
            return {}
 
    def translate_text_lmstudio(self, text: str) -> str:
        """Translate text using local LMStudio server."""

        if self.model_type == "llama":
            prompt_0 = translation_prompt_llama2_0(text, self.target_language, self.Further_StyleInstructions)
        elif self.model_type == "deepseek":
            prompt_0 = translation_prompt_deepseek_0(text, self.target_language, self.Further_StyleInstructions)
        
        payload = {
            "messages": [
                {"role": "system", "content": "You are a professional translator."},
                {"role": "user", "content": prompt_0}
            ],
            "model": self.lmstudio_model,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                self.LMSTUDIO_API_URL,
                headers=self.lmstudio_headers,
                json=payload
            )
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            
            # Extract text between <translation> tags
            translation_match = re.search(r'<translation>\s*(.*?)\s*</translation>', content, re.DOTALL)
            if translation_match:
                if self.verbose:
                    print(f"\tTranslation match: {translation_match.group(1).strip()}")
                return translation_match.group(1).strip()
            return text
            
        except Exception as e:
            print(f"Translation error with LMStudio: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return text
    
    def _create_mapping_map(self, original_text_elements: set, translated_text: str, translation_map: dict) -> dict:
        """Create a mapping between original text and their translations."""

        try:
            if self.mapping_method == "OpenAI":
                prompt = mapping_prompt_openai(original_text_elements, self.original_text, translated_text)
                
                response = self.map_client.chat.completions.create(
                    model=self.mapping_model,
                    messages=[
                        {"role": "system", "content": "You are a professional text alignment expert, editor and translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
                segment_mappings = json.loads(response.choices[0].message.content)
                
            elif self.mapping_method == "HuggingFace":
                # Use existing HuggingFace implementation
                system_prompt = """You are a professional text alignment expert, editor and translator.
                Your task is to return a JSON object mapping original text segments to their translations.
                The output must be valid JSON with the original segments as keys and translations as values."""
                
                formatted_prompt = mapping_prompt_llama2(original_text_elements, self.original_text, translated_text)

                payload = {"inputs": formatted_prompt}
                response = requests.post(self.HUGGINGFACE_API_URL, headers=self.huggingface_headers, json=payload)
                
                # Extract and validate JSON from the response
                try:
                    response_text = response.json()[0]["generated_text"]
                    # Find JSON content between the last [/INST] and the end
                    json_text = response_text.split("[/INST]")[-1].strip()
                    # Try to parse the JSON
                    segment_mappings = json.loads(json_text)
                    
                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    print(f"Error parsing Hugging Face response: {e}")
                    print(f"Raw response: {response.text}")
                    # Return empty mapping as fallback
                    return {}
                
            elif self.mapping_method == "LMStudio":
                # Use existing LMStudio implementation
                if self.model_type == "llama":
                    formatted_prompt = mapping_prompt_llama2(original_text_elements, self.original_text, translated_text)
                elif self.model_type == "deepseek":
                    formatted_prompt = mapping_prompt_deepseek(original_text_elements, self.original_text, translated_text)

                payload = {
                    "messages": [
                        {"role": "system", "content": "You are a professional text alignment expert, editor and translator."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "model": self.lmstudio_model,
                    "temperature": 0.1
                }
                
                try:
                    response = requests.post(
                        self.LMSTUDIO_API_URL,
                        headers=self.lmstudio_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    
                    response_data = response.json()
                    content = response_data['choices'][0]['message']['content']
                    
                    # Find JSON content between the last [/INST] and the end
                    json_text = content.split("[/INST]")[-1].strip()
                    # Try to parse the JSON
                    segment_mappings = json.loads(json_text)
                    
                except (json.JSONDecodeError, KeyError, IndexError, requests.RequestException) as e:
                    print(f"Error parsing LMStudio response: {e}")
                    print(f"Raw response: {response.text if 'response' in locals() else 'No response'}")
                    # Return empty mapping as fallback
                    return {}
            
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

    def process_slides(self, folder_path: str, progress_callback=None, stop_check_callback=None):
        """Main function to process all slides in the presentation."""
        slide_files = self.find_slide_files(folder_path)
        selected_slides = ["slide2.xml", "slide3.xml", "slide4.xml"]
        total_slides = len(slide_files)

        for slide_file in sorted(slide_files):
            # Check if processing should be stopped
            if stop_check_callback and stop_check_callback():
                print("\nProcessing stopped by user")
                return False

            if self.reduce_slides:
                if os.path.basename(slide_file) not in selected_slides:
                    continue

            current_slide = slide_files.index(slide_file) + 1
            if progress_callback:
                progress_callback(os.path.basename(slide_file), current_slide, total_slides)

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
            translation_map = self.create_translation_map(text_elements, original_text_elements)
            
            # Update text while preserving XML structure and whitespace
            for original_text, translation in translation_map.items():
                # Check for stop request during translation updates
                if stop_check_callback and stop_check_callback():
                    print("\nProcessing stopped by user")
                    return False

                if translation==None:  # Skip empty translations
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
                    # Check for stop request during language updates
                    if stop_check_callback and stop_check_callback():
                        print("\nProcessing stopped by user")
                        return False

                    # Detect and update language
                    for run in root.findall('.//a:r', self.namespaces):
                        text_elem = run.find('a:t', self.namespaces)
                        if text_elem is not None and text_elem.text is not None:
                            try:
                                detected_lang = self.detect_pptx_language(text_elem.text.strip())
                                # Find and update the language attribute in the corresponding rPr element
                                #parent_run = text_elem.getparent()
                                rPr = run.find('a:rPr', self.namespaces)
                                if rPr is not None:
                                    rPr.set('lang', detected_lang)
                                    if self.verbose:
                                        print(f"\tUpdated language for '{translation.strip()}' to {detected_lang}")
                            except Exception:
                                continue

            # Register extracted namespaces
            for prefix, uri in namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Register our known namespaces
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Write back XML while preserving declaration and namespaces
            with open(slide_file, 'wb') as f:
                tree.write(f, encoding='UTF-8', xml_declaration=True)
        
        return True