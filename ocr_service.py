import boto3
import io
from PIL import Image
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, S3_BUCKET_NAME

# Load OCR models
langs = ["en"]  # Replace with your languages - optional but recommended
det_processor, det_model = load_det_processor(), load_det_model()
rec_model, rec_processor = load_rec_model(), load_rec_processor()

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

def download_pdf_from_s3(s3_key: str):
    """
    Download PDF file from S3.
    """
    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
    return io.BytesIO(response["Body"].read())

def convert_pdf_to_images(pdf_stream):
    """
    Convert PDF to images using pdf2image.
    """
    # Convert PDF bytes to images (one image per page)
    images = convert_from_bytes(pdf_stream.getvalue(), dpi=300)
    return images

def perform_ocr_on_images(images, filename):
    """
    Perform OCR on a list of images using SuryaOCR.
    """
    ocr_results = []
    for idx, image in enumerate(images, start=1):
        predictions = run_ocr(
            [image], [langs], det_model, det_processor, rec_model, rec_processor, batch_size=1
        )
        # Combine all text lines into a single extracted_text field
        extracted_text = " ".join([text_line.text for text_line in predictions[0].text_lines])
        ocr_result = {
            "page_number": idx,
            "filename": filename,
            "extracted_text": extracted_text
        }
        ocr_results.append(ocr_result)
    return ocr_results
