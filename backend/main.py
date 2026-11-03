import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4
import firebase_admin
import ollama
from firebase_admin import credentials, firestore
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# --------------------------------------------------
# 1. CONFIGURACIÓN Y LOGS
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
KEY_PATH = Path(
    os.getenv("FIREBASE_KEY", str(BASE_DIR / "serviceAccountKey.json"))
).expanduser()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)
# --------------------------------------------------
# 2. FIREBASE / FIRESTORE
# --------------------------------------------------
if not firebase_admin._apps:
    if not KEY_PATH.is_file():
        raise FileNotFoundError(
            f"No se encontró la clave de Firebase: {KEY_PATH}. "
            "Configurá FIREBASE_KEY o colocá serviceAccountKey.json "
            "en la carpeta backend."
        )

    cred = credentials.Certificate(str(KEY_PATH))
    firebase_admin.initialize_app(cred)

db = firestore.client()
tasks_collection = db.collection("tasks")

# --------------------------------------------------
# 3. EJECUTOR de la pool de hilos Y CICLO DE VIDA
# --------------------------------------------------
executor = ThreadPoolExecutor(
    max_workers=3,
    thread_name_prefix="agente-ia",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando API y ThreadPoolExecutor")
    try:
        yield
    finally:
        logger.info("Cerrando ThreadPoolExecutor")
        executor.shutdown(wait=True)
        logger.info("ThreadPoolExecutor cerrado")


app = FastAPI(
    title="Sistema Multiagente de generacion y analisis de codigo",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# 4. MODELO DE ENTRADA
# --------------------------------------------------
class TaskRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
# --------------------------------------------------
# 5. PROCESAMIENTO DE AGENTES
# --------------------------------------------------
def process_task(task_id: str):
    """Ejecuta los agentes y reduce las escrituras a Firestore."""

    referencia = tasks_collection.document(task_id)
    start = perf_counter()

    results = {}
    errors = {}
    agent_elapsed_seconds = {}

    def run_agent(name, function):
        agent_start = perf_counter()
        logger.info("Tarea %s: inicia agente %s", task_id, name)

        try:
            result = function()

            if not isinstance(result, str) or not result.strip():
                raise ValueError(
                    f"El agente {name} devolvió una respuesta vacía."
                )

            logger.info(
                "Tarea %s: agente %s finalizado", task_id, name
            )
            return result.strip()

        except Exception:
            logger.exception(
                "Tarea %s: error en agente %s", task_id, name
            )
            raise

        finally:
            duration = round(perf_counter() - agent_start, 3)
            agent_elapsed_seconds[name] = duration

            logger.info(
                "Tarea %s: agente %s tardó %.3f segundos",
                task_id,
                name,
                duration,
            )

    try:
        # 1. Obtener la tarea
        documento = referencia.get()

        if not documento.exists:
            logger.warning("La tarea %s no existe", task_id)
            return

        task_data = documento.to_dict()
        text_value = task_data["text"]

        # 2. Marcar el inicio
        referencia.update({
            "status": "procesando",
            "resultados_parciales": {},
            "results": {},
            "agent_elapsed_seconds": {},
            "errors": {},
        })

        logger.info("Tarea %s iniciada", task_id)
        # 3. Agente de resumen
        def summarize():
            response = ollama.generate(
                model="llama3.2:1b",
                prompt=(
                    "Resumí la solicitud, identificá su objetivo y requisitos. "
                    "Si pide código, describí qué debe hacer sin resolverlo. "
                    "No inventes información y señalá brevemente cualquier ambigüedad.\n\n"
                    f"Solicitud:\n{text_value}"
                ),
            )

            return response["response"]
        # 4. Agente de generación de código
        def generate_code():
            response = ollama.generate(
                model="qwen2.5-coder:1.5b",
                prompt=(
                    "Sos un programador Python. Generá código que "
                    "resuelva el siguiente requerimiento. "
                    "Incluí el código completo, imports necesarios "
                    "y comentarios útiles cuando corresponda. "
                    "No inventes requisitos ni agregues explicaciones. "
                    "Devolvé el código en un bloque Markdown.\n\n"
                    f"Requerimiento:\n{text_value}"
                ),
            )
            return response["response"]

        # 5. Ejecutar resumen y código en paralelo
        jobs = {
            "resumen": summarize,
            "codigo": generate_code,
        }

        futures = {
            executor.submit(run_agent, name, function): name
            for name, function in jobs.items()
        }

        for future in as_completed(futures):
            name = futures[future]

            try:
                results[name] = future.result()
            except Exception as exc:
                errors[name] = str(exc)

        # 6. Una escritura conjunta de los resultados parciales
        referencia.update({
            "resultados_parciales": results.copy(),
            "errors": errors.copy(),
            "agent_elapsed_seconds": agent_elapsed_seconds.copy(),
        })

        logger.info(
            "Tarea %s: resultados parciales guardados",
            task_id,
        )

        # 7. Revisar el código con Mistral
        if "codigo" in results:

            def review_code():
                prompt = f"""  Sos un revisor de codigo Python con criterio tecnico estricto.
                        Responde.

                        REQUERIMIENTO ORIGINAL:
                        {text_value}

                        CODIGO A REVISAR:
                        {results["codigo"]}
                        Indica:
                        1. Si el codigo cumple con el requerimiento.
                        2. Si hay errores , problemas de seguridad o malas prácticas.
                        3. Hasta 3 Sugerencias de mejora.
                        Se breve y objetivo.
                            """
                response = ollama.generate(
                    model="mistral:7b",
                    prompt=prompt,
                )
                return response["response"]

            try:
                results["revision"] = run_agent(
                    "revision", review_code
                )

            except Exception as exc:
                errors["revision"] = str(exc)

        else:
            errors["revision"] = (
                "No se pudo revisar el código porque falló "
                "su generación."
            )
        # 8. Guardar todo junto al finalizar.
        elapsed = round(perf_counter() - start, 3)
        final_status = "completada" if not errors else "con errores"
        referencia.update({
            "results": results.copy(),
            "resultados_parciales": results.copy(),
            "errors": errors.copy(),
            "agent_elapsed_seconds": agent_elapsed_seconds.copy(),
            "elapsed_seconds": elapsed,
            "status": final_status,
        })
        logger.info(
            "Tarea %s finalizada con estado '%s' en %.3f segundos",
            task_id,
            final_status,
            elapsed,
        )
    except Exception as exc:
        elapsed = round(perf_counter() - start, 3)
        logger.exception(
            "Error general al procesar la tarea %s", task_id
        )
        try:
            referencia.update({
                "status": "con errores",
                "errors": {
                    **errors,
                    "general": str(exc),
                },
                "results": results.copy(),
                "resultados_parciales": results.copy(),
                "agent_elapsed_seconds": agent_elapsed_seconds.copy(),
                "elapsed_seconds": elapsed,
            })
        except Exception:
            logger.exception(
                "No se pudo guardar el error final de la tarea %s",
                task_id,
            )
# --------------------------------------------------
# 6. ENDPOINTS
# --------------------------------------------------
@app.get("/stats")
def get_stats():
    try:
        documentos = tasks_collection.stream()

        total_tareas = 0
        completadas = 0
        con_errores = 0
        pendientes = 0
        procesando = 0

        tiempos = []

        # Acumuladores de tiempos individuales
        tiempos_agentes = {
            "resumen": [],
            "codigo": [],
            "revision": [],
        }

        for documento in documentos:
            tarea = documento.to_dict() or {}

            total_tareas += 1
            estado = tarea.get("status")

            if estado == "completada":
                completadas += 1
            elif estado == "con errores":
                con_errores += 1
            elif estado == "pendiente":
                pendientes += 1
            elif estado == "procesando":
                procesando += 1

            # Tiempo total de la tarea
            tiempo = tarea.get("elapsed_seconds")

            if (
                isinstance(tiempo, (int, float))
                and not isinstance(tiempo, bool)
                and tiempo >= 0
            ):
                tiempos.append(tiempo)

            # Tiempos individuales de los agentes
            agentes = tarea.get("agent_elapsed_seconds") or {}

            for nombre in tiempos_agentes:
                duracion = agentes.get(nombre)

                if (
                    isinstance(duracion, (int, float))
                    and not isinstance(duracion, bool)
                    and duracion >= 0
                ):
                    tiempos_agentes[nombre].append(duracion)

        tiempo_promedio = (
            round(sum(tiempos) / len(tiempos), 2)
            if tiempos
            else 0
        )

        promedios_agentes = {
            nombre: (
                round(sum(duraciones) / len(duraciones), 2)
                if duraciones
                else 0
            )
            for nombre, duraciones in tiempos_agentes.items()
        }

        return {
            "total_tareas": total_tareas,
            "completadas": completadas,
            "con_errores": con_errores,
            "pendientes": pendientes,
            "procesando": procesando,
            "tiempo_promedio": tiempo_promedio,
            "tiempos_promedio_agentes": promedios_agentes,
        }

    except Exception as exc:
        logger.exception("Error calculando las estadísticas")

        raise HTTPException(
            status_code=500,
            detail="No se pudieron calcular las estadísticas",
        ) from exc

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
        "agent_elapsed_seconds": {},
        "resultados_parciales": {},
    }

    try:
        tasks_collection.document(task_id).set(task_data)

    except Exception as exc:
        logger.exception("No se pudo crear la tarea en Firestore")

        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar la tarea en Firestore",
        ) from exc

    background_tasks.add_task(process_task, task_id)

    logger.info("Tarea %s creada", task_id)

    return {"id": task_id, "status": "pendiente"}
@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    try:
        documento = tasks_collection.document(task_id).get()

    except Exception as exc:
        logger.exception("Error consultando la tarea %s", task_id)

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
    try:
        referencia.set({
            "mensaje": "Conexión exitosa",
            "origen": "FastAPI",
        })

        documento = referencia.get()
        return {
            "ok": documento.exists,
            "datos": documento.to_dict(),
        }
    except Exception as exc:
        logger.exception("Error probando Firestore")

        raise HTTPException(
            status_code=500,
            detail="Falló la prueba de conexión con Firestore",
        ) from exc
