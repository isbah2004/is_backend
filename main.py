from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from stego import encode_image, decode_image
import csv
import os
from datetime import datetime
from PIL import Image
import io

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


def log_event(operation: str, filename: str, success: bool):
    with open(LOG_PATH, "a", newline="") as log:
        writer = csv.writer(log)
        writer.writerow([
            datetime.now().isoformat(),
            operation,
            filename,
            "Success" if success else "Failed"
        ])


@app.post("/encode")
async def encode(
        image: UploadFile = File(...),
        payload: str = Form(...)
):
    try:
        # Process image
        img_data = await image.read()
        img = Image.open(io.BytesIO(img_data))
        encoded_img = encode_image(io.BytesIO(img_data), payload)

        # Save result
        img_byte_arr = io.BytesIO()
        encoded_img.save(img_byte_arr, format="PNG")

        log_event("ENCODE", image.filename, True)
        return {"image": img_byte_arr.getvalue()}
    except Exception as e:
        log_event("ENCODE", image.filename, False)
        raise HTTPException(400, str(e))


@app.post("/decode")
async def decode(image: UploadFile = File(...)):
    try:
        payload = decode_image(io.BytesIO(await image.read()))
        log_event("DECODE", image.filename, True)
        return {"payload": payload}
    except Exception as e:
        log_event("DECODE", image.filename, False)
        raise HTTPException(400, str(e))
