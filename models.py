from pydantic import BaseModel

class PDFRequest(BaseModel):
    s3_key: str