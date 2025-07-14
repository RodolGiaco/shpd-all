import React, { useState } from "react";
import CalibracionMonitor from "../components/CalibracionMonitor";
import { useLocation } from "react-router-dom";

const CalibracionPage: React.FC = () => {
  const [finalizado, setFinalizado] = useState(false);
  const location = useLocation();
  const force = new URLSearchParams(location.search).get("forceCalib") === "1";
  const calibrado = !force && localStorage.getItem("calibrado") === "1";

  return (
    <>
      {!finalizado && (
        <CalibracionMonitor
          onFinish={() => {
            localStorage.setItem("calibrado", "1");
            setFinalizado(true);
          }}
        />
      )}
      {/* El componente muestra su propio mensaje de éxito */}
    </>
  );
};

export default CalibracionPage; 