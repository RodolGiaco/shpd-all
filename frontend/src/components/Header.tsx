import { Paciente } from '../types'; // Importar el tipo centralizado

type HeaderProps = {
  paciente: Paciente | null; // Aceptar el paciente como prop
  tiempoActual: string;
  estadoSesion: string;
};

export default function Header({ paciente, tiempoActual, estadoSesion }: HeaderProps) {
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
