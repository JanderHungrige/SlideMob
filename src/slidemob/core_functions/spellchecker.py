from .base_class import PowerpointPipeline
import xml.etree.ElementTree as ET
import re
from spellchecker import SpellChecker


class SlideSpellChecker(PowerpointPipeline):
    def __init__(self, Further_SpellCheckInstructions):
        super().__init__()

        self.spell = SpellChecker()
        # Define namespaces used in PPTX XML
        self.namespaces = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
        }
        ET.register_namespace("a", self.namespaces["a"])
        ET.register_namespace("p", self.namespaces["p"])

    def check_and_fix_slide(self, xml_content):
        tree = ET.ElementTree(ET.fromstring(xml_content))
        root = tree.getroot()

        # Find all paragraphs
        for paragraph in root.findall(".//a:p", self.namespaces):
            self._process_paragraph(paragraph)

        return ET.tostring(root, encoding="unicode")

    def _process_paragraph(self, paragraph):
        runs = paragraph.findall("a:r", self.namespaces)
        i = 0
        while i < len(runs):
            current_run = runs[i]

            # Check if current run has error attribute
            if current_run.get("err") == "1":
                # Store original properties
                run_props = current_run.find("a:rPr", self.namespaces)

                # Collect text from this and adjacent runs
                combined_text = self._collect_adjacent_text(runs, i)

                # Fix spelling and update runs
                corrected_text = self._fix_spelling(combined_text)
                if corrected_text != combined_text:
                    self._update_runs_with_correction(
                        runs, i, corrected_text, run_props
                    )

                # Merge runs with identical properties
                self._merge_identical_runs(paragraph)

            # Check language consistency
            self._check_language_consistency(current_run)

            i += 1

    def _collect_adjacent_text(self, runs, start_index):
        """Collects text from adjacent runs that might be part of the same word"""
        text_parts = []
        i = start_index

        while i < len(runs):
            text_elem = runs[i].find("a:t", self.namespaces)
            if text_elem is not None:
                text_parts.append(text_elem.text)
            i += 1

            # Stop if we hit punctuation or clear word boundary
            if text_elem is not None and re.search(r"[.!?,\s]$", text_elem.text):
                break

        return "".join(text_parts)

    def _fix_spelling(self, text):
        words = text.split()
        corrected_words = []

        for word in words:
            if not self.spell.correction(word) == word:
                corrected_words.append(self.spell.correction(word))
            else:
                corrected_words.append(word)

        return " ".join(corrected_words)

    def _update_runs_with_correction(
        self, runs, start_index, corrected_text, original_props
    ):
        """Updates the runs with corrected text while maintaining formatting"""
        # Create new run with corrected text
        new_run = ET.Element("a:r")
        new_run.append(original_props)

        text_elem = ET.SubElement(new_run, "a:t")
        text_elem.text = corrected_text

        # Replace old runs with new corrected run
        parent = runs[start_index].getparent()
        parent.remove(runs[start_index])
        parent.insert(start_index, new_run)

    def _merge_identical_runs(self, paragraph):
        """Merges adjacent runs with identical properties"""
        runs = paragraph.findall("a:r", self.namespaces)
        i = 0

        while i < len(runs) - 1:
            current_run = runs[i]
            next_run = runs[i + 1]

            if self._runs_have_identical_props(current_run, next_run):
                # Merge text content
                current_text = current_run.find("a:t", self.namespaces).text
                next_text = next_run.find("a:t", self.namespaces).text
                current_run.find("a:t", self.namespaces).text = current_text + next_text

                # Remove the merged run
                paragraph.remove(next_run)
                runs = paragraph.findall("a:r", self.namespaces)
            else:
                i += 1

    def _runs_have_identical_props(self, run1, run2):
        """Checks if two runs have identical properties"""
        props1 = run1.find("a:rPr", self.namespaces)
        props2 = run2.find("a:rPr", self.namespaces)

        if props1 is None or props2 is None:
            return False

        # Compare relevant attributes
        attrs_to_compare = ["lang", "sz", "b", "i", "u"]
        return all(props1.get(attr) == props2.get(attr) for attr in attrs_to_compare)

    def _check_language_consistency(self, run):
        """Checks and fixes language consistency within a run"""
        run_props = run.find("a:rPr", self.namespaces)
        if run_props is not None and run_props.get("lang") is None:
            # Set default language if missing
            run_props.set("lang", "en-US")
