from fastapi import FastAPI, UploadFile, File
from rag_chain_model import generate_project_ideas
import shutil

app = FastAPI()

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    with open(f"data/documents/{file.filename}", "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": f"{file.filename} uploaded."}

@app.get("/generate")
def generate():
    return generate_project_ideas()
