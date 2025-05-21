import { useEffect, useState } from 'react';

type Paciente = {
  nombre: string;
  edad: number;
  sexo: string;
  diagnostico: string;
};

type HeaderProps = {
  tiempoActual: string;
  estadoSesion: string;
};

export default function Header({ tiempoActual, estadoSesion }: HeaderProps) {
  const [paciente, setPaciente] = useState<Paciente | null>(null);

  useEffect(() => {
    fetch("http://192.168.194.122:8765/pacientes/")
      .then(res => res.json())
      .then(data => {
        setPaciente(data[0]); // solo el primer paciente por ahora
      });
  }, []);

  return (
    <div className="flex justify-between items-center p-4 border-b bg-white">
      <div>
        <h2 className="text-xl font-bold">Monitoreo Postural</h2>
        {paciente ? (
          <p>
            Paciente: <b>{paciente.nombre}</b> ({paciente.edad} años) – {paciente.diagnostico}
          </p>
        ) : (
          <p className="text-gray-500">Cargando paciente...</p>
        )}
      </div>
      <p className="text-sm text-gray-500 text-right">
        {tiempoActual} <br />
        <span className="text-blue-500">{estadoSesion}</span>
      </p>
    </div>
  );
}
