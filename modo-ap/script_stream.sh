#!/bin/bash

# Ruta donde estás ejecutando mediamtx y el script
WORKDIR="$HOME/mediamtx_v1.12.2_linux_armv7"

# Nombre del pipe temporal
PIPE="$WORKDIR/stream.h264"

# Función para limpiar en salida
cleanup() {
  echo "🧹 Deteniendo procesos y limpiando..."
  pkill -f "libcamera-vid"
  pkill -f "ffmpeg.*$PIPE"
  rm -f "$PIPE"
  exit 0
}

# Crear pipe si no existe
if [[ ! -p "$PIPE" ]]; then
  echo "📎 Creando FIFO $PIPE..."
  mkfifo "$PIPE"
fi

# Arrancar mediamtx en background
echo "🚀 Iniciando servidor RTSP (mediamtx)..."
cd "$WORKDIR"
./mediamtx > mediamtx.log 2>&1 &
sleep 1

# Iniciar libcamera-vid (productor)
echo "🎥 Iniciando captura con libcamera-vid..."
libcamera-vid --nopreview -t 0 --width 640 --height 480 --framerate 15 \
              --codec h264 --inline -o "$PIPE" &

# Iniciar ffmpeg (consumidor y emisor RTSP)
echo "📡 Reenviando stream a RTSP con ffmpeg..."
ffmpeg -re -i "$PIPE" -f rtsp -rtsp_transport tcp rtsp://localhost:8554/stream

# Si se corta, limpiar
trap cleanup SIGINT SIGTERM
wait
