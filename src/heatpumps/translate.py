import re
from googletrans import Translator

translator = Translator()


def translate_text(text):
    """Translates German text to English while keeping code intact."""
    return translator.translate(text, src="de", dest="en").text


def translate_st_write(file_path, output_path):
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    translated_lines = []
    inside_st_write = False
    text_to_translate = ""
    indent = ""

    for line in lines:
        stripped_line = line.strip()

        # Detect the start of `st.write()`
        if stripped_line.startswith("st.write("):
            inside_st_write = True
            indent = line[: line.index("st.write")]  # Capture indentation
            text_to_translate = stripped_line[
                9:
            ]  # Extract the content after `st.write(`

            if text_to_translate.endswith(")") and not text_to_translate.startswith(
                ('"""', "'''")
            ):
                # Single-line case
                text_to_translate = text_to_translate[:-1]  # Remove closing `)`
                translated_text = translate_text(text_to_translate)
                translated_lines.append(f'{indent}st.write("{translated_text}")\n')
                inside_st_write = False
            else:
                translated_lines.append(line)  # Keep the original opening line
            continue

        # Handle multi-line cases
        if inside_st_write:
            text_to_translate += " " + stripped_line  # Append the next line content
            if stripped_line.endswith(('"""', "'''", ")")):
                inside_st_write = False  # End multi-line block
                translated_text = translate_text(text_to_translate)
                translated_lines.append(f'{indent}st.write("""{translated_text}""")\n')
            continue

        translated_lines.append(line)  # Keep other lines unchanged

    with open(output_path, "w", encoding="utf-8") as file:
        file.writelines(translated_lines)

    print(f"Translated file saved as {output_path}")


# Paths to the original and translated file
input_file = "hp_dashboard.py"  # Your original file
output_file = "hp_dashboard_translated.py"

translate_st_write(input_file, output_file)
