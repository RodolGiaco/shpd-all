// src/components/HistoryChart.tsx
import React from "react";
import { HistorialPosturalItem } from "../types";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

interface Props {
  historial: HistorialPosturalItem[];
}

const POSTURAS_FIJAS = [
  "sentado erguido",
  "inclinación hacia adelante",
  "inclinación hacia atrás",
  "inclinación hacia la izquierda",
  "inclinación hacia la derecha",
  "mentón en mano",
  "piernas cruzadas",
  "rodillas elevadas o muy bajas",
  "hombros encogidos",
  "brazos sin apoyo",
  "cabeza adelantada",
  "slouching",
  "sentarse en el borde del asiento"
];

const HistoryChart: React.FC<Props> = ({ historial }) => {
  const data = POSTURAS_FIJAS.map((postura) => {
    const found = historial.find((item) => item.nombre === postura);

    return {
      postura,
      conteo: found ? found.conteo : 0,
    };
  });

  return (
    <div className="p-4 bg-white border rounded-lg shadow">
      <h2 className="text-lg font-bold mb-2">📊 Historial de Posturas</h2>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="postura" angle={-25} textAnchor="end" interval={0} height={70} />
          <YAxis />
          <Tooltip />
          <Bar dataKey="conteo" fill="#3b82f6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default HistoryChart;
