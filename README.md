# SlideMob

SlideMob is a Python-based tool for automated PowerPoint presentation translation using AI. It helps translate presentations while preserving formatting and technical terms.

![SlideMob Logo](./images/doppelfahreimer Small.png)


## Features

- Automated translation of PowerPoint presentations
- Preservation of original formatting and layout
- Support for multiple languages (25+ languages including major European and Asian languages)
- Intelligent handling of technical terms and proper nouns
- Built-in quality control for translations
- Support for custom translation rules and style guides

## Installation

1. Clone the repository
2. Install dependencies using Poetry:

```bash
poetry install
```     

or using pip:

```bash
pip install -r requirements.txt
```

You can aslo use conda by setting up your environment an then install all the dependencies via pip. 
Pro tip: If you are using conda, always make sure to install all conda dependencies first and then install the pip dependencies. Otherwise you might run into issues with missing dlls etc. However, if you follow this order, it will work fine. Pip is our friend.


## Usage



###GUI:

in your the Terminal cd into the slidemob folder and run:
```bash
python main.py
```
Choose the pptx file you want to work with and choose the output folder.

Now you can choose with the radio buttons if you want to just extract the ppt into xml (for devs), polish the text, or translate the presentation. 
At this moment, for each part, the xml is separattely created. This means, that, so far, the features are not run after each other, creating one plished and translated file, but would create two separate pptx files. You would have to manually e.g., first polish the pptx, and then load the polished pptx to translate it. 

If you run translate with the same language as the original text, then, it seems that spelling errors are corrected. But be aware, LLMs can always halucinate and might change the meaning of the text.

ToDo: Add a feature to run all features after each other and create one finished and translated file.

## Supported Languages
As we are using the OpenAI API, you can use any language that is supported by the API. However in the GUI you can only select languages that we put into the config file. If you miss any particular language, you can add it there.
ToDo: Add a way to add languages to the config file via an option "custom languages" in the dropdown menu.

####Configuration

You can add any further instruction to the LLM calls via the field "Additional Style instructions" in the GUI.
Those will be added to the prompt, while the original text is always placed at the end of the prompt.

You can customize the translation behavior through configuration files:
- Language settings
- Translation style guidelines
- Technical term preservation rules
- Output formatting preferences

ToDo: Add a separate Gui field for translation style additions.


###CLI:

You can run the code also in python to better controll the process, and check for errors etc.

Run the code in the terminal with 
```bash
python main.py --testing
```
Optional arguments are:
--input
Path to the input PPTX file (default: uses test presentation if in testing mode)
    
--language
default='English',
choices=['German', 'French', 'Spanish', 'Italian','English']
Target language for translation

-h or --help

If you do not specify an input file, the default test presentation will be used, which is set in main.py.
Right now it is "Testpptx/CV_Jan_Werth_DE_2024-10-23.pptx" as this file does still create problems. 



## ToDos

- create installable exe
- extensive tests
- Bug updateing language setting. The Languagedetector langdetect does get some values at some point he cannot work with. So far skipping did not work, probably not skipt far enough ;-)
- Add a feature to run all features after each other and create one finished and translated file.
- Add a separate Gui field for translation style additions.
- Add a way to add languages to the config file via an option "custom languages" in the dropdown menu.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Requirements

- Python 3.11+
- Poetry for dependency management
- OpenAI API key for translation services