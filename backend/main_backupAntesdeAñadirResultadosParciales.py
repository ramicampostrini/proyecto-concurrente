from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from pathlib import Path
from uuid import uuid4
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = BASE_DIR / "serviceAccountKey.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(str(KEY_PATH))
    firebase_admin.initialize_app(cred)

db = firestore.client()
tasks_collection = db.collection("tasks")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
executor = ThreadPoolExecutor(max_workers=3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    executor.shutdown(wait=True)


app = FastAPI(
    title="Sistema Concurrente con IA",
    lifespan=lifespan,
)



class TaskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)




def process_task(task_id: str):
    """Ejecuta tareas con modelos locales de Ollama y guarda los resultados."""

    import ollama

    referencia = tasks_collection.document(task_id)
    documento = referencia.get()

    if not documento.exists:
        return

    task_data = documento.to_dict()
    text_value = task_data["text"]

    referencia.update({"status": "procesando"})
    start = perf_counter()

    results = {}
    errors = {}

    def summarize():
        response = ollama.generate(
            model="llama3.2:1b",
            prompt=(
                "Resumí el siguiente texto en español, de forma clara "
                "y breve:\n\n" + text_value
            ),
        )
        return response["response"]

    def generate_code():
        response = ollama.generate(
            model="qwen2.5-coder:1.5b",
            prompt=(
                "Analizá el siguiente requerimiento y generá una solución "
                "en Python. Incluí código claro y comentarios útiles. "
                "Devolvé solamente el código y no inventes requisitos.\n\n"
                "Requerimiento:\n" + text_value
            ),
        )
        return response["response"]

    # Fase 1: resumen y generación de código en paralelo.
    jobs = {
        "resumen": summarize,
        "codigo": generate_code,
    }

    futures = {
        executor.submit(function): name
        for name, function in jobs.items()
    }

    for future in as_completed(futures):
        name = futures[future]
        try:
            results[name] = future.result()
        except Exception as exc:
            errors[name] = str(exc)

    # Fase 2: el revisor analiza el código generado.
    if "codigo" in results:
        try:
            response = ollama.generate(
                model="mistral:7b",
                prompt=(
                    "Actuá como revisor de código Python. "
                    "Analizá el código, señalá errores potenciales, "
                    "problemas de seguridad y mejoras posibles. "
                    "No afirmes haber ejecutado el código.\n\n"
                    "Requerimiento original:\n"
                    + text_value
                    + "\n\nCódigo a revisar:\n"
                    + results["codigo"]
                ),
            )
            results["revision"] = response["response"]
        except Exception as exc:
            errors["revision"] = str(exc)
    else:
        errors["revision"] = (
            "No se pudo revisar el código porque falló su generación."
        )

    elapsed = round(perf_counter() - start, 3)

    referencia.update({
        "results": results,
        "errors": errors,
        "elapsed_seconds": elapsed,
        "status": "completada" if not errors else "con errores",
    })


@app.get("/")
def home():
    return {"message": "API concurrente funcionando"}


@app.post("/tasks", status_code=202)
def create_task(
    request: TaskRequest,
    background_tasks: BackgroundTasks,
):
    task_id = str(uuid4())

    task_data = {
        "id": task_id,
        "text": request.text,
        "status": "pendiente",
        "results": {},
        "errors": {},
        "elapsed_seconds": None,
    }

    try:
        tasks_collection.document(task_id).set(task_data)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar la tarea en Firestore",
        ) from exc

    background_tasks.add_task(process_task, task_id)

    return {"id": task_id, "status": "pendiente"}

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    try:
        documento = tasks_collection.document(task_id).get()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="No se pudo consultar Firestore",
        ) from exc

    if not documento.exists:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada",
        )

    return documento.to_dict()
@app.get("/test-firestore")
def test_firestore():
    referencia = db.collection("pruebas").document("conexion")

    referencia.set({
        "mensaje": "Conexión exitosa",
        "origen": "FastAPI"
    })

    documento = referencia.get()

    return {
        "ok": documento.exists,
        "datos": documento.to_dict()
    }