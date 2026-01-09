def translation_prompt_openai_0(text, target_language, Further_StyleInstructions):
    return f"""Translate following this instructions: 
    Maintain similar total character length and preserve any special formatting or technical terms. 
    IMPORTANT:For the translation you must not return any other text than the pure translation.
    Keep technical terms in the translation. 
    Keep role names in the translation (e.g., DataScientist, CEO, etc.).
    Keep names of companies in the translation (e.g., Apple, Microsoft, etc.).
    Keep names of products in the translation (e.g., iPhone, Windows, LegalAI, etc.).
    Make the translation sharp, concise and business-like.
    Translate the text to {target_language}.
    {Further_StyleInstructions}
    IMPORTANT:For the translation you must not return any other text than the pure translation.
    Text to translate: {text}
    """


def translation_prompt_openai_1(text, target_language, Further_StyleInstructions):
    return f"""
You are a professional translator tasked with accurately translating text while adhering to specific guidelines. Your goal is to provide a high-quality translation that meets all the given requirements.

Here are the key elements for your translation task:

1. Text to Translate:
<text_to_translate>
{text}
</text_to_translate>

2. Target Language:
<target_language>
{target_language}
</target_language>

3. Additional Style Instructions:
<style_instructions>
{Further_StyleInstructions}
</style_instructions>

Translation Guidelines:
1. Translate the text strictly into the specified target language.
2. Maintain a similar total character length to the original text.
3. Preserve any special formatting, technical terms, company roles (e.g., Lead, Senior, DataScientist), technical names (e.g., LegalAI, GenAI, LLM), company names (e.g., Apple, Microsoft), and product names (e.g., iPhone, Windows).
4. Ensure the translation is sharp, concise, and business-like.
5. Apply any additional style instructions provided.

Translation Process:
Before providing your final translation, perform a detailed analysis inside <translation_analysis> tags. Include the following steps:
1. List any special elements in the text that need to be preserved.
2. Write down 2-3 key phrases or sentences from the original text and their initial translations to serve as anchors.
3. Translate the full text, paying close attention to accuracy and context.
4. Review the translation to ensure it's entirely in the target language.
5. Compare the character count of the original and translated text. List both counts.
6. Refine the translation for sharpness and conciseness.
7. List the style instructions applied and briefly explain how they affected the translation.
8. Perform a final review to ensure all requirements are met.

It's OK for this section to be quite long.

After completing your analysis, provide the final translation within <translation> tags. Remember, your output should contain only the pure translation, without any additional text or explanations."""


def translation_prompt_llama2_0(text, target_language, Further_StyleInstructions):
    return f"""
[INST] You are a professional translator tasked with accurately translating text while adhering to specific guidelines. Your goal is to provide a high-quality translation that meets all the given requirements.

Here are the key elements for your translation task:

1. Text to Translate:
<text_to_translate>
{text}
</text_to_translate>

2. Target Language:
<target_language>
{target_language}
</target_language>

3. Additional Style Instructions:
<style_instructions>
{Further_StyleInstructions}
</style_instructions>

Translation Guidelines:
1. Translate the text strictly into the specified target language.
2. Maintain a similar total character length to the original text.
3. Preserve any special formatting, technical terms, company roles (e.g., Lead, Senior, DataScientist), technical names (e.g., LegalAI, GenAI, LLM), company names (e.g., Apple, Microsoft), and product names (e.g., iPhone, Windows).
4. Ensure the translation is sharp, concise, and business-like.
5. Apply any additional style instructions provided.

Translation Process:
Before providing your final translation, perform a detailed analysis inside <translation_analysis> tags. Include the following steps:
1. List any special elements in the text that need to be preserved.
2. Write down 2-3 key phrases or sentences from the original text and their initial translations to serve as anchors.
3. Translate the full text, paying close attention to accuracy and context.
4. Review the translation to ensure it's entirely in the target language.
5. Compare the character count of the original and translated text. List both counts.
6. Refine the translation for sharpness and conciseness.
7. List the style instructions applied and briefly explain how they affected the translation.
8. Perform a final review to ensure all requirements are met.

It's OK for this section to be quite long.

After completing your analysis, provide the final translation within <translation> tags. Remember, your output should contain only the pure translation, without any additional text or explanations. 
[/INST]"""


