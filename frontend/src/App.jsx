import { useEffect, useState } from "react";
import "./App.css";

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
const API = "http://127.0.0.1:8000";
const AGENT_LABELS = {
  resumen: "Llama 3.2 (resumen)",
  codigo: "Qwen 2.5 Coder (código)",
  revision: "Mistral 7B (revisión)",
};
function App() {
  const [text, setText] = useState("");
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stats, setStats] = useState(null);
  const [statsError, setStatsError] = useState("");
// Función para cargar las estadísticas desde el backend y manejar errores
  async function loadStats() {
    try {
      const response = await fetch(`${API}/stats`);

      if (!response.ok) {
        throw new Error("No se pudieron cargar las estadísticas");
      }

      const data = await response.json();
      setStats(data);
      setStatsError("");
    } catch (err) {
      setStatsError(
        err instanceof Error ? err.message : "Error al cargar estadísticas"
      );
    }
  }
  useEffect(() => {
    loadStats();
  }, []);
  
// Función para enviar la tarea al backend y manejar su estado desde la documentación de la API, incluyendo la espera de su finalización o error, y la actualización de las estadísticas.
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
      setError(
        err instanceof Error? err.message: "Ocurrió un error inesperado"
      );
    } finally {
      setLoading(false);
    }
  }
  // Consulta el estado de la tarea durante un máximo aproximado de 15 minutos.
  async function checkTask(id) {
    for (let i = 0; i < 180; i++) {
      const response = await fetch(`${API}/tasks/${id}`);

      if (!response.ok) {
        throw new Error("No se pudo consultar el estado de la tarea");
      }

      const data = await response.json();
      setTask(data);

      if (
        data.status === "completada" ||
        data.status === "con errores"
      ) {
        return;
      }

      await new Promise((resolve) => setTimeout(resolve, 5000));
    }

    throw new Error(
      "La consulta superó los quince minutos. La tarea podría seguir procesándose."
    );
  }
// Formatea el tiempo en segundos a un string con dos decimales y "s" al final
  function formatTime(seconds) {
    if (seconds == null || Number.isNaN(Number(seconds))) return "—";
    return `${Number(seconds).toFixed(2)} s`;
  }
  const agentData = stats?.tiempos_promedio_agentes
  ? [
      { agente: "Llama 3.2", segundos: Number(stats.tiempos_promedio_agentes.resumen) },
      { agente: "Qwen 2.5", segundos: Number(stats.tiempos_promedio_agentes.codigo) },
      { agente: "Mistral 7B", segundos: Number(stats.tiempos_promedio_agentes.revision) },
    ].filter((item) => Number.isFinite(item.segundos))
  : [];

  const fastestAgent =
    agentData.length > 0
      ? agentData.reduce((a, b) => a.segundos <= b.segundos ? a : b)
      : null;

  const slowestAgent =
    agentData.length > 0
      ? agentData.reduce((a, b) => a.segundos >= b.segundos ? a : b)
      : null;

  const llamaTime = agentData.find((a) => a.agente === "Llama 3.2")?.segundos;
  const qwenTime = agentData.find((a) => a.agente === "Qwen 2.5")?.segundos;
  const mistralTime = agentData.find((a) => a.agente === "Mistral 7B")?.segundos;

  const parallelData =llamaTime != null && qwenTime != null? [
                  { etapa: "Etapa paralela", segundos: Math.max(llamaTime, qwenTime) },
                  ...(mistralTime != null
                    ? [{ etapa: "Revisión secuencial", segundos: mistralTime }]
                    : []),
                ]
              : [];
// Tiempo que se ahorraría al ejecutar Llama y Qwen en paralelo
  const parallelSaving =llamaTime != null && qwenTime != null? Math.min(llamaTime, qwenTime): null;
// Porcentaje de ahorro de tiempo al ejecutar Llama y Qwen en paralelo
  const parallelSavingPercent =llamaTime != null && qwenTime != null && llamaTime + qwenTime > 0 ? (parallelSaving / (llamaTime + qwenTime)) * 100: null;
