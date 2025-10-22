from fastapi import FastAPI
from pydantic import BaseModel
from model import pipe

app = FastAPI()


class NERRequest(BaseModel):
    query: str


@app.post("/ner")
def func(request: NERRequest):
    result = pipe(request.query)
    return [
        {
            "entity": item["entity"],
            "score": float(item["score"]),
            "index": int(item["index"]) if "index" in item else None,
            "word": item["word"],
            "start": int(item["start"]) if "start" in item else None,
            "end": int(item["end"]) if "end" in item else None
        }
        for item in result
    ]