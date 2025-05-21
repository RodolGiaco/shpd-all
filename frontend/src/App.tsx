// src/App.tsx
import React, { useEffect, useState } from "react";
import { PosturaMessage, SessionData } from "./types";
import PostureCard from "./components/PostureCard";
import SessionInfo from "./components/SessionInfo";
import HistoryChart from "./components/HistoryChart";
import Header from "./components/Header";
import SessionProgress from "./components/SessionProgress";
import PostureTimelineTable from "./components/PostureTimelineTable";

export default function App() {
  const [data, setData] = useState<PosturaMessage | null>(null);
  const [elapsed, setElapsed] = useState<number>(0); // estado para simular tiempo

  const tablaResumen = [
    { timestamp: "00:01", postura: "sentado erguido", tiempo_mala_postura: 0 },
    { timestamp: "00:02", postura: "mentón en mano", tiempo_mala_postura: 15 },
    { timestamp: "00:03", postura: "slouching", tiempo_mala_postura: 45 },
    { timestamp: "00:04", postura: "inclinación hacia adelante", tiempo_mala_postura: 75 },
    { timestamp: "00:05", postura: "sentado erguido", tiempo_mala_postura: 0 },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      (async () => {
        try {
          // obtengo la sesión desde la BD
          const sesRes = await fetch(
            `http://${window.location.hostname}:8765/sesiones/`
          );
          const sessions: SessionData[] = await sesRes.json();
          const session = sessions[sessions.length - 1];

          // Reemplazo completo: actualizar elapsed y data juntos
          setElapsed(prev => {
            const next = Math.min(prev + 2, session.intervalo_segundos);

            // actualizo data usando el nuevo elapsed
            setData({
              timestamp: new Date().toISOString(),
              session: {
                ...session,
                tiempo_transcurrido: next, // uso el valor calculado
              },
              postura: {
                actual: "mentón en mano",
                transiciones_malas: Math.floor(Math.random() * 10),
                porcentaje_correcta: parseFloat(
                  (Math.random() * 100).toFixed(1)
                ),
                porcentaje_incorrecta: parseFloat(
                  (Math.random() * 100).toFixed(1)
                ),
                tiempo_parado: Math.floor(Math.random() * 200),
                tiempo_sentado: Math.floor(Math.random() * 500),
                alertas_enviadas: Math.floor(Math.random() * 5),
              },
               historial_postural: [
              { nombre: "sentado erguido", conteo: 68 },
              { nombre: "mentón en mano", conteo: 12 },
              { nombre: "slouching", conteo: 6 },
              { nombre: "inclinación hacia adelante", conteo: 3 },
            ],
            });

            return next;
          });
        } catch (err) {
          console.error("Error fetching session:", err);
        }
      })();
    }, 2000);

    return () => clearInterval(interval);
  }, []); // intervalo cada 2s

  return (
    <main className="min-h-screen bg-gray-100 p-4">
      <Header
        tiempoActual={new Date().toLocaleString()}
        estadoSesion="En curso"
      />

      {data ? (
        <>
          <div className="my-4">
            <SessionProgress
              actual={data.session.tiempo_transcurrido}
              total={data.session.intervalo_segundos}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-4">
              <PostureCard sesionId={data.session.id} />
              <HistoryChart historial={data.historial_postural} />
            </div>
            <div className="space-y-4">
              <SessionInfo session={data.session} />
              <PostureTimelineTable data={tablaResumen} />
            </div>
          </div>
        </>
      ) : (
        <p className="text-center p-4">Cargando datos de sesión…</p>
      )}
    </main>
  );
}
