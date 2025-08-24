from bs4 import BeautifulSoup


def generate_title_and_img_url(entryContent: str):
    soup = BeautifulSoup(entryContent, "html.parser")
    print("entryContent: ", entryContent)
    heading = soup.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    title = heading.get_text(strip=True) if heading else "Untitled"
    img = soup.find("img")
    url = img["src"] if img and img.has_attr("src") else None
    return_value={"content_title":title,"presigned_url":url}
    return return_value

def html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(" ", strip=True)