from setuptools import setup, find_packages

setup(
    name="slidemob",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "openai",
        "pydantic",
        "spellchecker",
        "langdetect",
    ],
    entry_points={
        'console_scripts': [
            'slidemob-gui=slidemob.gui.main:main',
        ],
    },
)