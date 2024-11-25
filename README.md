## Surya OCR FastAPI service

### Running server

to run the server, use the following command:

```
uvicorn main:app --reload
```

### Testing using CURL command

``` 
curl -X POST "http://127.0.0.1:8000/process-pdf" \
-H "Content-Type: application/json" \
-d '{"s3_key": "test.pdf"}'
```

Output: JSON