def translation_prompt_llama2_1(text, target_language, Further_StyleInstructions):
    return f"""[INST] You are a precise translator. Translate the following text to {target_language}.

Input Text: {text}

Requirements:
- Keep the same approximate length
- Preserve all technical terms, company names, product names, and role titles
- Make it sharp and business-like
- Follow these additional style guidelines: {Further_StyleInstructions}

First analyze the text and plan your translation. Then provide ONLY the final translation.

Format your response as:
<analysis>
1. Terms to preserve:
2. Key phrases:
3. Length check:
4. Style notes:
</analysis>

<translation>
[Your translation here]
</translation>
[/INST]"""


def mapping_prompt_openai(original_segments, original_text, translated_text):
    return f"""Match each original text segment with its corresponding part from the translation.
    Original segments: {[text for text in original_segments]}
    Full original text: {original_text}
    Full translation: {translated_text}
    
    Return a JSON object where keys are the original segments and values are their corresponding translations.
    Only include segments that appear in the original text."""


def mapping_prompt_llama2(original_segments, original_text, translated_text):
    system_prompt = """You are a professional text alignment expert, editor and translator.
    Your task is to return a JSON object mapping original text segments to their translations.
    The output must be valid JSON with the original segments as keys and translations as values."""

    return f"""<s>[INST] <<SYS>>
    {system_prompt}
    <</SYS>>
    
    Original segments: {[text for text in original_segments]}
    Full original text: {original_text}
    Full translation: {translated_text}
    
    Return a JSON object where keys are the original segments and values are their corresponding translations.
    Only include segments that appear in the original text.
    
    Format your response as valid JSON like this:
    {{
        "original_text_1": "translated_text_1",
        "original_text_2": "translated_text_2"
    }}[/INST]"""


def translation_prompt_deepseek_0(text, target_language, Further_StyleInstructions):
    return f"""You are an expert translator specializing in precise, technical translations. Translate the following text to {target_language}.

Input Text:
{text}

Translation Requirements:
1. Make sure that the translation is in the actual target language and no other language or dialect.
2. Maintain similar character length
3. Preserve exactly:
   - All technical terms
   - Role names (e.g., DataScientist, CEO)
   - Company names (e.g., Apple, Microsoft)
   - Product names (e.g., iPhone, Windows, LegalAI)
   - Special formatting and symbols
4. Style:
   - Sharp and business-like tone
   - Concise phrasing
   - {Further_StyleInstructions}

Process:
1. First provide your analysis:
<analysis>
- Key terms to preserve: [list them]
- Initial translation of 2-3 key phrases
- Character count comparison
- Style considerations
- Make sure again that the translation is in the actual target language and no other language or dialect.
</analysis>

2. Then provide ONLY the final translation:
<translation>
[Your translation here]
</translation>

Critical: Return ONLY the content within the <translation> tags as your final output."""


def mapping_prompt_deepseek(original_segments, original_text, translated_text):
    return f"""You are a text alignment specialist. Map each original segment to its corresponding translation.

Input:
Original segments: {[text for text in original_segments]}

Context:
Original text: {original_text}
Translated text: {translated_text}

Task:
1. Find each original segment in the original text
2. Identify its corresponding part in the translation
3. Create a mapping as JSON

Requirements:
- Only include segments that appear in the original text
- Maintain exact matches for technical terms
- Preserve formatting in the translations

Return a valid JSON object with this structure:
{{
    "original_segment": "translated_segment",
    ...
}}

Important: Provide ONLY the JSON output, no explanations."""
def translation_prompt_with_markers(text, target_language, Further_StyleInstructions):
    return f"""You are a professional translator. Your task is to translate the following text while preserving special markers that indicate formatting.

Text to translate (with markers like <f1>, <f2>, etc.):
<text_to_translate>
{text}
</text_to_translate>

Target Language: {target_language}

Instructions:
1. Translate the text into {target_language}.
2. Preserve all markers (<f1>...</f1>, <f2>...</f2>, etc.) and place them around the words or phrases in the translation that carry the same MEANING as the words they were around in the original text.
3. Do not change the IDs of the markers (e.g., if <f1> was around "Revenue", it should be around the translation of "Revenue").
4. Ensure the output is natural and grammatically correct in the target language.
5. If a marker was around multiple words, it should stay around the equivalent words in the translation.
6. Style guidelines: {Further_StyleInstructions}

Return ONLY the translated text with the markers. Do not include any explanations or other tags.

<translation>
"""
