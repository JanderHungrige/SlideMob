import asyncio
import json
import os
import re
import traceback


from langdetect import detect
from lxml import etree as ET
from openai import AzureOpenAI
from pydantic import BaseModel
import requests
import sys

try:
    # Handle bundled packages for PyInstaller before importing argostranslate
    if getattr(sys, 'frozen', False):
        # Look for bundled packages in the _internal/argos-translate/packages dir
        bundled_packages_path = os.path.join(sys._MEIPASS, 'argos-translate/packages')
        if os.path.exists(bundled_packages_path):
            os.environ['ARGOS_TRANSLATE_PACKAGES_DIR'] = bundled_packages_path
            
    import argostranslate.package
    import argostranslate.translate
    HAS_ARGOS = True
except ImportError:
    HAS_ARGOS = False

from ..utils.promts import (
    mapping_prompt_deepseek,
    mapping_prompt_llama2,
    mapping_prompt_openai,
    translation_prompt_deepseek_0,
    translation_prompt_llama2_0,
    translation_prompt_llama2_1,
    translation_prompt_openai_0,
    translation_prompt_openai_1,
    translation_prompt_with_markers,
)
from .base_class import PowerpointPipeline
from ..utils.marker_utils import MarkerUtils


class TranslationResponse(BaseModel):
    translation: str


