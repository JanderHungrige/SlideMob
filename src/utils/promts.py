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

def translation_prompt_huggingface_llama2_0(text, target_language, Further_StyleInstructions):
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

def translation_prompt_huggingface_llama2_1(text, target_language, Further_StyleInstructions):
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