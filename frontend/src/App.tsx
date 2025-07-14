// src/App.tsx
import React, { useEffect, useState } from "react";
import {
  SessionData,
  SessionProgressData,
  HistorialPosturalItem,
  Paciente,
  TimelineEntry,
} from "./types";
import PostureCard from "./components/PostureCard";
import SessionInfo from "./components/SessionInfo";
import HistoryChart from "./components/HistoryChart";
import Header from "./components/Header";
import SessionProgress from "./components/SessionProgress";
import PostureTimelineTable from "./components/PostureTimelineTable";

export default function App() {
  const [session, setSession] = useState<SessionData | null>(null);
  const [progress, setProgress] = useState<SessionProgressData | null>(null);
  const [paciente, setPaciente] = useState<Paciente | null>(null);
  const [deviceId, setDeviceId] = useState<string | null>(null);
  const [sessionEnded, setSessionEnded] = useState(false);

  // --- Historial Postural real desde backend ---
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);

  // Fetch timeline entries
  useEffect(() => {
    if (!session) return;

    const fetchTimeline = async () => {
      try {
        const res = await fetch(
          `http://${window.location.hostname}:8765/timeline/${session.id}`
        );
        const data: TimelineEntry[] = await res.json();
        setTimeline(data);
      } catch (err) {
        console.error("Error al obtener timeline:", err);
      }
    };

    fetchTimeline();
    const idInt = setInterval(fetchTimeline, 3000);
    return () => clearInterval(idInt);
  }, [session]);

  // 1) Obtener el device_id de la URL al cargar
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const id = params.get("device_id");
    if (id) {
      setDeviceId(id);
    } else {
      console.error("No se encontró 'device_id' en la URL.");
    }
  }, []);

  // 2) Obtener datos del paciente cuando el deviceId esté disponible
  useEffect(() => {
    if (!deviceId) return;

    (async () => {
      try {
        const res = await fetch(`http://${window.location.hostname}:8765/pacientes/${deviceId}`);
        if (!res.ok) {
          throw new Error(`Error al obtener paciente: ${res.statusText}`);
        }
        const data: Paciente = await res.json();
        setPaciente(data);
      } catch (err) {
        console.error(err);
      }
    })();
  }, [deviceId]);

  // 3) Obtener la sesión activa
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(
          `http://${window.location.hostname}:8765/sesiones/`
        );
        const sessions: SessionData[] = await res.json();
        if (sessions.length > 0) {
        const last = sessions[sessions.length - 1];
        setSession({
          id: last.id,
          intervalo_segundos: last.intervalo_segundos,
          modo: last.modo,
          tiempo_transcurrido: 0,
        });
        }
      } catch (err) {
        console.error("Error al obtener sesión:", err);
      }
    })();
  }, []);

  // 4) Polling de progreso desde Redis vía backend
  useEffect(() => {
    if (!session) return;

    // Cuando se inicia una nueva sesión, borro la marca de finalización
    if (deviceId) {
      localStorage.removeItem(`session_ended_${deviceId}`);
    }

    const interval = setInterval(async () => {
      try {
        const res = await fetch(
          `http://${window.location.hostname}:8765/sesiones/progress/${session.id}`
        );
        const data: SessionProgressData = await res.json();
        setProgress(data);
        if (data && data.elapsed >= data.intervalo_segundos) {
          setSessionEnded(true);
        }
      } catch (err) {
        console.error("Error al obtener progreso de sesión:", err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [session, deviceId]);

  // --- Evitar doble reporte usando localStorage ---
  useEffect(() => {
    if (sessionEnded && deviceId) {
      // Verifica si ya se envió el reporte
      if (localStorage.getItem(`session_ended_${deviceId}`) === "true") return;

      fetch(`http://${window.location.hostname}:8765/sesiones/end/${deviceId}`, {
        method: "POST",
      })
        .then(res => res.json())
        .then(data => {
          localStorage.setItem(`session_ended_${deviceId}`, "true");
          // Borra calibrado para forzar calibración en la próxima sesión
          localStorage.removeItem("calibrado");
          // Opcional: mostrar un toast o mensaje de éxito
          console.log("Sesión finalizada y reporte enviado:", data);
        })
        .catch(err => {
          // Opcional: mostrar un toast o mensaje de error
          console.error("Error al finalizar sesión:", err);
        });
    }
  }, [sessionEnded, deviceId]);

  if (sessionEnded) {
    const handleRestartSession = () => {
      if (!deviceId) return;
      // Borro cualquier marca y redirijo inmediatamente. El reinicio de backend se maneja en segundo plano.
      localStorage.removeItem(`session_ended_${deviceId}`);

      // Llamo al backend pero no bloqueo la navegación por la respuesta
      fetch(`http://${window.location.hostname}:8765/sesiones/reiniciar/${session?.id ?? ""}?device_id=${deviceId}`,
        { method: "POST" }
      ).catch(() => {/* silenciar error, se mostrará en próximo ciclo si falla */});

      window.location.href = `/calibracion?device_id=${deviceId}`;
    };
    return (
      <main className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-100 to-green-100 p-4">
        <div className="bg-white rounded-2xl shadow-2xl px-8 py-10 flex flex-col items-center max-w-md w-full animate-fade-in">
          <div className="text-6xl mb-4 animate-bounce">🎉</div>
          <h2 className="text-3xl font-extrabold text-green-700 mb-2 text-center">¡Sesión finalizada!</h2>
          <p className="text-gray-700 mb-6 text-center">
            ¡Felicitaciones por completar tu sesión de monitoreo postural!<br/>
            Puedes revisar tus métricas o iniciar una nueva sesión cuando lo desees.
          </p>
          <button
            className="px-8 py-3 bg-gradient-to-r from-blue-500 to-green-500 text-white rounded-full shadow-lg hover:scale-105 hover:from-green-500 hover:to-blue-500 transition-all duration-300 text-lg font-semibold focus:outline-none focus:ring-4 focus:ring-blue-200"
            onClick={handleRestartSession}
          >
            <span className="mr-2">🔄</span> Iniciar nueva sesión
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-100 p-4">
      <Header
        paciente={paciente}
        tiempoActual={new Date().toLocaleString()}
        estadoSesion={session?.modo ?? "—"}
      />

      {session && progress ? (
        <>
          <div className="my-4">
            <SessionProgress
              actual={progress.elapsed}
              total={progress.intervalo_segundos}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-4">
              <PostureCard sesionId={session.id} />
              <HistoryChart sesionId={session.id} />
            </div>
            <div className="space-y-4">
              <SessionInfo
                session={{
                  ...session,
                  tiempo_transcurrido: progress.elapsed,
                }}
              />
              <PostureTimelineTable data={timeline} />
            </div>
          </div>
        </>
      ) : (
        <p className="text-center p-4">Cargando configuración de sesión…</p>
      )}
    </main>
  );
}
