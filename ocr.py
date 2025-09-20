import ddddocr
import sys
import base64
import requests
from io import BytesIO
from PIL import Image
import cairosvg
import re
import urllib.parse

# Initialize DdddOcr
ocr = ddddocr.DdddOcr(beta=True, show_ad=False)

# Function to check if input is a URL
def is_url(input_string):
    url_pattern = re.compile(
        r'^(https?://)?'  # http:// or https://
        r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,}|localhost)'  # domain
        r'(:[0-9]+)?'  # optional port
        r'(/.*)?$'  # optional path
    )
    return bool(url_pattern.match(input_string))

# Function to determine image format from base64 data URI or decoded data
def get_base64_format(base64_string):
    if not base64_string:
        print("Debug: Input base64 string is empty")
        return None
    # Handle URL-encoded strings
    base64_string = urllib.parse.unquote(base64_string)
    print(f"Debug: URL-decoded input (first 50 chars): {base64_string[:50]}")
    if base64_string.startswith("data:image/"):
        match = re.match(r'data:image/([a-zA-Z+]+);base64,', base64_string)
        if match:
            return match.group(1).lower()  # e.g., "svg+xml", "png", "jpeg"
    # Try to guess format by decoding and checking magic numbers
    try:
        decoded = base64.b64decode(base64_string, validate=True)
        print(f"Debug: Decoded data starts with: {decoded[:10].hex()}")
        print(f"Debug: Decoded data length: {len(decoded)} bytes")
        if decoded.startswith(b'\x89PNG'):
            return "png"
        elif decoded.startswith(b'\xff\xd8'):
            return "jpeg"
        elif decoded.startswith(b'<?xml') or decoded.startswith(b'<svg'):
            return "svg"
        else:
            print("Debug: Decoded data does not match known image formats")
            return "svg"  # Fallback to SVG for unknown formats
    except base64.binascii.Error as e:
        print(f"Debug: Base64 decode error: {e}")
        return None

# Function to process image and perform OCR
def process_image(image_data, image_format):
    if not image_data:
        print("Error: No image data provided")
        sys.exit(1)

    print(f"Debug: Processing image with format: {image_format}")
    # If SVG, convert to PNG
    if image_format in ["svg+xml", "svg"]:
        png_data = BytesIO()
        try:
            cairosvg.svg2png(bytestring=image_data, write_to=png_data)
            png_data.seek(0)
            if png_data.getbuffer().nbytes == 0:
                print("Error: SVG conversion produced empty PNG data")
                sys.exit(1)
            try:
                image = Image.open(png_data)
            except Exception as e:
                print(f"Error opening converted PNG: {e}")
                sys.exit(1)
        except Exception as e:
            print(f"Error converting SVG to PNG: {e}")
            sys.exit(1)
    else:
        # For PNG, JPG, etc., open directly
        try:
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            print(f"Error opening image: {e}")
            sys.exit(1)

    # Perform OCR
    try:
        res = ocr.classification(image)
        return res
    except Exception as e:
        print(f"Error during OCR: {e}")
        sys.exit(1)

# Get the input from command-line argument
print(f"Debug: Command-line arguments: {sys.argv}")
if len(sys.argv) < 2:
    print("Error: No input provided. Usage: python ocr.py <base64_string_or_url>")
    sys.exit(1)

input_string = sys.argv[1]
print(f"Debug: Input string (first 50 chars): {input_string[:50]}")
print(f"Debug: Input string length: {len(input_string)}")

# Process based on input type
if is_url(input_string):
    print("Debug: Processing as URL")
    try:
        response = requests.get(input_string, timeout=10)
        response.raise_for_status()
        image_data = response.content
        content_type = response.headers.get("content-type", "").lower()
        print(f"Debug: Content-Type: {content_type}")
        if "svg" in content_type:
            image_format = "svg"
        elif "png" in content_type:
            image_format = "png"
        elif "jpeg" in content_type or "jpg" in content_type:
            image_format = "jpeg"
        else:
            image_format = input_string.split('.')[-1].lower()
            if image_format not in ["png", "jpeg", "jpg", "svg"]:
                print(f"Unsupported image format: {image_format}")
                sys.exit(1)
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        sys.exit(1)
else:
    print("Debug: Processing as base64")
    image_format = get_base64_format(input_string)
    if image_format is None:
        print("Error: Invalid base64 string or unable to determine format")
        sys.exit(1)
    else:
        # Strip data URI prefix if present
        if input_string.startswith("data:image/"):
            input_string = input_string.split(",", 1)[1]
            print(f"Debug: Stripped base64 (first 50 chars): {input_string[:50]}")
        # Decode base64
        try:
            image_data = base64.b64decode(input_string, validate=True)
            print(f"Debug: Decoded data length: {len(image_data)} bytes")
        except base64.binascii.Error as e:
            print(f"Error decoding base64 string: {e}")
            sys.exit(1)

# Process the image and perform OCR
result = process_image(image_data, image_format)
print(result)
