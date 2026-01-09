import re
from lxml import etree as ET

class MarkerUtils:
    @staticmethod
    def paragraph_to_marked_text(p_element, namespaces):
        """
        Converts an a:p element into a string with markers representing formatting.
        Example: "Hello <f1>World</f1>"
        Returns: (marked_text, run_properties_map)
        """
        marked_text = ""
        run_properties_map = {}
        marker_counter = 1

        # We need to iterate through children of a:p, which can be a:r, a:fld, a:br
        for child in p_element:
            tag = child.tag.split("}")[-1]
            
            if tag == "r":
                text_elem = child.find("a:t", namespaces)
                if text_elem is not None and text_elem.text:
                    rPr = child.find("a:rPr", namespaces)
                    if rPr is not None and len(rPr.attrib) > 0 or len(rPr) > 0:
                        # This run has formatting
                        marker_id = f"f{marker_counter}"
                        marker_counter += 1
                        run_properties_map[marker_id] = rPr
                        marked_text += f"<{marker_id}>{text_elem.text}</{marker_id}>"
                    else:
                        marked_text += text_elem.text
            elif tag == "br":
                marked_text += "\n"
            elif tag == "fld":
                # Fields (like page numbers) - handle as plain text for now or skip
                text_elem = child.find("a:t", namespaces)
                if text_elem is not None and text_elem.text:
                    marked_text += text_elem.text

        return marked_text, run_properties_map

    @staticmethod
    def marked_text_to_runs(marked_text, run_properties_map, namespaces):
        """
        Parses marked text and returns a list of a:r (and a:br) elements.
        """
        # Split by tags while keeping them
        parts = re.split(r"(<f\d+>.*?</f\d+>)", marked_text, flags=re.DOTALL | re.IGNORECASE)
        
        new_elements = []
        
        for part in parts:
            if not part:
                continue
                
            match = re.match(r"<(f\d+)>(.*?)</\1>", part, flags=re.DOTALL | re.IGNORECASE)
            if match:
                marker_id = match.group(1).lower()
                content = match.group(2)
                
                # Create a run element
                run = ET.Element("{http://schemas.openxmlformats.org/drawingml/2006/main}r")
                
                # Copy properties if they exist
                if marker_id in run_properties_map:
                    # We should probably clone the element
                    original_rPr = run_properties_map[marker_id]
                    run.append(ET.fromstring(ET.tostring(original_rPr)))
                
                text_elem = ET.SubElement(run, "{http://schemas.openxmlformats.org/drawingml/2006/main}t")
                text_elem.text = content
                new_elements.append(run)
            else:
                # Handle plain text - could contain newlines to convert back to a:br
                sub_parts = re.split(r"(\n)", part)
                for sub_part in sub_parts:
                    if sub_part == "\n":
                        new_elements.append(ET.Element("{http://schemas.openxmlformats.org/drawingml/2006/main}br"))
                    elif sub_part:
                        run = ET.Element("{http://schemas.openxmlformats.org/drawingml/2006/main}r")
                        text_elem = ET.SubElement(run, "{http://schemas.openxmlformats.org/drawingml/2006/main}t")
                        text_elem.text = sub_part
                        new_elements.append(run)
                        
        return new_elements
