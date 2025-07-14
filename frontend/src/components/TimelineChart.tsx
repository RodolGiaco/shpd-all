// src/components/TimelineChart.tsx
import React from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell
} from "recharts";

interface TimelineEntry {
  timestamp: string;
  postura: string;
}

const COLOR_MAP: Record<string, string> = {
  "sentado erguido": "#22c55e",
  "slouching": "#f43f5e",
  "mentón en mano": "#facc15",
  "inclinación hacia adelante": "#f97316",
  "inclinación hacia atrás": "#38bdf8",
  "inclinación hacia la izquierda": "#a855f7",
  "inclinación hacia la derecha": "#10b981",
  "cabeza adelantada": "#f87171",
  "piernas cruzadas": "#e879f9",
  "hombros encogidos": "#60a5fa",
  "brazos sin apoyo": "#fb7185",
  "rodillas elevadas o muy bajas": "#fcd34d",
  "sentado al borde del asiento": "#f472b6"
};

interface Props {
  data: TimelineEntry[];
}

const TimelineChart: React.FC<Props> = ({ data }) => {
  return (
    <div className="p-4 bg-white border rounded-lg shadow mt-4">
      <h2 className="text-lg font-bold mb-2">🕒 Resumen Temporal de Actividad</h2>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ left: 30 }}>
          <XAxis type="number" hide domain={[0, 1]} />
          <YAxis type="category" dataKey="timestamp" width={60} />
          <Tooltip formatter={(value: any, name, props: any) => [props.payload.postura, "Postura"]} />
          <Bar dataKey={() => 1}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLOR_MAP[entry.postura] || "#a3a3a3"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TimelineChart;
