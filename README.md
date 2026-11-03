Sistema Concurrente Multiagente con Inteligencia Artificial

Sistema desarrollado como proyecto académico para aplicar concurrencia mediante múltiples agentes de inteligencia artificial. Cuenta con una interfaz web, una API backend, persistencia en la nube y modelos de lenguaje ejecutados localmente.

El sistema permite enviar una tarea y distribuir su procesamiento entre distintos agentes especializados, coordinando su ejecución y almacenando los resultados.

Características principales
Procesamiento concurrente: los agentes independientes se ejecutan en hilos mediante ThreadPoolExecutor.
Arquitectura multiagente: cada modelo cumple una función específica.
Inteligencia artificial local: integración con modelos ejecutados mediante Ollama.
Procesamiento en segundo plano: la API responde de inmediato (HTTP 202) y la tarea continúa con BackgroundTasks.
Persistencia de datos: almacenamiento de tareas y resultados en Firebase Firestore.
Dashboard web: visualización del estado de las tareas, resultados y estadísticas, con actualización manual.
Métricas de tiempo: tiempo total de cada tarea y tiempo individual de cada agente.
Arquitectura del sistema

El proyecto está dividido en dos componentes principales:

Frontend: interfaz desarrollada con React y Vite.
Backend: API desarrollada con Python y FastAPI.

El backend coordina los agentes de IA, administra la ejecución de las tareas y almacena la información en Firestore.

Flujo de una tarea
El usuario envía un texto desde la interfaz web.
El backend genera un identificador único (uuid4), guarda la tarea en Firestore con estado pendiente y responde HTTP 202.
En segundo plano, el estado pasa a procesando y se ejecutan en paralelo el agente de resumen y el agente de código.
Con el código generado, el agente de revisión lo analiza.
Los resultados, los tiempos y el estado final (completada o con errores) se guardan en Firestore.
El frontend consulta el estado de la tarea hasta que termina.
Agentes de inteligencia artificial

El sistema utiliza tres modelos especializados:

Agente	Modelo	Responsabilidad
Resumen	llama3.2:1b	Generar un resumen del contenido recibido.
Código	qwen2.5-coder:1.5b	Generar soluciones en Python relacionadas con la solicitud.
Revisión	mistral:7b	Revisar el código generado por el agente de código y aportar observaciones.

Los agentes de resumen y código son independientes entre sí y se ejecutan concurrentemente. El agente de revisión depende del código generado, por lo que se ejecuta a continuación.

Concurrencia
ThreadPoolExecutor (máximo de tres trabajadores): ejecuta en hilos distintos el agente de resumen y el de código.
as_completed: recoge cada resultado apenas termina, sin imponer un orden.
BackgroundTasks de FastAPI: permite responder al cliente antes de que termine el procesamiento.
Cierre ordenado: al apagar el servidor, el pool espera a que terminen los hilos en curso.

Los hilos permanecen mayormente a la espera de la respuesta HTTP de Ollama, que es quien realiza el cómputo de los modelos en un proceso aparte. Por eso el beneficio real de la concurrencia depende del hardware y del servidor de modelos, y debe evaluarse de forma empírica.

Tecnologías utilizadas
Área	Tecnología
Lenguaje backend	Python
API	FastAPI
Concurrencia	ThreadPoolExecutor
Recolección de resultados	as_completed
Tareas en segundo plano	BackgroundTasks
Frontend	React
Herramienta de desarrollo frontend	Vite
Gráficos	Recharts
Base de datos	Firebase Firestore
Modelos de IA	Ollama
Control de versiones	Git y GitHub
Requisitos

Antes de ejecutar el proyecto, es necesario contar con:

Python 3.13 (versión del entorno probado).
Node.js 20.19 o superior en la rama 20, o 22.13 o superior, y npm.
Ollama instalado.
Acceso autorizado al proyecto Firebase/Firestore.
Git para clonar el repositorio.
Instalación y configuración
1. Clonar el repositorio
bash
git clone URL_DEL_REPOSITORIO
cd proyecto-concurrente

Reemplazá URL_DEL_REPOSITORIO por la dirección real del repositorio.

2. Configurar el backend

Desde la carpeta backend, crear y activar un entorno virtual e instalar las dependencias:

powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