// Porcentaje de tiempo que representa Mistral 7B en el proceso total
  const mistralPercentOfProcess =llamaTime != null && qwenTime != null && mistralTime != null? (mistralTime / (Math.max(llamaTime, qwenTime) + mistralTime)) * 100: null;
// Comparación entre ejecución secuencial y concurrente
const sequentialTime =llamaTime != null && qwenTime != null && mistralTime != null? llamaTime + qwenTime + mistralTime: null;

const concurrentTime =llamaTime != null && qwenTime != null && mistralTime != null? Math.max(llamaTime, qwenTime) + mistralTime: null;
// Speedup: aceleración estimada por concurrencia
const speedup =sequentialTime != null && concurrentTime > 0? sequentialTime / concurrentTime: null;
// Eficiencia paralela: porcentaje de aprovechamiento de los agentes que trabajan simultáneamente
const parallelEfficiency =llamaTime != null &&qwenTime != null &&Math.max(llamaTime, qwenTime) > 0? ((llamaTime + qwenTime) / (2 * Math.max(llamaTime, qwenTime))) * 100: null;
// Renderizado del componente principal
  return (
    <main className="container">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">PANEL DE CONTROL</p>
          <h1>Sistema Multiagente de generación y análisis de código</h1>
          <p>
            Monitoreá las tareas procesadas y el rendimiento de los agentes
            de inteligencia artificial.
          </p>
        </div>
        <button className="refresh-button" onClick={loadStats}>
          Actualizar estadísticas
        </button>
      </header>
      <section className="stats-section">
        <h2>Resumen general</h2>
        {statsError && <p className="error">{statsError}</p>}
        <div className="stats-grid">
          <article className="stat-card">
            <span className="stat-label">Tareas procesadas</span>
            <strong>{stats?.total_tareas ?? "—"}</strong>
          </article>
          <article className="stat-card">
            <span className="stat-label">Completadas</span>
            <strong className="success-number">
              {stats?.completadas ?? "—"}
            </strong>
          </article>
          <article className="stat-card">
            <span className="stat-label">Con errores</span>
            <strong className="error-number">
              {stats?.con_errores ?? "—"}
            </strong>
          </article>
          <article className="stat-card">
            <span className="stat-label">Tiempo promedio</span>
            <strong>
              {stats ? formatTime(stats.tiempo_promedio) : "—"}
            </strong>
          </article>
        </div>
      </section>
  <section className="performance-section">
  <h2>Indicadores de rendimiento</h2>
  <div className="performance-grid">
    <article className="performance-card">
      <span>Agente más rápido</span>
      <strong>
        {fastestAgent
          ? `${fastestAgent.agente} · ${fastestAgent.segundos.toFixed(2)} s`
          : "Sin datos"}
      </strong>
      <p>Agente con menor tiempo promedio de ejecución.</p>
    </article>

    <article className="performance-card">
      <span>Agente que más tiempo consume</span>
      <strong>
        {slowestAgent? `${slowestAgent.agente} · ${slowestAgent.segundos.toFixed(2)} s`: "Sin datos"}
      </strong>
      <p>Agente con mayor tiempo promedio de ejecución.</p>
    </article>

    <article className="performance-card">
      <span>Ahorro teórico por concurrencia</span>
      <strong>
        {parallelSaving != null? `${parallelSaving.toFixed(2)} s`: "Sin datos"}
      </strong>
      <p>
      {parallelSavingPercent != null? `${parallelSavingPercent.toFixed(1)}% del tiempo combinado de Llama y Qwen. Estimación sobre promedios, no una medición.`: "Se necesitan datos de ambos agentes."}
    </p>
    </article>
    <article className="performance-card">
      <span>Speedup estimado</span>
      <strong>
        {speedup != null? `${speedup.toFixed(2)}x` : "Sin datos"}
      </strong>
      <p>
      Estimación calculada con tiempos promedio. No reemplaza una
      comparación medida entre ejecución secuencial y concurrente.
      </p>
    </article>
    <article className="performance-card">
      <span>Eficiencia Concurrente</span>
      <strong>
        {parallelEfficiency != null
          ? `${parallelEfficiency.toFixed(1)}%`
          : "Sin datos"}
      </strong>
      <p>
      <p>
      Estimación del aprovechamiento de los dos agentes que trabajan
      simultáneamente, calculada con promedios.
      </p>
      </p>
    </article>
  </div>
</section>
<section className="charts-section">
<h2>Análisis de rendimiento</h2>

<div className="charts-grid">
{/* Gráfico 1: tiempo promedio por agente */}
<article className="chart-card">
  <h3>Tiempo promedio por agente</h3>

  {stats && agentData.length > 0 ? (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={agentData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="agente" />
        <YAxis unit=" s" />
        <Tooltip
          formatter={(value) => `${Number(value).toFixed(2)} segundos`}
        />

        <Bar
          dataKey="segundos"
          name="Tiempo promedio"
          fill="#2459d3"
          radius={[6, 6, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  ) : (
    <p>No hay tiempos de agentes disponibles.</p>
  )}

  <p className="chart-note">
    {mistralPercentOfProcess != null
      ? `Mistral 7B representa el ${mistralPercentOfProcess.toFixed(1)}% del tiempo estimado total del proceso.`
      : "No hay datos suficientes para calcular la participación de Mistral."}
  </p>
</article>

  {/* Gráfico 2: tiempo por etapa de procesamiento */}
  <article className="chart-card">
    <h3>Tiempo por etapa de procesamiento</h3>

    {stats && parallelData.length > 0 ? (
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={parallelData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="etapa" />
          <YAxis unit=" s" />
          <Tooltip
            formatter={(value) => `${Number(value).toFixed(2)} segundos`}
          />

          <Bar
            dataKey="segundos"
            name="Tiempo de procesamiento"
            fill="#0d9488"
            radius={[6, 6, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    ) : (
      <p>No hay datos suficientes para comparar las etapas.</p>
    )}

    <p className="chart-note">
      La etapa paralela toma como referencia el mayor tiempo entre
      Llama 3.2 y Qwen 2.5, ya que ambos se ejecutan simultáneamente.
      La revisión de Mistral 7B se realiza posteriormente, de forma
      secuencial.
    </p>
  </article>
</div>
</section>
      <section className="agents-section">
        <h2>Agentes del sistema</h2>

        <div className="agents-grid">
          <article className="agent-card">
            <h3>Llama 3.2</h3>
            <p>Resumen analítico de la solicitud.</p>
            <span className="agent-role">Agente de resumen</span>
          </article>

          <article className="agent-card">
            <h3>Qwen 2.5 Coder</h3>
            <p>Generación del código solicitado.</p>
            <span className="agent-role">Agente de programación</span>
          </article>

          <article className="agent-card">
            <h3>Mistral 7B</h3>
            <p>Revisión, observaciones y mejoras.</p>
            <span className="agent-role">Agente auditor</span>
          </article>
        </div>
      </section>
      <section className="task-section">
        <h2>Nueva tarea</h2>
        <p>
          Enviá una solicitud para que los tres agentes procesen el contenido.
        </p>

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
      </section>
      {task && (
        <section className="results-section">
          <h2>Resultado de la tarea</h2>

          <article>
            <h3>Estado: {task.status}</h3>
            <p>ID: {task.id}</p>

            {task.elapsed_seconds != null && (
              <p>Tiempo total: {formatTime(task.elapsed_seconds)}</p>
            )}
          </article>

          {Object.entries(
            task.resultados_parciales || task.results || {}
          ).map(([name, result]) => (
            <article key={name}>
              <h3>
                {name === "resumen"
                  ? "Resumen (Llama 3.2)"
                  : name === "codigo"
                  ? "Código generado (Qwen 2.5 Coder)"
                  : name === "revision"
                  ? "Revisión (Mistral 7B)"
                  : name}
              </h3>
              <pre>{result}</pre>
            </article>
          ))}

          <h2>Tiempos de ejecución</h2>

          {Object.entries(task.agent_elapsed_seconds || {}).map(
            ([name, seconds]) => (
              <p key={name}>
                Tiempo de {AGENT_LABELS[name] ?? name}: {formatTime(seconds)}
              </p>
            )
          )}

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
