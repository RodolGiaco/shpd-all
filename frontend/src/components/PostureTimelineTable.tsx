// src/components/PostureTimelineTable.tsx
import React from "react";

interface TimelineEntry {
  timestamp: string;
  postura: string;
  tiempo_mala_postura: number; // en segundos
}

interface Props {
  data: TimelineEntry[];
}

const PostureTimelineTable: React.FC<Props> = ({ data }) => {
  return (
    <div className="bg-white p-4 rounded-lg border shadow-sm">
      <h2 className="text-lg font-semibold mb-2">🕒 Resumen de Actividad Postural</h2>
      <table className="min-w-full text-sm">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="py-2 px-3">Hora</th>
            <th className="py-2 px-3">Postura</th>
            <th className="py-2 px-3">Tiempo acumulado (s)</th>
          </tr>
        </thead>
        <tbody>
          {data.map((entry, i) => (
            <tr key={i} className="border-t">
              <td className="py-1 px-3">{entry.timestamp}</td>
              <td className="py-1 px-3">{entry.postura}</td>
              <td className={`py-1 px-3 ${entry.tiempo_mala_postura > 0 ? "text-rose-600 font-medium" : "text-gray-700"}`}>
                {entry.tiempo_mala_postura}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default PostureTimelineTable;