Si usás Visual Studio Code, también podés seleccionar el intérprete de backend/.venv desde la paleta de comandos (Python: Select Interpreter) y abrir una terminal nueva.

3. Configurar Firebase

El backend utiliza Firebase Admin SDK para conectarse a Firestore.

Se requiere un archivo de credenciales de cuenta de servicio ubicado en:

text
backend/serviceAccountKey.json

Opcionalmente, la ruta puede indicarse con la variable de entorno FIREBASE_KEY.

Cada integrante debe obtener sus credenciales de manera segura y autorizada para el proyecto Firebase correspondiente.


4. Instalar y configurar Ollama

Instalar Ollama en el equipo donde se ejecutarán los modelos y descargar los modelos necesarios:

powershell
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:1.5b
ollama pull mistral:7b

Verificar que estén disponibles:

powershell
ollama list

El servidor de Ollama debe estar en ejecución mientras se usa el sistema (la aplicación de Ollama, o ollama serve en una terminal aparte). Si está apagado, las tareas terminan con estado con errores.

Nota: el archivo backend/.env.example lista los modelos previstos, pero actualmente los nombres de los modelos están definidos en main.py; la única variable de entorno que lee el backend es FIREBASE_KEY.

5. Iniciar el backend

Desde la carpeta backend, con el entorno virtual activado:

powershell
python -m uvicorn main:app --reload

La API estará disponible en:

http://127.0.0.1:8000

La documentación interactiva de FastAPI se encuentra en:

http://127.0.0.1:8000/docs

6. Iniciar el frontend

Abrir otra terminal y ejecutar:

powershell
cd frontend
npm install
npm run dev

La aplicación estará disponible habitualmente en:

http://localhost:5173

API
Método	Ruta	Descripción
GET	/	Verifica que la API esté funcionando.
POST	/tasks	Crea una tarea (cuerpo: { "text": "..." }) y devuelve su id.
GET	/tasks/{task_id}	Devuelve el estado y los resultados de una tarea.
GET	/stats	Devuelve estadísticas generales y tiempos promedio.
GET	/test-firestore	Prueba la conexión con Firestore.
Dashboard e indicadores de rendimiento

El dashboard permite consultar estadísticas generales del sistema y visualizar información sobre los agentes. Las estadísticas se actualizan con el botón Actualizar estadísticas, para evitar lecturas innecesarias a Firestore.

Entre los indicadores disponibles se encuentran:

Agente con menor tiempo de ejecución.
Agente con mayor tiempo de ejecución.
Ahorro teórico asociado a la ejecución concurrente.
Speedup estimado.
Eficiencia del tramo paralelo.

Los indicadores calculados a partir de tiempos promedio son estimaciones teóricas. No representan por sí solos una comparación experimental entre una ejecución completamente secuencial y otra concurrente.

Estructura del proyecto
text
proyecto-concurrente/
│
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── serviceAccountKey.json   (local, no se sube)
│   └── .venv/                   (local, no se sube)
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── package.json
│   ├── eslint.config.js
│   └── vite.config.js
│
├── .gitignore
└── README.md

Algunos elementos, como .venv, node_modules y serviceAccountKey.json, son locales y no deben incorporarse al repositorio.

Trabajo en equipo

Para colaborar en el proyecto:

Clonar el repositorio.
Instalar las dependencias del backend y del frontend.
Configurar las credenciales locales de Firebase.
Instalar Ollama y descargar los modelos requeridos.
Crear ramas para desarrollar nuevas funcionalidades.
Integrar los cambios mediante commits y pull requests.
Seguridad
No subir serviceAccountKey.json a GitHub.
No publicar claves privadas ni credenciales.
No subir carpetas .venv o node_modules.
No compartir archivos .env con información sensible.
Si una credencial se publica accidentalmente, revocarla y generar una nueva.
Conceder acceso a Firebase únicamente a integrantes autorizados.
El backend usa Firebase Admin SDK, que no está limitado por las reglas de seguridad de Firestore. Si se incorpora autenticación, el backend deberá verificar los tokens y controlar el acceso a cada tarea.
Objetivo académico

El objetivo del proyecto es demostrar la aplicación práctica de conceptos de concurrencia y coordinación de tareas, integrándolos con herramientas actuales de desarrollo web e inteligencia artificial.

Además, busca analizar cómo la ejecución concurrente de procesos independientes puede afectar los tiempos de procesamiento de una tarea.