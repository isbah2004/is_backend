from PIL import Image
import numpy as np


def encode_image(image_path: str, payload: str) -> Image.Image:
    img = Image.open(image_path)
    arr = np.array(img)

    # Convert payload to binary + length header
    bin_payload = ''.join(format(ord(c), '08b') for c in payload)
    bin_payload = format(len(bin_payload), '032b') + bin_payload

    # Validate capacity
    max_bits = arr.size * 3  # 3 channels per pixel
    if len(bin_payload) > max_bits:
        raise ValueError(f"Payload too large ({len(bin_payload)} > {max_bits} bits)")

    # Embed in LSB
    flat = arr.flatten()
    for i, bit in enumerate(bin_payload):
        flat[i] = (flat[i] & ~1) | int(bit)

    return Image.fromarray(flat.reshape(arr.shape))


def decode_image(image_path: str) -> str:
    img = Image.open(image_path)
    arr = np.array(img)
    flat = arr.flatten()

    # Read payload length
    length_bin = ''.join(str(flat[i] & 1) for i in range(32))
    length = int(length_bin, 2)

    # Extract payload
    payload_bin = ''.join(str(flat[i] & 1) for i in range(32, 32 + length))
    payload = ''.join(chr(int(payload_bin[i:i + 8], 2))
                      for i in range(0, len(payload_bin), 8))

    return payload