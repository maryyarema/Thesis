import asyncio
import os
import uuid
import shutil
from fastapi import FastAPI, Form, UploadFile, File, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from .comfyui_client import send_upload_image, send_workflow_to_comfyui, send_workflow_to_comfyui_retry, send_workflow_to_comfyui_test

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
global_file_id = None
@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/tryon")
async def tryon(
    person: UploadFile = File(...), 
    cloth: UploadFile = File(...),
    cloth_type: str = Query('upper'),
    retry_catvton: bool = Query(True, description="Повторно запустити тільки CatVTON")
):
    max_attempts = 3
    attempt = 0
    last_exception = None

    while attempt < max_attempts:
        try:
            global global_file_id
            file_id=f"{person.filename}-{cloth.filename}"
            # Збереження файлів
            person_filename = f"{uuid.uuid4()}_{person.filename}"
            cloth_filename = f"{uuid.uuid4()}_{cloth.filename}"
            person_path = os.path.join(UPLOAD_DIR, person_filename)
            cloth_path = os.path.join(UPLOAD_DIR, cloth_filename)

            with open(person_path, "wb") as f:
                shutil.copyfileobj(person.file, f)
            with open(cloth_path, "wb") as f:
                shutil.copyfileobj(cloth.file, f)

            print(f"[INFO] Збережено зображення: {person_filename}, {cloth_filename}")

             # Повний workflow (сегментація + CatVTON)
            full_workflow = {
            "10": {"inputs": {"image": ""}, "class_type": "LoadImage", "_meta": {"title": "Target Person"}},
            "11": {"inputs": {"image": ""}, "class_type": "LoadImage", "_meta": {"title": "Reference Garment"}},
            "12": {"inputs": {"catvton_path": "zhengchong/CatVTON"}, "class_type": "LoadAutoMasker", "_meta": {"title": "Load AutoMask Generator"}},
            "13": {"inputs": {"cloth_type": "upper", "pipe": ["12", 0], "target_image": ["10", 0]}, "class_type": "AutoMasker", "_meta": {"title": "Auto Mask Generation"}},
            "14": {"inputs": {"images": ["13", 1]}, "class_type": "PreviewImage", "_meta": {"title": "Masked Target"}},
            "15": {"inputs": {"images": ["13", 0]}, "class_type": "PreviewImage", "_meta": {"title": "Binary Mask"}},
            "16": {
                "inputs": {
                    "seed": 42,
                    "steps": 50,
                    "cfg": 2.5,
                    "pipe": ["17", 0],
                    "target_image": ["10", 0],
                    "refer_image": ["11", 0],
                    "mask_image": ["13", 0]
                },
                "class_type": "CatVTON",
                "_meta": {"title": "TryOn by CatVTON"}
            },
            "17": {
                "inputs": {
                    "sd15_inpaint_path": "runwayml/stable-diffusion-inpainting",
                    "catvton_path": "zhengchong/CatVTON",
                    "mixed_precision": "bf16"
                },
                "class_type": "LoadCatVTONPipeline",
                "_meta": {"title": "Load CatVTON Pipeline"}
            },
            "18": {"inputs": {"images": ["16", 0]}, "class_type": "PreviewImage", "_meta": {"title": "Preview Image"}}
            }

            if True:
                global_file_id = file_id
                print("[INFO] Запуск повного флоу...")
                person_uploaded, cloth_uploaded = await send_upload_image(person_path, cloth_path)
                full_workflow["10"]["inputs"]["image"] = person_uploaded
                full_workflow["11"]["inputs"]["image"] = cloth_uploaded
                # Якщо потрібно, також підставте cloth_type у full_workflow:
                full_workflow["13"]["inputs"]["cloth_type"] = cloth_type
                await asyncio.sleep(15)
                # Запускаємо повний флоу
                img_bytes = await send_workflow_to_comfyui_test(full_workflow)
                print("[INFO] Отримано результат з ComfyUI.")
                return Response(content=img_bytes, media_type="image/png")
        except RuntimeError as e:
            if "Allocation on device" in str(e).lower():
                print(f"[INFO] OOM! Повторний запуск (спроба {attempt+1}/{max_attempts}) з тими ж зображеннями...")
                last_exception = e
                attempt += 1
                await asyncio.sleep(2)
                continue
            else:
                raise
    # Якщо всі спроби не вдалися
    print(f"[ERROR] OOM після {max_attempts} спроб: {last_exception}")
    return Response(content=f"Error: Out of GPU memory after {max_attempts} attempts.", status_code=507)
