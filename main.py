from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from stego import encode_image, decode_image
import csv
import os
from datetime import datetime
from PIL import Image
import io
import base64

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_PATH = "logs/stego_log.csv"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Initialize log file with headers if it doesn't exist
if not os.path.exists(LOG_PATH):
    with open(LOG_PATH, "w", newline="") as log:
        writer = csv.writer(log)
        writer.writerow(["timestamp", "operation", "filename", "status"])


def log_event(operation: str, filename: str, success: bool):
    try:
        with open(LOG_PATH, "a", newline="") as log:
            writer = csv.writer(log)
            writer.writerow([
                datetime.now().isoformat(),
                operation,
                filename or "unknown",
                "Success" if success else "Failed"
            ])
    except Exception as e:
        print(f"Logging error: {e}")


@app.post("/encode")
async def encode(
        image: UploadFile = File(...),
        payload: str = Form(...)
):
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")

        # Validate payload
        if not payload or len(payload.strip()) == 0:
            raise HTTPException(400, "Payload cannot be empty")

        # Process image
        img_data = await image.read()

        # Reset file pointer and create PIL Image
        img_bytes = io.BytesIO(img_data)
        pil_image = Image.open(img_bytes)

        # Encode the payload
        encoded_img = encode_image(pil_image, payload)

        # Save result to bytes
        img_byte_arr = io.BytesIO()
        encoded_img.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        # Convert to base64 for JSON response
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

        log_event("ENCODE", image.filename, True)
        return {
            "success": True,
            "message": "Image encoded successfully",
            "image_base64": img_base64,
            "filename": f"encoded_{image.filename}"
        }

    except ValueError as ve:
        log_event("ENCODE", image.filename, False)
        raise HTTPException(400, f"Encoding error: {str(ve)}")
    except Exception as e:
        log_event("ENCODE", image.filename, False)
        raise HTTPException(500, f"Internal server error: {str(e)}")


@app.post("/decode")
async def decode(image: UploadFile = File(...)):
    try:
        # Validate file type
        if not image.content_type or not image.content_type.startswith('image/'):
            raise HTTPException(400, "File must be an image")

        # Process image
        img_data = await image.read()
        img_bytes = io.BytesIO(img_data)

        # Decode the payload
        payload = decode_image(img_bytes)

        log_event("DECODE", image.filename, True)
        return {
            "success": True,
            "payload": payload,
            "message": "Payload decoded successfully"
        }

    except ValueError as ve:
        log_event("DECODE", image.filename, False)
        raise HTTPException(400, f"Decoding error: {str(ve)}")
    except Exception as e:
        log_event("DECODE", image.filename, False)
        raise HTTPException(500, f"Internal server error: {str(e)}")


@app.get("/")
async def root():
    return {"message": "Steganography API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)