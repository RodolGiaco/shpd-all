// src/components/SessionProgress.tsx
import React from "react";

interface Props {
  actual: number;
  total: number;
}

const SessionProgress: React.FC<Props> = ({ actual, total }) => {
  const porcentaje = Math.min((actual / total) * 100, 100);

  return (
    <div className="bg-white p-4 rounded-lg shadow-md">
      <h2 className="text-lg font-semibold mb-2">⏳ Progreso de la sesión</h2>
      <div className="w-full bg-gray-200 rounded-full h-4">
        <div
          className="bg-blue-500 h-4 rounded-full text-right pr-2"
          style={{ width: `${porcentaje}%` }}
        >
          <span className="text-xs text-white">{porcentaje.toFixed(1)}%</span>
        </div>
      </div>
      <p className="text-sm text-gray-600 mt-1">
        {actual}s de {total}s monitoreados
      </p>
    </div>
  );
};

export default SessionProgress;
