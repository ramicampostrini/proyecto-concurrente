"""Benchmark: ejecución secuencial vs concurrente.
Se realizó este benchmark para comparar el rendimiento del sistema multiagente utilizando dos modos de ejecución: secuencial y concurrente. Se ejecutaron tres pruebas por modalidad sobre un mismo prompt, registrando los tiempos de ejecución de cada agente, el tiempo de la primera etapa y el tiempo total del pipeline.
Los resultados mostraron que la ejecución concurrente no produjo una mejora significativa en la primera etapa, debido principalmente a la competencia por los recursos de CPU durante la inferencia de los modelos locales. Si bien el tiempo promedio total fue menor en el modo concurrente, esta diferencia estuvo influenciada por la variabilidad en los tiempos de respuesta del agente de revisión.

Con esto se permite analizar el comportamiento del sistema y comparar ambas modalidades, destacando que la concurrencia no garantiza una reducción del tiempo total cuando los recursos de hardware son limitados.
Requiere el backend (uvicorn) y Ollama activos en diferentes terminales,Ademas una tercer consola para ejecutar este script. 
Uso, desde la carpeta backend:
    python benchmark.py --repeats 1 --prompts 1   # prueba rápida
    python benchmark.py --repeats 5 --prompts 2   # corrida completa
"""
import argparse
import csv
import json
import time
import hashlib
from datetime import datetime
from urllib import request as urlrequest

PROMPTS = [
    "Crear una funcion en Python que devuelva el promedio de una lista",
    "Crear una clase en Python que implemente una pila con push, pop, "
    "peek y verificacion de pila vacia, con manejo de errores",
]
AGENTS = ("resumen", "codigo", "revision")
POLL_SECONDS = 3
TIMEOUT_SECONDS = 900


def http_json(method, url, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urlrequest.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urlrequest.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_task(base_url, text, mode):
    created = http_json("POST", f"{base_url}/tasks", {"text": text, "mode": mode})
    task_id = created["id"]
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(POLL_SECONDS)
        task = http_json("GET", f"{base_url}/tasks/{task_id}")
        if task.get("status") in ("completada", "con errores"):
            return task
    raise TimeoutError(f"La tarea {task_id} no terminó en {TIMEOUT_SECONDS} s")


def build_row(run, prompt_id, mode, task):
    metrics = task.get("agent_metrics") or {}
    times = task.get("agent_elapsed_seconds") or {}
    row = {
        "run": run,
        "prompt_id": prompt_id,
        "mode": mode,
        "task_id": task.get("id"),
        "status": task.get("status"),
        "stage1_s": task.get("stage1_elapsed_seconds"),
        "pipeline_s": task.get("pipeline_elapsed_seconds"),
        "elapsed_s": task.get("elapsed_seconds"),
    }
    loads = []
    for agent in AGENTS:
        m = metrics.get(agent) or {}
        count, duration = m.get("eval_count"), m.get("eval_duration_s")
        row[f"{agent}_s"] = times.get(agent)
        text = (task.get("results") or {}).get(agent)
        row[f"{agent}_hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8] if text else None
        row[f"{agent}_eval_count"] = count
        row[f"{agent}_tok_s"] = round(count / duration, 2) if count and duration else None
        row[f"{agent}_load_s"] = m.get("load_duration_s")
        if m.get("load_duration_s") is not None:
            loads.append(m["load_duration_s"])
    row["cold_start"] = any(load > 1 for load in loads)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--prompts", type=int, default=2)
    args = parser.parse_args()

    prompts = PROMPTS[: args.prompts]
    filename = f"benchmark_{datetime.now():%Y%m%d_%H%M%S}.csv"

    print("Calentamiento (se descarta)...")
    warmup = run_task(args.base_url, prompts[0], "concurrent")
    if warmup.get("status") != "completada":
        raise SystemExit(
            f"El calentamiento falló: {warmup.get('errors')}. "
            "Verificá que Ollama esté activo."
        )

    run = 0
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = None
        for prompt_id, text in enumerate(prompts, start=1):
            for i in range(args.repeats):
                # Orden contrabalanceado: S,C / C,S / S,C ...
                order = ("sequential", "concurrent") if i % 2 == 0 else ("concurrent", "sequential")
                for mode in order:
                    run += 1
                    print(f"[{run}] prompt {prompt_id} | {mode} ...", flush=True)
                    task = run_task(args.base_url, text, mode)
                    if task.get("status") != "completada":
                        raise SystemExit(
                            f"La corrida {run} terminó con errores: "
                            f"{task.get('errors')}. Se detiene el benchmark."
                        )
                    row = build_row(run, prompt_id, mode, task)
                    if writer is None:
                        writer = csv.DictWriter(f, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    f.flush()
                    print(f"    {row['status']} | pipeline {row['pipeline_s']} s")
    print(f"Listo: {filename}")


if __name__ == "__main__":
    main()