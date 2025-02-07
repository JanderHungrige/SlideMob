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
from openai import AzureOpenAI

class TranslationResponse(BaseModel):
    translation: str

class SlideTranslator():
    def __init__(self, pipeline_settings: Optional[PowerpointPipeline] = None,
                 verbose: bool = False):

        # Initialize parent class first with settings from pipeline_settings
        self.root_folder=pipeline_settings.root_folder
        self.translation_method=pipeline_settings.translation_method
        self.mapping_method=pipeline_settings.mapping_method
        self.translation_client=pipeline_settings.translation_client
        self.mapping_client=pipeline_settings.mapping_client
        self.translation_model=pipeline_settings.translation_model
        self.mapping_model=pipeline_settings.mapping_model
        self.style_instructions = pipeline_settings.style_instructions
        self.update_language = pipeline_settings.update_language
        self.reduce_slides = pipeline_settings.reduce_slides
        self.verbose = pipeline_settings.verbose
        self.target_language = pipeline_settings.target_language
        self.verbose=pipeline_settings.verbose
        self.namespaces=pipeline_settings.namespaces
        self.translation_headers=pipeline_settings.translation_headers
        self.mapping_headers=pipeline_settings.mapping_headers
        self.translation_api_url=pipeline_settings.translation_api_url
        self.mapping_api_url=pipeline_settings.mapping_api_url
        
        self.find_slide_files=pipeline_settings.find_slide_files
        self.extract_paragraphs=pipeline_settings.extract_paragraphs
        self.extract_text_runs=pipeline_settings.extract_text_runs
   
        # Load language codes mapping
        config_languages_path = os.path.join(self.root_folder, "src", "config_languages.json")
        with open(config_languages_path, "r") as f:
            self.language_codes = json.load(f)

        # Check model type for LMStudio
        if hasattr(self, 'translation_model') and self.translation_model:
            if re.search(r'\bllama\b', self.translation_model.lower()):
                self.translation_model_type = "llama"
            elif re.search(r'\bdeepseek\b', self.translation_model.lower()):
                self.translation_model_type = "deepseek"
            else:
                self.translation_model_type = "unknown"

        # Check model type for LMStudio
        if hasattr(self, 'mapping_model') and self.mapping_model:
            if re.search(r'\bllama\b', self.mapping_model.lower()):
                self.mapping_model_type = "llama"
            elif re.search(r'\bdeepseek\b', self.translation_model.lower()):
                self.mapping_model_type = "deepseek"
            else:
                self.mapping_model_type = "unknown"

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
                    elif self.translation_method == "DeepSeek":
                        translated_text = self.translate_text_deepseek(self.original_text)
                    elif self.translation_method == "HuggingFace":
                        translated_text = self.translate_text_huggingface(self.original_text)
                    elif self.translation_method == "LMStudio":
                        translated_text = self.translate_text_lmstudio(self.original_text)
                    elif self.translation_method == "Azure OpenAI":
                        translated_text = self.translate_text_azure_openai(self.original_text)
    
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

    def use_translation_OpenAIclient(self, prompt: str, temperature: float, response_format: str) -> str:
        try:
            response = self.translation_client.chat.completions.create(
                model=self.translation_model,
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    response_format=response_format
                )
            return response
        
        except Exception as e:
            print(f"Translation error. Something wrong with the OpenAI API: {e}")

    def use_mapping_OpenAIclient(self, prompt: str, temperature: float, response_format: str) -> str:
        try:
            response = self.mapping_client.chat.completions.create(
                model=self.mapping_model,
                    messages=[
                        {"role": "system", "content": "You are a professional text alignment expert, editor and translator."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    response_format=response_format
                )
            return response
        
        except Exception as e:
            print(f"Mapping error. Something wrong with the OpenAI API: {e}")


    def translate_text_OpenAI(self, text: str) -> str:
        # result = self.analyze_text(text)
        # if result == "not_translatable":
        #     return text  # Return original text without translation
        
        """Translate text while preserving approximate length and formatting."""
        chosen_prompt=1
        prompt_0 = translation_prompt_openai_0(text, self.target_language, self.style_instructions)
        prompt_1 = translation_prompt_openai_1(text, self.target_language, self.style_instructions)
                
        try:
            response = self.use_translation_OpenAIclient(prompt_0, 1.5, "text")
        except Exception as e:
            print(f"Translation error. Something wrong with the OpenAI API: {e}")
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
    
    def translate_text_deepseek(self, text: str) -> str:
        # result = self.analyze_text(text)
        # if result == "not_translatable":
        #     return text  # Return original text without translation
        
        """Translate text while preserving approximate length and formatting."""
        prompt_0 = translation_prompt_deepseek_0(text, self.target_language, self.style_instructions)
                
        try:
            response = self.use_translation_OpenAIclient(prompt_0, 1.5)
        except Exception as e:
            print(f"Translation error. Something wrong with the DeepSeek API: {e}")
            return text

        try:
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
    
    def translate_text_huggingface(self, text: str) -> str:
        prompt_0 = translation_prompt_llama2_0(text, self.target_language, self.style_instructions)
        prompt_1 = translation_prompt_llama2_1(text, self.target_language, self.style_instructions)

        payload = {"inputs": prompt_0}
        response = requests.post(self.translation_api_url,
                                 headers=self.translation_headers, 
                                 json=payload)
                        
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

        if self.translation_model_type == "llama":
            prompt_0 = translation_prompt_llama2_0(text, self.target_language, self.style_instructions)
        elif self.translation_model_type == "deepseek":
            prompt_0 = translation_prompt_deepseek_0(text, self.target_language, self.style_instructions)
        elif self.translation_model_type == "unknown":
            print(f"Warning: Translation model type not recognized: {self.translation_model_type}")
            return text
        
        viaOpenAIclient = True
        if viaOpenAIclient:
            response_format = {"type": "json_object"}
            response = self.use_translation_OpenAIclient(prompt_0, 1.5, response_format)
        else:
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt_0}
                ],
                "model": self.translation_model,
                "temperature": 1.5
            }
            
            response = requests.post(
                self.translation_api_url,
                headers=self.translation_headers,
                json=payload,
                timeout=42
            )
            response.raise_for_status()
            response = response.json()
        try:

            content = response['choices'][0]['message']['content']
            
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
        
    def translate_text_azure_openai(self, text: str) -> str:
        """Translate text using Azure OpenAI"""
        try:
            # Get Azure config from settings or use defaults
            azure_config = getattr(self, 'azure_translation_config', AZURE_CONFIG)
            
            model_cfg = {
                "engine": self.translation_model,
                "api_version": "2024-02-15-preview",
                "temperature": azure_config["temperature"],
                "frequency_penalty": azure_config["frequency_penalty"],
                "presence_penalty": azure_config["presence_penalty"],
                "max_tokens_out": azure_config["max_tokens_out"]
            }
            
            if not hasattr(self, 'azure_client'):
                self.azure_client = AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_ENDPOINT_KEY"),
                    api_version=model_cfg["api_version"],
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
                )

            prompt = translation_prompt_openai_1(text, self.target_language, self.style_instructions)
            
            response = self.azure_client.chat.completions.create(
                model=model_cfg["engine"],
                messages=[{"role": "user", "content": prompt}],
                temperature=model_cfg["temperature"],
                frequency_penalty=model_cfg["frequency_penalty"],
                presence_penalty=model_cfg["presence_penalty"],
                max_tokens=model_cfg["max_tokens_out"]
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error in Azure OpenAI translation: {e}")
            return text
    
    def _create_mapping_map(self, original_text_elements: set, translated_text: str, translation_map: dict) -> dict:
        """Create a mapping between original text and their translations."""

        try:
            if self.mapping_method == "OpenAI":
                prompt = mapping_prompt_openai(original_text_elements, self.original_text, translated_text)
                response_format={"type": "json_object"}
                response = self.use_mapping_OpenAIclient(prompt, 0.3, response_format)
                segment_mappings = json.loads(response.choices[0].message.content)
            
            elif self.mapping_method == "Azure OpenAI":
                prompt = mapping_prompt_openai(original_text_elements, self.original_text, translated_text)
                response_format={"type": "json_object"}
                response = self.use_mapping_OpenAIclient(prompt, 0.3, response_format)
                segment_mappings = json.loads(response.choices[0].message.content)
                
            elif self.mapping_method == "DeepSeek":
                prompt = mapping_prompt_deepseek(original_text_elements, self.original_text, translated_text)
                response_format={"type": "json_object"}
                response = self.use_mapping_OpenAIclient(prompt, 0.3, response_format)
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
                if self.mapping_model_type == "llama":
                    formatted_prompt = mapping_prompt_llama2(original_text_elements, self.original_text, translated_text)
                elif self.mapping_model_type == "deepseek":
                    formatted_prompt = mapping_prompt_deepseek(original_text_elements, self.original_text, translated_text)
                elif self.mapping_model_type == "unknown":
                    print(f"Warning: Mapping model type not recognized: {self.mapping_model_type}")
                    return {}
                
                viaOpenAIclient = True
                if viaOpenAIclient:
                    response_format={"type": "json_object"}
                    response = self.use_mapping_OpenAIclient(formatted_prompt, 0.3, response_format)
                else:
                    payload = {
                        "messages": [
                            {"role": "system", "content": "You are a professional text alignment expert, editor and translator."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "model": self.mapping_model,
                    "temperature": 0.3
                }
                
                    response = requests.post(
                        self.mapping_api_url,
                        headers=self.mapping_headers,
                        json=payload,
                        timeout=42
                    )
                    response.raise_for_status()
                    response = response.json()
        
                try:
                    content = response['choices'][0]['message']['content']
                    
                    # Find JSON content between the last [/INST] and the end
                    json_text = content.split("[/INST]")[-1].strip()
                    # Try to parse the JSON
                    segment_mappings = json.loads(json_text)
                
                except (json.JSONDecodeError, KeyError, IndexError, requests.RequestException) as e:
                    print(f"Error parsing LMStudio mapping response: {e}")
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

    def process_slides(self, progress_callback=None, stop_check_callback=None):
        """Main function to process all slides in the presentation."""
        slide_files = self.find_slide_files()
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