class SlideTranslator:
    def __init__(
        self,
        pipeline_settings: PowerpointPipeline | None = None,
        verbose: bool = False,
    ):

        # Initialize parent class first with settings from pipeline_settings
        self.root_folder = pipeline_settings.root_folder
        self.translation_method = pipeline_settings.translation_method
        self.mapping_method = pipeline_settings.mapping_method
        self.translation_client = pipeline_settings.translation_client
        self.mapping_client = pipeline_settings.mapping_client
        self.translation_model = pipeline_settings.translation_model
        self.mapping_model = pipeline_settings.mapping_model
        self.style_instructions = pipeline_settings.style_instructions
        self.update_language = pipeline_settings.update_language
        self.reduce_slides = pipeline_settings.reduce_slides
        self.verbose = pipeline_settings.verbose
        self.target_language = pipeline_settings.target_language
        self.verbose = pipeline_settings.verbose
        self.namespaces = pipeline_settings.namespaces
        self.translation_headers = pipeline_settings.translation_headers
        self.mapping_headers = pipeline_settings.mapping_headers
        self.translation_api_url = pipeline_settings.translation_api_url
        self.mapping_api_url = pipeline_settings.mapping_api_url

        self.find_slide_files = pipeline_settings.find_slide_files
        self.extract_paragraphs = pipeline_settings.extract_paragraphs
        self.extract_text_runs = pipeline_settings.extract_text_runs
        self.translation_reasoning_model = pipeline_settings.translation_reasoning_model
        self.mapping_reasoning_model = pipeline_settings.mapping_reasoning_model
        self.translation_strategy = pipeline_settings.translation_strategy

        # Load language codes mapping
        config_languages_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config_languages.json"
        )
        with open(config_languages_path) as f:
            self.language_codes = json.load(f)

        # Check model type for LMStudio
        if hasattr(self, "translation_model") and self.translation_model:
            if re.search(r"\bdeepseek\b", self.translation_model.lower()):
                self.translation_model_type = "deepseek"
            elif re.search(r"\bllama\b", self.translation_model.lower()):
                self.translation_model_type = "llama"
            elif re.search(r"\bgpt\b", self.translation_model.lower()) or re.search(r"\bopenai\b", self.translation_model.lower()):
                self.translation_model_type = "openai"
            else:
                self.translation_model_type = "unknown"

        # Check model type for LMStudio
        if hasattr(self, "mapping_model") and self.mapping_model:
            if re.search(r"\bdeepseek\b", self.mapping_model.lower()):
                self.mapping_model_type = "deepseek"
            elif re.search(r"\bllama\b", self.mapping_model.lower()):
                self.mapping_model_type = "llama"
            elif re.search(r"\bgpt\b", self.mapping_model.lower()) or re.search(r"\bopenai\b", self.mapping_model.lower()):
                self.mapping_model_type = "openai"
            else:
                self.mapping_model_type = "unknown"

    def create_translation_map(
        self, text_elements: list[ET.Element], original_text_elements: set, stop_check_callback=None
    ) -> dict:
        """Create a mapping between original text and their translations."""
        translation_map = {text: "" for text in original_text_elements}
        
        # Debug: Log target language
        if self.verbose:
            print(f"\t[DEBUG] Creating translation map with target_language: '{self.target_language}'")
            print(f"\t[DEBUG] Original text elements to translate: {list(original_text_elements)[:5]}...")
        for element in text_elements:
            # Check for stop request before processing each paragraph
            if stop_check_callback and stop_check_callback():
                print("\nProcessing stopped by user during translation map creation")
                return None  # Return None to indicate stop was requested
            
            if element.text is not None:
                self.original_text = element.text.strip()
                source_lang = element.get("lang", "en-GB")
            else:
                continue

            if self.original_text is not None:
                # Check if the text is only a number (float or integer) with optional spaces
                if re.match(r"^\s*-?\d*\.?\d+\s*$", self.original_text):
                    translated_text = self.original_text
                else:
                    if self.translation_method == "OpenAI":
                        translated_text = self.translate_text_OpenAI(self.original_text)
                    elif self.translation_method == "Google":
                        translated_text = self.translate_text_google(self.original_text)
                    elif self.translation_method == "DeepSeek":
                        translated_text = self.translate_text_deepseek(
                            self.original_text
                        )
                    elif self.translation_method == "HuggingFace":
                        translated_text = self.translate_text_huggingface(
                            self.original_text
                        )
                    elif self.translation_method == "LMStudio":
                        translated_text = self.translate_text_lmstudio(
                            self.original_text
                        )
                    elif self.translation_method == "Azure OpenAI":
                        translated_text = self.translate_text_azure_openai(
                            self.original_text
                        )
                    elif self.translation_method == "Argos Translate":
                        translated_text = self.translate_text_argostranslate(
                            self.original_text
                        )

                    if self.verbose:
                        print(f"\tOriginal paragraph: {self.original_text}")
                        print(f"\tTranslated paragraph: {translated_text}\n")
                    
                    if hasattr(self, 'log_callback') and self.log_callback:
                        self.log_callback(self.original_text, translated_text)
                    
                    # Filter candidates to only those that appear in the current paragraph
                    # This reduces context noise and hallucinations
                    local_candidates = {
                        t for t in original_text_elements 
                        if t in self.original_text
                    }
                    
                    if not local_candidates:
                         # Fallback if strict substring check fails (unlikely if extract matches)
                         local_candidates = original_text_elements

                    translation_map = self._create_mapping_map(
                        local_candidates, translated_text, translation_map, stop_check_callback
                    )
                    
                    # Check for stop request after each paragraph translation
                    if stop_check_callback and stop_check_callback():
                        print("\nProcessing stopped by user during translation map creation")
                        return None  # Return None to indicate stop was requested
        return translation_map

    def analyze_text(self, text: str) -> str:
        if not text or text.isspace():
            return "not_translatable"

        text = text.strip()
        # Check if empty or just whitespace
        if not text:
            return "not_translatable"

        # Check if it's just numbers, basic punctuation, plus/minus signs, and spaces
        if re.match(r"^[+\-\d\s%.,()]+$", text):
            return "not_translatable"

        # Check if it's just special characters
        if re.match(r"^[^a-zA-Z0-9\s]*$", text):
            return "not_translatable"

        # Check if it's just numbers  and special character(e.g., 10%)
        if re.match(r"^[\d\s%.,]+$", text):
            return "not_translatable"

        # If we get here, the text contains some actual content
        return "translatable"

    def use_translation_OpenAIclient(
        self, prompt: str, temperature: float, response_format: str
    ) -> str:
        try:
            # openai.api_base = self.translation_api_url
            client = self.translation_client
            response = client.chat.completions.create(
                model=self.translation_model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )
            return response

        except Exception as e:
            print(f"Translation error. Something wrong with the OpenAI API: {e}")

    def use_mapping_OpenAIclient(
        self, prompt: str, temperature: float, response_format: str
    ) -> str:
        try:
            response = self.mapping_client.chat.completions.create(
                model=self.mapping_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional text alignment expert, editor and translator.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )
            return response

        except Exception as e:
            print(f"Mapping error. Something wrong with the OpenAI API: {e}")

    def translate_text_OpenAI(self, text: str) -> str:
        # result = self.analyze_text(text)
        # if result == "not_translatable":
        #     return text  # Return original text without translation
        """Translate text while preserving approximate length and formatting."""
        chosen_prompt = 1
        prompt_0 = translation_prompt_openai_0(
            text, self.target_language, self.style_instructions
        )
        prompt_1 = translation_prompt_openai_1(
            text, self.target_language, self.style_instructions
        )

        try:
            response = self.use_translation_OpenAIclient(prompt_0, 1.5, "text")
        except Exception as e:
            print(f"Translation error. Something wrong with the OpenAI API: {e}")
            return text

        try:
            if not response:
                return text

            if chosen_prompt == 0:
                return response.choices[0].message.content.strip()

            if chosen_prompt == 1:
                content = response.choices[0].message.content.strip()
                if self.reasoning_model:
                    # First remove any <think>...</think> content, then search for translation
                    content_without_think = re.sub(
                        r"<think>.*?</think>", "", content, flags=re.DOTALL
                    )
                    translation_match = re.search(
                        r"<translation>\s*(.*?)\s*</translation>",
                        content_without_think,
                        re.DOTALL,
                    )
                else:
                    translation_match = re.search(
                        r"<translation>\s*(.*?)\s*</translation>", content, re.DOTALL
                    )
                if translation_match:
                    if self.verbose:
                        print(
                            f"\tTranslation match: {translation_match.group(1).strip()}"
                        )
                return translation_match.group(1).strip()

        except Exception as e:
            content_preview = "No response"
            if 'response' in locals() and response and hasattr(response, 'choices') and response.choices:
                content_preview = response.choices[0].message.content
            print(
                f"Response.strip() error: {e} for text: {text} with result {content_preview}"
            )
            print("Full traceback:")
            print(traceback.format_exc())

    def translate_text_google(self, text: str) -> str:
        # First find the matching language code from the languages list
        target_lang_code = None
        for lang in self.language_codes.get("languages", []):
            if lang["language"].startswith(self.target_language):
                target_lang_code = lang["code"]
                break

        if not target_lang_code:
            print(
                f"Warning: Could not find language code for {self.target_language}, defaulting to 'en-US'"
            )
            target_lang_code = "en-US"

        # Map the PowerPoint language code to Google translate code
        google_lang_code = self.language_codes.get("language_google_codes", {}).get(
            target_lang_code
        )

        if not google_lang_code:
            print(
                f"Warning: Could not find Google translate code for {target_lang_code}, defaulting to 'en'"
            )
            google_lang_code = "en"

        # Get API Key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Error: GOOGLE_API_KEY not found in environment variables.")
            return text

        try:
            url = f"https://translation.googleapis.com/language/translate/v2?key={api_key}"
            payload = {
                "q": text,
                "target": google_lang_code,
                "format": "text"
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result["data"]["translations"][0]["translatedText"]
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get("error", {}).get("message", error_msg)
                except:
                    pass
            print(f"Google translation error: {error_msg}")
            return text

    def translate_text_deepseek(self, text: str) -> str:
        # result = self.analyze_text(text)
        # if result == "not_translatable":
        #     return text  # Return original text without translation
        """Translate text while preserving approximate length and formatting."""
        prompt_0 = translation_prompt_deepseek_0(
            text, self.target_language, self.style_instructions
        )

        try:
            response = self.use_translation_OpenAIclient(prompt_0, 1.5)
        except Exception as e:
            print(f"Translation error. Something wrong with the DeepSeek API: {e}")
            return text

        try:
            if not response:
                return text
                
            content = response.choices[0].message.content.strip()
            # First remove any <think>...</think> content, then search for translation
            content_without_think = re.sub(
                r"<think>.*?</think>", "", content, flags=re.DOTALL
            )
            translation_match = re.search(
                r"<translation>\s*(.*?)\s*</translation>",
                content_without_think,
                re.DOTALL,
            )
            if translation_match:
                if self.verbose:
                    print(f"\tTranslation match: {translation_match.group(1).strip()}")
                return translation_match.group(1).strip()

        except Exception as e:
            content_preview = "No response"
            if 'response' in locals() and response and hasattr(response, 'choices') and response.choices:
                content_preview = response.choices[0].message.content
            print(
                f"Response.strip() error: {e} for text: {text} with result {content_preview}"
            )
            print("Full traceback:")
            print(traceback.format_exc())

    def translate_text_huggingface(self, text: str) -> str:
        prompt_0 = translation_prompt_llama2_0(
            text, self.target_language, self.style_instructions
        )
        prompt_1 = translation_prompt_llama2_1(
            text, self.target_language, self.style_instructions
        )

        payload = {"inputs": prompt_0}
        response = requests.post(
            self.translation_api_url, headers=self.translation_headers, json=payload
        )

        # Extract and validate JSON from the response
        try:
            response_text = response.json()[0]["generated_text"]
            # Find JSON content between the last [/INST] and the end
            content = response_text.split("[/INST]")[-1].strip()
            # First remove any <think>...</think> content, then search for translation
            content_without_think = re.sub(
                r"<think>.*?</think>", "", content, flags=re.DOTALL
            )
            translation_match = re.search(
                r"<translation>\s*(.*?)\s*</translation>",
                content_without_think,
                re.DOTALL,
            )
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
            prompt_0 = translation_prompt_llama2_0(
                text, self.target_language, self.style_instructions
            )
        elif self.translation_model_type == "deepseek":
            prompt_0 = translation_prompt_deepseek_0(
                text, self.target_language, self.style_instructions
            )
        elif self.translation_model_type == "unknown":
            print(
                f"Warning: Translation model type not recognized: {self.translation_model_type}"
            )
            return text

        viaOpenAIclient = True
        if viaOpenAIclient:
            response_format = {"type": "json_object"}
            response = self.use_translation_OpenAIclient(prompt_0, 1.5, response_format)
        else:
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt_0},
                ],
                "model": self.translation_model,
                "temperature": 1.5,
            }

            response = requests.post(
                self.translation_api_url,
                headers=self.translation_headers,
                json=payload,
                timeout=42,
            )
            response.raise_for_status()
            response = response.json()
        try:
            if not response:
                if self.verbose:
                    print(f"\tWarning: No response from translation service for text: {text[:50]}...")
                return text

            # content = response['choices'][0]['message']['content']
            content = response.choices[0].message.content
            # First remove any <think>...</think> content, then search for translation
            if self.translation_reasoning_model:
                content_without_think = re.sub(
                    r"<think>.*?</think>", "", content, flags=re.DOTALL
                )
                translation_match = re.search(
                    r"<translation>\s*(.*?)\s*</translation>",
                    content_without_think,
                    re.DOTALL,
                )
            else:
                translation_match = re.search(
                    r"<translation>\s*(.*?)\s*</translation>", content, re.DOTALL
                )
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
            azure_config = getattr(self, "azure_translation_config", AZURE_CONFIG)

            model_cfg = {
                "engine": self.translation_model,
                "api_version": "2024-02-15-preview",
                "temperature": azure_config["temperature"],
                "frequency_penalty": azure_config["frequency_penalty"],
                "presence_penalty": azure_config["presence_penalty"],
                "max_tokens_out": azure_config["max_tokens_out"],
            }

            if not hasattr(self, "azure_client"):
                self.azure_client = AzureOpenAI(
                    api_key=os.getenv("AZURE_OPENAI_ENDPOINT_KEY"),
                    api_version=model_cfg["api_version"],
                    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                )

            prompt = translation_prompt_openai_1(
                text, self.target_language, self.style_instructions
            )

            response = self.azure_client.chat.completions.create(
                model=model_cfg["engine"],
                messages=[{"role": "user", "content": prompt}],
                temperature=model_cfg["temperature"],
                frequency_penalty=model_cfg["frequency_penalty"],
                presence_penalty=model_cfg["presence_penalty"],
                max_tokens=model_cfg["max_tokens_out"],
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error in Azure OpenAI translation: {e}")
            return text

    @staticmethod
    def install_argos_languages():
        """Install requested Argos Translate packages."""
        if not HAS_ARGOS:
            print("Error: argostranslate is not installed. Cannot install language packs.")
            return False
        try:
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
            
            # Requested pairs:
            # english <-> german
            # english <-> french
            # german <-> french
            # english <-> ukrainian
            # german <-> ukrainian
            # english <-> spanish
            # english <-> portuguese
            
            # Map common names to ISO codes if needed, or check Argos definitions
            # Argos uses ISO 639-1 (e.g. 'en', 'de', 'fr', 'uk', 'es', 'pt')
            
            pairs_to_install = [
                ('en', 'de'), ('de', 'en'),
                ('en', 'fr'), ('fr', 'en'),
                ('de', 'fr'), ('fr', 'de'),
                ('en', 'uk'), ('uk', 'en'),
                ('de', 'uk'), ('uk', 'de'),
                ('en', 'es'), ('es', 'en'),
                ('en', 'pt'), ('pt', 'en'),
            ]
            
            installed_count = 0
            for from_code, to_code in pairs_to_install:
                package_to_install = next(
                    filter(
                        lambda x: x.from_code == from_code and x.to_code == to_code,
                        available_packages
                    ),
                    None
                )
                if package_to_install:
                    if package_to_install in argostranslate.package.get_installed_packages():
                        print(f"Argos package {from_code}->{to_code} already installed.")
                    else:
                        print(f"Installing Argos package {from_code}->{to_code}...")
                        package_to_install.install()
                        installed_count += 1
                else:
                    print(f"Warning: Argos package {from_code}->{to_code} not found.")

            print(f"Argos Translate setup complete. Installed {installed_count} new packages.")
            return True
        except Exception as e:
            print(f"Error installing Argos languages: {e}")
            traceback.print_exc()
            return False

    @staticmethod
    def install_argos_pair(from_code: str, to_code: str):
        """Install a specific Argos Translate language pair."""
        if not HAS_ARGOS:
            return False
        try:
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
            package_to_install = next(
                filter(
                    lambda x: x.from_code == from_code and x.to_code == to_code,
                    available_packages
                ),
                None
            )
            if package_to_install:
                if package_to_install in argostranslate.package.get_installed_packages():
                    print(f"Argos package {from_code}->{to_code} already installed.")
                    return True
                else:
                    print(f"Installing Argos package {from_code}->{to_code}...")
                    package_to_install.install()
                    return True
            else:
                print(f"Warning: Argos package {from_code}->{to_code} not found.")
                return False
        except Exception as e:
            print(f"Error installing Argos pair {from_code}->{to_code}: {e}")
            return False

    @staticmethod
    def install_common_argos_languages():
        """Install common requested Argos Translate packages."""
        return SlideTranslator.install_argos_languages()

    @staticmethod
    def get_installed_argos_languages():
        """Get a list of installed Argos Translate language pairs."""
        if not HAS_ARGOS:
            return []
        try:
            installed_packages = argostranslate.package.get_installed_packages()
            return [f"{p.from_code} -> {p.to_code}" for p in installed_packages]
        except Exception as e:
            print(f"Error getting installed Argos languages: {e}")
            return []

    def translate_text_argostranslate(self, text: str) -> str:
        """Translate text using local Argos Translate."""
        if not HAS_ARGOS:
            if self.verbose:
                print("Warning: Argos Translate not available (module missing).")
            return text
        try:
            # Map target language to code
            # We assume self.target_language is a full name or similar, we need code.
            # Using self.language_codes to find the code.
            
            target_lang_code = "en"
            for lang in self.language_codes.get("languages", []):
                # Match against the base name (before parenthesis) which is what GUI uses
                base_name = lang["language"].split(" (")[0]
                if base_name.lower() == self.target_language.lower():
                    target_lang_code = lang["code"].split('-')[0] # Get 'de' from 'de-DE'
                    break
            
            # Determine source language
            from_code = 'en'
            
            # Use explicitly provided source language if available in config
            if hasattr(self, 'config') and 'source_language' in self.config:
                 source_lang = self.config['source_language']
                 # Map source name to code
                 for lang in self.language_codes.get("languages", []):
                    base_name = lang["language"].split(" (")[0]
                    if base_name.lower() == source_lang.lower():
                        from_code = lang["code"].split('-')[0]
                        break

            if from_code == target_lang_code:
                return text

            # Perform translation
            try:
                translated_text = argostranslate.translate.translate(text, from_code, target_lang_code)
                return translated_text
            except Exception as e:
                # If direct translation unavailable, maybe pivot through English? 
                # Or just fail gracefully.
                # print(f"Argos translation failed for {from_code}->{target_lang_code}: {e}")
                return text

        except Exception as e:
            print(f"Argos Translate critical error: {e}")
            return text

    def _parse_json_response(self, content: str) -> dict:
        """Helper to robustly parse JSON from LLM response."""
        try:
            # Remove markdown code blocks
            content = re.sub(r"```json\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"```\s*$", "", content, flags=re.IGNORECASE)
            content = content.strip()
            
            # If content contains text before/after JSON, extract the JSON object
            match = re.search(r"(\{.*\})", content, re.DOTALL)
            if match:
                content = match.group(1)
            
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Content was: {content}")
            return {}


    def _create_mapping_map(
        self, original_text_elements: set, translated_text: str, translation_map: dict, stop_check_callback=None
    ) -> dict:
        """Create a mapping between original text and their translations."""
        if len(original_text_elements) == 1:
            translation_map[next(iter(original_text_elements))] = translated_text
            return translation_map
            
        if stop_check_callback and stop_check_callback():
            return translation_map
            
        try:
            if self.mapping_method == "OpenAI" or self.mapping_method == "Azure OpenAI":
                prompt = mapping_prompt_openai(
                    original_text_elements, self.original_text, translated_text
                )
                response_format = {"type": "json_object"}
                response = self.use_mapping_OpenAIclient(prompt, 0.3, response_format)
                if response:
                    segment_mappings = self._parse_json_response(response.choices[0].message.content)
                else:
                    segment_mappings = {}

            elif self.mapping_method == "DeepSeek":
                prompt = mapping_prompt_deepseek(
                    original_text_elements, self.original_text, translated_text
                )
                response_format = {"type": "json_object"}
                response = self.use_mapping_OpenAIclient(prompt, 0.3, response_format)
                if response:
                    segment_mappings = self._parse_json_response(response.choices[0].message.content)
                else:
                    segment_mappings = {}

            elif self.mapping_method == "HuggingFace":
                # Use existing HuggingFace implementation
                system_prompt = """You are a professional text alignment expert, editor and translator.
                Your task is to return a JSON object mapping original text segments to their translations.
                The output must be valid JSON with the original segments as keys and translations as values."""

                formatted_prompt = mapping_prompt_llama2(
                    original_text_elements, self.original_text, translated_text
                )
                payload = {"inputs": formatted_prompt}
                response = requests.post(
                    self.HUGGINGFACE_API_URL,
                    headers=self.huggingface_headers,
                    json=payload,
                )

                # Extract and validate JSON from the response
                try:
                    response_text = response.json()[0]["generated_text"]
                    # Find JSON content between the last [/INST] and the end
                    json_text = response_text.split("[/INST]")[-1].strip()
                    # First remove any <think>...</think> content, then search for translation
                    json_text_without_think = re.sub(
                        r"<think>.*?</think>", "", json_text, flags=re.DOTALL
                    )
                    segment_mappings = self._parse_json_response(json_text_without_think)

                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    print(f"Error parsing Hugging Face response: {e}")
                    print(f"Raw response: {response.text}")
                    # Return empty mapping as fallback
                    return {}

            elif self.mapping_method == "LMStudio":
                # Use existing LMStudio implementation
                if self.mapping_model_type == "llama":
                    formatted_prompt = mapping_prompt_llama2(
                        original_text_elements, self.original_text, translated_text
                    )
                elif self.mapping_model_type == "deepseek":
                    formatted_prompt = mapping_prompt_deepseek(
                        original_text_elements, self.original_text, translated_text
                    )
                elif self.mapping_model_type == "unknown":
                    print(
                        f"Warning: Mapping model type not recognized: {self.mapping_model_type}"
                    )
                    return {}

                viaOpenAIclient = True
                if viaOpenAIclient:
                    response_format = {"type": "json_object"}
                    response = self.use_mapping_OpenAIclient(
                        formatted_prompt, 0.3, response_format
                    )
                else:
                    payload = {
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional text alignment expert, editor and translator.",
                            },
                            {"role": "user", "content": formatted_prompt},
                        ],
                        "model": self.mapping_model,
                        "temperature": 0.3,
                    }

                    response = requests.post(
                        self.mapping_api_url,
                        headers=self.mapping_headers,
                        json=payload,
                        timeout=42,
                    )
                    response.raise_for_status()
                    response = response.json()

                try:
                    if not response:
                         if self.verbose:
                             print(f"\tWarning: No response from mapping service")
                         raise ValueError("No response from mapping service")
                         
                    # content = response['choices'][0]['message']['content']
                    content = response.choices[0].message.content
                    if self.mapping_reasoning_model:
                        # First remove any <think>...</think> content, then search for translation
                        content_without_think = re.sub(
                            r"<think>.*?</think>", "", content, flags=re.DOTALL
                        )
                        # Find JSON content between the last [/INST] and the end
                        json_text = content_without_think.split("[/INST]")[-1].strip()
                    else:
                        json_text = content.split("[/INST]")[-1].strip()
                    # Try to parse the JSON
                    segment_mappings = self._parse_json_response(json_text)

                except (
                    json.JSONDecodeError,
                    KeyError,
                    IndexError,
                    requests.RequestException,
                ) as e:
                    print(f"Error parsing LMStudio mapping response: {e}")
                    print(
                        f"Raw response: {getattr(response, 'text', 'No response attribute') if response else 'No response'}"
                    )
                    # Return empty mapping as fallback
                    return {}

            for orig_text, trans_text in segment_mappings.items():
                if orig_text in translation_map:
                    translation_map[orig_text] = trans_text
            
            # Fallback: If mapping failed or is incomplete, and we have only one candidate,
            # apply the full translation to it
            if not segment_mappings and len(original_text_elements) == 1:
                single_text = next(iter(original_text_elements))
                if single_text in translation_map:
                    translation_map[single_text] = translated_text
                    if self.verbose:
                        print(f"\tApplied fallback mapping: '{single_text}' -> '{translated_text}'")

        except Exception as e:
            print(f"\tError matching segments for translation map: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            # Fallback: If mapping completely fails, try to apply translation to the full text
            if len(original_text_elements) == 1:
                single_text = next(iter(original_text_elements))
                if single_text in translation_map and not translation_map[single_text]:
                    translation_map[single_text] = translated_text
                    if self.verbose:
                        print(f"\tApplied error fallback mapping: '{single_text}' -> '{translated_text}'")
        
        if self.verbose:
            print(f"\tTranslation map: {translation_map}")
            # Log any unmapped entries
            unmapped = [k for k, v in translation_map.items() if not v or v.strip() == ""]
            if unmapped:
                print(f"\tWarning: {len(unmapped)} text elements have no translation: {unmapped[:5]}...")
        return translation_map

    def translate_paragraph_with_markers(self, p_element: ET.Element):
        """Translate a paragraph using the marker-based strategy."""
        marked_text, run_properties_map = MarkerUtils.paragraph_to_marked_text(
            p_element, self.namespaces
        )
        
        if not marked_text.strip():
            return
            
        prompt = translation_prompt_with_markers(
            marked_text, self.target_language, self.style_instructions
        )
        
        try:
            # Use OpenAI or similar client to translate
            response = self.use_translation_OpenAIclient(prompt, 0.7, "text")
            
            if not response:
                if self.verbose:
                    print(f"\tWarning: No response from translation service for paragraph")
                return

            translated_marked_text = response.choices[0].message.content.strip()
            
            # Extract content from <translation> tags if present
            translation_match = re.search(
                r"<translation>\s*(.*?)\s*</translation>", 
                translated_marked_text, 
                re.DOTALL | re.IGNORECASE
            )
            if translation_match:
                translated_marked_text = translation_match.group(1).strip()
            
            if self.verbose:
                print(f"\tOriginal marked text: {marked_text}")
                print(f"\tTranslated marked text: {translated_marked_text}")

            # Reconstruct runs
            new_runs = MarkerUtils.marked_text_to_runs(
                translated_marked_text, run_properties_map, self.namespaces
            )
            
            # Clear existing runs and add new ones
            # In PowerPoint XML, a:p can contain a:pPr, a:r, a:br, a:fld, etc.
            # We want to keep a:pPr if it exists and replace everything else.
            pPr = p_element.find("a:pPr", self.namespaces)
            p_element.clear()
            if pPr is not None:
                p_element.append(pPr)
            
            for run in new_runs:
                p_element.append(run)
                
        except Exception as e:
            print(f"Error in marker-based translation: {e}")
            traceback.print_exc()

    def _get_element_xpath(self, element, root):
        """Get a unique XPath-like identifier for an element."""
        # Build a simple path based on parent chain
        parts = []
        current = element
        while current is not None and current != root:
            parent = current.getparent()
            if parent is None:
                break
            # Get index among siblings
            siblings = parent.findall(current.tag, self.namespaces)
            try:
                index = siblings.index(current)
                parts.append(f"{current.tag}[{index}]")
            except (ValueError, AttributeError):
                parts.append(current.tag)
            current = parent
        return "/".join(reversed(parts)) if parts else element.tag

    def _extract_text_runs_from_tree(self, root):
        """Extract text elements from an already-parsed XML tree (not from file)."""
        text_elements = []
        original_text_elements = set()

        # Create a backup with the original text elements
        for paragraph in root.findall(".//a:p", self.namespaces):
            for run in paragraph.findall(".//a:r", self.namespaces):
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
                # Use a valid tag name for lxml. Prefix 'a' is for DrawingML namespace.
                # Clark notation: {http://schemas.openxmlformats.org/drawingml/2006/main}t
                text_element = ET.Element("{http://schemas.openxmlformats.org/drawingml/2006/main}t")
                text_element.text = " ".join(text_parts)
                text_element.set("lang", lang or "en-GB")
                text_elements.append(text_element)

        if self.verbose:
            print("Text elements found:")
            for element in text_elements[:5]:  # Show first 5
                print(f"- {element.text.strip()[:50]} | lang: {element.get('lang')}")
        return text_elements, original_text_elements

    def detect_pptx_language(self, text: str) -> str:
        """Detect language and return PowerPoint language code."""
        # Handle empty or whitespace-only text
        if not text or text.isspace():
            return "en-US"

        # Remove leading/trailing whitespace
        text = text.strip()

        # Check if text is only numbers, punctuation, or special characters
        if all(char.isdigit() or char in ".,!?;:+-*/=()[]{}%$#@&" for char in text):
            return "en-US"

        try:
            # Detect language
            detected_lang = detect(text)
            # Convert to PowerPoint language code
            pptx_lang = self.language_codes.get(
                detected_lang, "en-US"
            )  # default to en-US if not found
            return pptx_lang
        except Exception as e:
            print(f"\tLanguage detection error: {e}")
            print("Full traceback:")
            print(traceback.format_exc())
            return "en-US"  # default to en-US on error

    def process_slides(self, progress_callback=None, stop_check_callback=None, log_callback=None):
        """Main function to process all slides in the presentation."""
        self.log_callback = log_callback
        
        # Debug: Verify target language is set correctly
        print(f"\n[DEBUG] SlideTranslator initialized with target_language: '{self.target_language}'")
        if not self.target_language or self.target_language == "English":
            print(f"[WARNING] Target language is '{self.target_language}' - translations may not be applied!")
        
        slide_files = self.find_slide_files()
        total_slides = len(slide_files)

        for slide_file in sorted(slide_files):
            # Check if processing should be stopped
            if stop_check_callback and stop_check_callback():
                print("\nProcessing stopped by user")
                return False

            current_slide = slide_files.index(slide_file) + 1
            if progress_callback:
                progress_callback(
                    os.path.basename(slide_file), current_slide, total_slides
                )

            if self.verbose:
                print(f"\nProcessing {os.path.basename(slide_file)}...")
                print(
                    f"Processing slide {slide_files.index(slide_file) + 1} of {len(slide_files)}..."
                )

            # Parse XML while preserving structure
            tree = ET.parse(slide_file)
            root = tree.getroot()

            # Extract namespaces from the root element
            namespaces = {}
            for key, value in root.attrib.items():
                if key.startswith("xmlns:"):
                    prefix = key.split(":")[1]
                    namespaces[prefix] = value

            if self.translation_strategy == "marker-based":
                if self.verbose:
                    print(f"\tUsing marker-based translation strategy")
                for p_element in root.findall(".//a:p", self.namespaces):
                    # Check for stop request
                    if stop_check_callback and stop_check_callback():
                        print("\nProcessing stopped by user")
                        return False
                    self.translate_paragraph_with_markers(p_element)
            else:
                if self.verbose:
                    print(f"\tUsing classic translation strategy")
                # Extract and create translation mapping
                # IMPORTANT: Extract from the already-parsed tree, not by re-reading the file
                # This ensures we're working with the current state of the XML
                text_elements, original_text_elements = self._extract_text_runs_from_tree(root)
                if self.verbose:
                    print(f"\tFound {len(text_elements)} text elements and {len(original_text_elements)} original text pieces")
                translation_map = self.create_translation_map(
                    text_elements, original_text_elements, stop_check_callback
                )
                # Check if stop was requested during translation map creation
                if translation_map is None:
                    print("\nProcessing stopped by user")
                    return False
                if self.verbose:
                    non_empty = sum(1 for v in translation_map.values() if v and v.strip())
                    print(f"\tTranslation map has {non_empty}/{len(translation_map)} non-empty translations")

                if self.verbose:
                    print(f"\t[DEBUG] Translation Map Keys: {[repr(k) for k in list(translation_map.keys())[:5]]}...")
                
                updated_xpaths = set()
                total_updates = 0
                
                # Create normalized lookup map for fast O(1) access
                normalized_translation_map = {}
                for k, v in translation_map.items():
                    if k and k.strip():
                        # Use split().join() for robust whitespace normalization
                        normalized_translation_map[' '.join(k.split())] = v.strip()

                # Iterate through XML elements (N)
                for element in root.findall(".//a:t", self.namespaces):
                    # Check for stop request during processing
                    if stop_check_callback and stop_check_callback():
                        print("\nProcessing stopped by user")
                        return False

                    if element.text:
                        original_text = element.text
                        original_normalized = ' '.join(original_text.strip().split())
                        
                        # Check against every translation key (M)
                        # We sort keys by length descending to ensure longest matches are applied first
                        # normalized_translation_map keys are already normalized
                        sorted_keys = sorted(normalized_translation_map.keys(), key=len, reverse=True)
                        
                        for key in sorted_keys:
                            if not key: continue
                            
                            translation = normalized_translation_map[key]
                            
                            # Exact Match Check
                            if key == original_normalized:
                                # Preserve leading/trailing whitespace
                                leading_space = " " if original_text.startswith(" ") else ""
                                trailing_space = " " if original_text.endswith(" ") else ""
                                
                                element.text = leading_space + translation + trailing_space
                                total_updates += 1
                                if self.verbose:
                                    print(f"\tUpdated (Exact): '{original_normalized}' -> '{translation}'")
                                break # Stop checking other keys for this element if we found an exact match
                                
                            # Partial Match Check
                            elif key in original_normalized and len(key) > 3:
                                # Only replace if the key is a substring
                                # We need to serve the original whitespace structure of the substring if possible,
                                # but key normalization makes that hard. N-to-M partial replacement is tricky.
                                # Here we do a simple string replacement on the *original* text if strictly contained.
                                
                                # Note: This simple replacement might fail if whitespace differs significantly.
                                # But for the "one sentence split over slides" case, usually the split parts are clean.
                                if key in original_text: # Check strict substring first
                                     element.text = element.text.replace(key, translation)
                                     total_updates += 1
                                     if self.verbose:
                                         print(f"\tUpdated (Partial): '{key}' -> '{translation}'")
                                     # Don't break here, multiple partial matches might exist
                            
                            # Fallback: check normalized substring (more aggressive)
                            elif key in original_normalized and len(key) > 3:
                                # This is harder to apply back to original_text without disturbing formatting.
                                # We skip this for now to avoid corrupting data, unless user demands it.
                                pass
                
                if self.verbose:
                    print(f"\t[DEBUG] Total text elements updated in this slide: {total_updates}")

                if self.update_language:
                    # Check for stop request during language updates
                    if stop_check_callback and stop_check_callback():
                        print("\nProcessing stopped by user")
                        return False

                    # Detect and update language
                    for run in root.findall(".//a:r", self.namespaces):
                        text_elem = run.find("a:t", self.namespaces)
                        if text_elem is not None and text_elem.text is not None:
                            try:
                                detected_lang = self.detect_pptx_language(
                                    text_elem.text.strip()
                                )
                                # Find and update the language attribute in the corresponding rPr element
                                # parent_run = text_elem.getparent()
                                rPr = run.find("a:rPr", self.namespaces)
                                if rPr is not None:
                                    rPr.set("lang", detected_lang)
                                    if self.verbose:
                                        print(
                                            f"\tUpdated language for '{translation.strip()}' to {detected_lang}"
                                        )
                            except Exception:
                                continue

            # Register extracted namespaces
            for prefix, uri in namespaces.items():
                ET.register_namespace(prefix, uri)

            # Register our known namespaces
            for prefix, uri in self.namespaces.items():
                ET.register_namespace(prefix, uri)

            # Write back XML while preserving declaration and namespaces
            # Debug: Verify we're writing the updated tree
            if self.verbose:
                # Check a few text elements to verify they were updated
                sample_texts = []
                for elem in root.findall(".//a:t", self.namespaces)[:3]:
                    if elem.text:
                        sample_texts.append(elem.text.strip()[:50])
                print(f"\t[DEBUG] Sample texts in XML before writing: {sample_texts}")
            
            with open(slide_file, "wb") as f:
                tree.write(f, encoding="UTF-8", xml_declaration=True)
            
            if self.verbose:
                print(f"\t[DEBUG] XML file written: {slide_file}")

        return True
