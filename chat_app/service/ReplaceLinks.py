import re
import uuid  # Example: Generates a random token (modify as needed)
from service.GenerateRenderLinks import getKaasLink


def extract_markdown_links(markdown_text):
    """
    Extracts all hyperlinks from Markdown content.

    Args:
    - markdown_text (str): The Markdown content as a string.

    Returns:
    - List of tuples: [(link_text, url), ...]
    """

    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'  # Regex to match [text](URL)
    links = re.findall(pattern, markdown_text)
    return links


def update_markdown_links(content, token):
    """
    Updates Markdown links by replacing multiple old URLs with new URLs containing dynamic tokens.

    """
    # Read the Markdown file
    url_mappings={}
    for text, url in extract_markdown_links(content):
        url_mappings[url] = getKaasLink(url,token)

    for old_url, new_url in url_mappings.items():
        # Generate a new token for each URL replacement


        # Regex pattern to match Markdown links: [text](old_url)
        pattern = rf'(\[.*?\])\({re.escape(old_url)}\)'

        # Replace old URL with new URL (containing the token)
        content = re.sub(pattern, rf'\1({new_url})', content)

        print(f"Updated {old_url} → {new_url}")

    # Write back the updated content
    return content




