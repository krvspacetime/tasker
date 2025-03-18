import re

# Initialize colorama
# init()


def strip_ansi_codes(text):
    ansi_escape = re.compile(r"\x1B\[[0-?9;]*[mK]")
    return ansi_escape.sub("", text)


def ansi_to_html(text):
    # Map ANSI codes to HTML styles
    ansi_mapping = {
        "\033[0m": "</span>",  # Reset
        "\033[1m": '<span style="font-weight: bold;">',  # Bold
        "\033[32m": '<span style="color: green;">',  # Green
        "\033[31m": '<span style="color: red;">',  # Red
        "\033[34m": '<span style="color: blue;">',  # Blue
        # Add more mappings as needed
    }

    for ansi_code, html_tag in ansi_mapping.items():
        text = text.replace(ansi_code, html_tag)

    return text
