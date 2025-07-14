#!/bin/bash

CONFIG_FILE="/home/rodo/shpd.conf"
HOTSPOT_FLAG="/home/rodo/.hotspot_active"

echo "[SHPD] 🚀 Iniciando lógica de arranque..."

# Si no hay configuración del cliente, entramos en modo hotspot
if [ ! -f "$CONFIG_FILE" ]; then
  echo "[SHPD] ⚠️ No se encontró shpd.conf. Activando modo hotspot..."

  # Solo activa si no está ya activo (previene loops)
  if [ ! -f "$HOTSPOT_FLAG" ]; then
    touch "$HOTSPOT_FLAG"

    echo "[SHPD] 📶 Activando hotspot..."
    bash /home/rodo/enable_hostspot.sh
    sleep  3
   
    echo "[SHPD] 🛰️ Iniciando servidor de configuración..."
    sudo systemctl restart setup_server.service
    sudo systemctl start setup_server.service
  else
    echo "[SHPD] 🟡 Hotspot ya estaba activo anteriormente"
  fi

else
  echo "[SHPD] ✅ Configuración encontrada. Iniciando script de streaming..."
  source /home/rodo/shpd37/bin/activate
  python3 home/rodo/test_websocket.py
fi
