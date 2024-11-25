from fastapi import FastAPI, HTTPException
from ocr_service import download_pdf_from_s3, convert_pdf_to_images, perform_ocr_on_images
from models import PDFRequest

app = FastAPI()

@app.get("/") 
async def dummy():
    return {"message": "this is a dummy request"}

@app.post("/process-pdf")
async def process_pdf(request: PDFRequest):
    """
    Endpoint to process a PDF from S3 and perform OCR.
    """
    try:
        s3_key = request.s3_key
        # Step 1: Download PDF from S3
        pdf_stream = download_pdf_from_s3(s3_key)

        # Step 2: Extract images from the PDF
        images = convert_pdf_to_images(pdf_stream)
        if not images:
            raise HTTPException(status_code=400, detail="No images found in the PDF.")

        # Step 3: Perform OCR on the extracted images
        filename = s3_key.split("/")[-1]  # Extract filename from S3 key
        ocr_results = perform_ocr_on_images(images, filename)

        # Step 4: Return the OCR results
        return {"status": "success", "ocr_data": ocr_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
