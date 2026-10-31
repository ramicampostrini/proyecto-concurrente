# Sistema Concurrente Multiagente con Inteligencia Artificial

Sistema desarrollado como proyecto académico para aplicar **concurrencia y procesamiento paralelo** mediante múltiples agentes de inteligencia artificial. Cuenta con una interfaz web, una API backend, persistencia en la nube y modelos de lenguaje ejecutados localmente.

El sistema permite enviar una tarea y distribuir su procesamiento entre distintos agentes especializados, coordinando su ejecución y almacenando los resultados.

## Características principales

- **Procesamiento concurrente:** ejecución paralela de agentes mediante `ThreadPoolExecutor`.
- **Arquitectura multiagente:** cada modelo cumple una función específica.
- **Inteligencia artificial local:** integración con modelos ejecutados mediante Ollama.
- **Persistencia de datos:** almacenamiento de tareas y resultados en Firebase Firestore.
- **Dashboard web:** visualización del estado de las tareas, resultados y estadísticas.
- **Métricas de rendimiento:** indicadores de tiempos de ejecución, velocidad relativa y eficiencia paralela estimada.

## Arquitectura del sistema

El proyecto está dividido en dos componentes principales:

- **Frontend:** interfaz desarrollada con React y Vite.
- **Backend:** API desarrollada con Python y FastAPI.

El backend coordina los agentes de IA, administra la ejecución de las tareas y almacena la información en Firestore.

## Agentes de inteligencia artificial

El sistema utiliza tres modelos especializados:

| Agente | Modelo | Responsabilidad |
| Resumen | `llama3.2:1b` | Generar un resumen del contenido recibido. |
| Código | `qwen2.5-coder:1.5b` | Analizar y generar soluciones relacionadas con código. |
| Revisión | `mistral:7b` | Revisar los resultados y aportar observaciones. |

Los agentes de resumen y código se ejecutan concurrentemente. Posteriormente, el agente de revisión procesa los resultados.

## Tecnologías utilizadas

| Área | Tecnología |
| Lenguaje backend | Python |
| API | FastAPI |
| Concurrencia | ThreadPoolExecutor |
| Sincronización | Lock |
| Tareas en segundo plano | BackgroundTasks |
| Frontend | React |
| Herramienta de desarrollo frontend | Vite |
| Gráficos | Recharts |
| Base de datos | Firebase Firestore |
| Modelos de IA | Ollama |
| Control de versiones | Git y GitHub |

## Requisitos

Antes de ejecutar el proyecto, es necesario contar con:

- Python 3.13 recomendado para el entorno probado.
- Node.js(version con la seguridad adecuada) y npm.
- Ollama instalado.
- Acceso autorizado al proyecto Firebase/Firestore.
- Git para clonar el repositorio.

## Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone URL_DEL_REPOSITORIO
cd proyecto-concurrente
```

Reemplazá `URL_DEL_REPOSITORIO` por la dirección real del repositorio.

### 2. Configurar el backend

Abrir la carpeta del proyecto en Visual Studio Code. Si el entorno virtual `.venv` está configurado y seleccionado como intérprete de Python, VS Code puede activarlo automáticamente al abrir una terminal.

Instalar las dependencias desde la terminal integrada:

```powershell
python -m pip install -r requirements.txt
```
Si VS Code no activa automáticamente el entorno virtual, seleccionar el intérprete de Python correspondiente a `backend/.venv` desde la paleta de comandos (`Python: Select Interpreter`) y abrir una nueva terminal.
### 3. Configurar Firebase

El backend utiliza Firebase Admin SDK para conectarse a Firestore.

Se requiere un archivo de credenciales de cuenta de servicio ubicado en:

```text
backend/serviceAccountKey.json
```

Cada integrante debe obtener sus credenciales de manera segura y autorizada para el proyecto Firebase correspondiente.

**Importante:** este archivo contiene información privada y no debe subirse al repositorio ni compartirse públicamente.

### 4. Instalar y configurar Ollama

Instalar Ollama en el equipo donde se ejecutarán los modelos.

Descargar los modelos necesarios:

```powershell
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:1.5b
ollama pull mistral:7b
```

Verificar que estén disponibles:

```powershell
ollama list
```

Los modelos se descargan localmente y deben estar disponibles para que el backend pueda utilizarlos.

### 5. Iniciar el backend

Desde la carpeta `backend`, con el entorno virtual activado:

```powershell
python -m uvicorn main:app --reload
```

La API estará disponible en:

http://127.0.0.1:8000

La documentación interactiva de FastAPI se encuentra en:

http://127.0.0.1:8000/docs

### 6. Iniciar el frontend

Abrir otra terminal y ejecutar:

```powershell
cd frontend
npm install
npm run dev
```

La aplicación estará disponible habitualmente en:

http://localhost:5173

## Dashboard e indicadores de rendimiento

El dashboard permite consultar estadísticas generales del sistema y visualizar información sobre los agentes.

Entre los indicadores disponibles se encuentran:

- Agente con menor tiempo de ejecución.
- Agente con mayor tiempo de ejecución.
- Ahorro teórico asociado a la ejecución concurrente.
- Speedup estimado.
- Eficiencia del tramo paralelo.

Los indicadores calculados a partir de tiempos promedio son estimaciones teóricas. No representan por sí solos una comparación experimental entre una ejecución completamente secuencial y otra concurrente.

## Estructura del proyecto

```text
proyecto-concurrente/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── serviceAccountKey.json
│   └── .venv/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
│
├── .gitignore
└── README.md
```

Algunos elementos de la estructura, como `.venv`, `node_modules` y `serviceAccountKey.json`, son locales y no deben incorporarse al repositorio.

## Trabajo en equipo

Para colaborar en el proyecto:

1. Clonar el repositorio.
2. Instalar las dependencias del backend y frontend.
3. Configurar las credenciales locales de Firebase.
4. Instalar Ollama y descargar los modelos requeridos.
5. Crear ramas para desarrollar nuevas funcionalidades.
6. Integrar los cambios mediante commits y pull requests.

## Seguridad

- No subir `serviceAccountKey.json` a GitHub.
- No publicar claves privadas ni credenciales.
- No subir carpetas `.venv` o `node_modules`.
- No compartir archivos `.env` con información sensible.
- Si una credencial se publica accidentalmente, revocarla y generar una nueva.
- Conceder acceso a Firebase únicamente a integrantes autorizados.

## Objetivo académico

El objetivo del proyecto es demostrar la aplicación práctica de conceptos de **concurrencia, paralelismo, sincronización y coordinación de tareas**, integrándolos con herramientas actuales de desarrollo web e inteligencia artificial.

Además, busca analizar cómo la ejecución concurrente de procesos especializados puede mejorar el aprovechamiento de los recursos y reducir los tiempos de procesamiento.