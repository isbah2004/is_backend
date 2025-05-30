from PIL import Image
import numpy as np


def encode_image(image_data, payload: str) -> Image.Image:
    """
    Encode payload into image using LSB steganography
    image_data can be either a file path (str) or PIL Image object
    """
    if isinstance(image_data, str):
        img = Image.open(image_data)
    elif isinstance(image_data, Image.Image):
        img = image_data
    else:
        # Handle BytesIO or file-like objects
        img = Image.open(image_data)

    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')

    arr = np.array(img)

    # Convert payload to binary with length header
    bin_payload = ''.join(format(ord(c), '08b') for c in payload)
    bin_payload = format(len(bin_payload), '032b') + bin_payload

    # Validate capacity
    max_bits = arr.size  # Total pixels * channels
    if len(bin_payload) > max_bits:
        raise ValueError(f"Payload too large ({len(bin_payload)} > {max_bits} bits)")

    # Ensure we're working with uint8 data
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    # Embed in LSB with bounds checking
    flat = arr.flatten()
    for i, bit in enumerate(bin_payload):
        if i >= len(flat):
            break
        # Safely modify the LSB
        current_val = flat[i]
        new_val = (current_val & 0xFE) | int(bit)  # Clears LSB then sets it
        flat[i] = np.uint8(new_val)

    return Image.fromarray(flat.reshape(arr.shape))


def decode_image(image_data) -> str:
    """
    Decode payload from image using LSB steganography
    image_data can be either a file path (str) or PIL Image object
    """
    if isinstance(image_data, str):
        img = Image.open(image_data)
    elif isinstance(image_data, Image.Image):
        img = image_data
    else:
        # Handle BytesIO or file-like objects
        img = Image.open(image_data)

    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')

    arr = np.array(img)

    # Ensure uint8 data type
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    flat = arr.flatten()

    # Read payload length (first 32 bits)
    if len(flat) < 32:
        raise ValueError("Image too small to contain payload length header")

    length_bin = ''.join(str(flat[i] & 1) for i in range(32))
    length = int(length_bin, 2)

    # Validate length
    if length <= 0 or length > (len(flat) - 32):
        raise ValueError("Invalid payload length or corrupted data")

    # Extract payload
    payload_bin = ''.join(str(flat[i] & 1) for i in range(32, 32 + length))

    # Convert binary to string
    if len(payload_bin) % 8 != 0:
        raise ValueError("Invalid payload data")

    try:
        payload = ''.join(chr(int(payload_bin[i:i + 8], 2))
                          for i in range(0, len(payload_bin), 8))
    except ValueError as e:
        raise ValueError(f"Failed to decode payload: {e}")

    return payload