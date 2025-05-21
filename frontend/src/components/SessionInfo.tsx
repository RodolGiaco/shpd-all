// src/components/SessionInfo.tsx
import React from "react";
import { SessionData } from "../types";

interface Props {
  session: SessionData;
}

const SessionInfo: React.FC<Props> = ({ session }) => {
  return (
    <div className="p-4 bg-white rounded-lg shadow-md h-fit">
      <h2 className="text-xl font-semibold mb-2">🕒 Sesión</h2>
      <p>
        <strong>Modo:</strong> {session.modo}
      </p>
      <p>
        <strong>Intervalo total:</strong> {session.intervalo_segundos}s
      </p>
      <p>
        <strong>Tiempo transcurrido:</strong> {session.tiempo_transcurrido}s
      </p>
    </div>
  );
};

export default SessionInfo;
