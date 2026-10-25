import { useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [text, setText] = useState("");
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submitTask(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setTask(null);

    try {
      const response = await fetch(`${API}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error("No se pudo crear la tarea");
      }

      const data = await response.json();
      await checkTask(data.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function checkTask(id) {
    for (let i = 0; i < 300; i++) {
      const response = await fetch(`${API}/tasks/${id}`);

      if (!response.ok) {
        throw new Error("No se pudo consultar la tarea");
      }

      const data = await response.json();
      setTask(data);

      if (
        data.status === "completada" ||
        data.status === "con errores"
      ) {
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    throw new Error("La consulta superó los dos minutos");
  }

  return (
    <main className="container">
      <h1>Procesador Concurrente con IA</h1>
      <p>Enviá un texto y observá cómo se procesan tres tareas.</p>

      <form onSubmit={submitTask}>
        <label htmlFor="text">Texto a procesar</label>

        <textarea
          id="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Escribí aquí tu solicitud..."
          required
          maxLength={10000}
        />

        <button disabled={loading || !text.trim()}>
          {loading ? "Procesando..." : "Iniciar procesamiento"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {task && (
        <section>
          <h2>Estado: {task.status}</h2>
          <p>ID: {task.id}</p>

          {task.elapsed_seconds != null && (
            <p>Tiempo total: {task.elapsed_seconds} segundos</p>
          )}

          {Object.entries(task.results || {}).map(([name, result]) => (
            <article key={name}>
              <h3>{name}</h3>
              <pre>{result}</pre>
            </article>
          ))}

          {Object.entries(task.errors || {}).map(([name, message]) => (
            <article key={name} className="error">
              <h3>Error en {name}</h3>
              <pre>{message}</pre>
            </article>
          ))}
        </section>
      )}
    </main>
  );
}

export default App;