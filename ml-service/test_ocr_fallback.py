from ml.ocr import extract_text_from_image

image_path = "test_data/graph.png"

text = extract_text_from_image(image_path)

print("OCR RESULT:")
print(text)
