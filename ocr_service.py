import boto3
import io
from PIL import Image
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
from dotenv import load_dotenv
import os
import httpx

# Load environment variables from .env file
load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")

# Load OCR models
langs = ["en"]  # Replace with your languages - optional but recommended
det_processor, det_model = load_det_processor(), load_det_model()
rec_model, rec_processor = load_rec_model(), load_rec_processor()

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

def download_pdf_from_s3(s3_key: str):
    """
    Download PDF file from S3.
    """
    try:
        response = s3_client.get_object(Bucket=AWS_BUCKET_NAME, Key=s3_key)
        return io.BytesIO(response["Body"].read())
    except Exception as e:
        raise Exception(f"Error downloading PDF from S3: {e}")

def convert_pdf_to_images(pdf_stream):
    """
    Convert PDF to images using pdf2image.
    """
    try:
        # Convert PDF bytes to images (one image per page)
        images = convert_from_bytes(pdf_stream.getvalue(), dpi=300)
        return images
    except Exception as e:
        raise Exception(f"Error converting PDF to images: {e}")

def perform_ocr_on_images(images, file_name):
    """
    Perform OCR on a list of images using SuryaOCR and include structured results with page numbers.
    """
    try:
        ocr_results = []
        for page_number, image in enumerate(images, start=1):  # Enumerate to get page number
            predictions = run_ocr(
                [image], [langs], det_model, det_processor, rec_model, rec_processor, batch_size=1
            )
            # Combine all text lines into a single string for this page
            page_text = " ".join([text_line.text for text_line in predictions[0].text_lines])
            # Append structured result for this page
            ocr_results.append({
                "image_name": file_name,
                "page_number": page_number,
                "text": page_text.strip()  # Strip extra spaces
            })
        return ocr_results
    except Exception as e:
        raise Exception(f"Error during OCR processing: {e}")




async def send_ocr_results(ocr_results):
    """
    Send OCR results and filename to an external endpoint.

    :param ocr_results: OCR data to send.
    :param filename: Name of the processed file.
    """

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://0.0.0.0:9010/store_data", json=ocr_results)
            if response.status == 200:
                print(f"Successfully sent OCR results for file")
            else:
                print(f"Failed to send OCR results for file")
        except httpx.RequestError as exc:
            print(f"An error occurred while sending OCR results: {exc}")
        except httpx.HTTPStatusError as exc:
            print(f"HTTP error occurred: {exc.response.status_code} - {exc.response.text}")
