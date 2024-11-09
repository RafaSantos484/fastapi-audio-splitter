import base64
import os
import shutil
import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from spleeter.separator import Separator

from app.utils import generate_random_id

app = FastAPI(title="Audio Splitter",
              description="API for splitting audio files into vocal and instrumental parts")

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def hello_world():
    return {"ok": True, "message": "Hello World!!!"}


@app.post("/")
async def upload_audio(file: UploadFile):
    id = generate_random_id()
    wav_filename = f"{id}.wav"
    try:
        with open(wav_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        print(e)
        return {"ok": False, "message": "Falha ao tentar salvar áudio"}

    try:
        separator = Separator("spleeter:2stems")
        separator.separate_to_file(wav_filename, "output")
    except Exception as e:
        print(e)
        return {"ok": False, "message": "Falha ao tentar separar áudio"}
    finally:
        os.remove(wav_filename)

    try:
        output_folder = os.path.join("output", id)
        vocal_path = os.path.join(output_folder, "vocals.wav")
        accompaniment_path = os.path.join(output_folder, "accompaniment.wav")
        with open(vocal_path, "rb") as vf:
            vocals_base64 = base64.b64encode(vf.read()).decode('utf-8')
        with open(accompaniment_path, "rb") as af:
            accompaniment_base64 = base64.b64encode(af.read()).decode('utf-8')
    except Exception as e:
        print(e)
        return {"ok": False, "message": "Falha ao tentar zipar áudio"}
    finally:
        shutil.rmtree(output_folder)

    # return FileResponse(zip_path, media_type="application/zip", filename=f"{id}.zip")
    return {"ok": True,
            "message": "Áudio processado com sucesso",
            "data": {
                "vocals_base64": f"data:audio/wav;base64,{vocals_base64}",
                "accompaniment_base64": f"data:audio/wav;base64,{accompaniment_base64}"
            }}


def run():
    uvicorn.run(app="app.index:app", host="0.0.0.0", port=8000)
