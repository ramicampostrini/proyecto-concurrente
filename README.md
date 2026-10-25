# Proyecto Concurrente con IA

Proyecto académico con frontend React, backend FastAPI, persistencia en Firebase Firestore y modelos locales mediante Ollama.

> Estado actual: FastAPI y la persistencia de tareas en Firestore ya fueron probadas. Los trabajos `resumen`, `codigo` y `revision` todavía son simulaciones; falta conectarlos a modelos de IA reales.

## Requisitos

- Python 3.13 recomendado para el entorno probado.
- Node.js y npm para el frontend.
- Ollama instalado para ejecutar modelos de IA localmente.
- Acceso autorizado al proyecto Firebase/Firestore.

## Backend (Windows / PowerShell)

Desde la carpeta del proyecto:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Credenciales de Firebase

El backend actual espera el archivo de cuenta de servicio en:

`backend/serviceAccountKey.json`

Cada integrante que ejecute el backend localmente debe obtener credenciales de forma segura y autorizada para el proyecto Firebase. No envíen el archivo por GitHub, chat grupal ni lo agreguen al repositorio. El archivo está excluido en `.gitignore`.

Para iniciar la API, desde `backend`:

```powershell
python -m uvicorn main:app --reload
```

La documentación interactiva estará en:

http://127.0.0.1:8000/docs

## Ollama

Instalá Ollama en cada PC que vaya a ejecutar los modelos. Los modelos se descargan por separado; tener instalada la biblioteca Python `ollama` no los descarga automáticamente.

Modelos previstos:

```powershell
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:1.5b
ollama pull mistral:7b
```

Comprobar los modelos locales:

```powershell
ollama list
```

Si PowerShell no reconoce `ollama`, puede ser necesario usar la ruta completa del ejecutable de Ollama o corregir el PATH.

## Frontend

Desde otra terminal:

```powershell
cd frontend
npm install
npm run dev
```

La dirección habitual de Vite es:

http://localhost:5173

## Trabajo en equipo con GitHub

1. Clonen el repositorio.
2. Instalen las dependencias siguiendo estas instrucciones.
3. Configuren sus credenciales locales de Firebase de manera segura.
4. No suban `.venv`, `node_modules`, claves privadas ni archivos `.env` reales.
5. Trabajen en ramas y hagan pull requests si el equipo lo necesita.

## Seguridad

- Nunca subir `backend/serviceAccountKey.json`.
- No copiar credenciales privadas a este README, a issues o a commits.
- Si una clave privada se subió por accidente, revocarla y generar una nueva.
- Compartir acceso al proyecto Firebase solo con integrantes autorizados y con permisos mínimos necesarios.

## Estructura esperada

```text
proyecto-concurrente/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── serviceAccountKey.json   # local, no se sube
├── frontend/
├── .gitignore
└── README.md
```
