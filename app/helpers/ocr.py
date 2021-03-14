from google.cloud import vision
import io

def detect_text(path):
    """Detects text in the file."""
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations

    content = ""
    list_text = []
    for text in texts:
        content += '{}'.format(text.description)
        list_text.append('{}'.format(text.description))
    
    return content, list_text
    
    if response.error.message:
        return response.error.message