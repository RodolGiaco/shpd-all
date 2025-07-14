#!/bin/bash

echo "[SHPD] Finalizando configuración. Pasando a modo WiFi cliente..."

# (Opcional) Mover la configuración WiFi temporal a la ubicación final con sudo
if [ -f "/tmp/wpa_supplicant.conf.tmp" ]; then
    echo "[SHPD] ✍️  Añadiendo nueva configuración de red..."
    cat /tmp/wpa_supplicant.conf.tmp | sudo tee -a /etc/wpa_supplicant/wpa_supplicant.conf > /dev/null
    sudo rm /tmp/wpa_supplicant.conf.tmp
else
    echo "[SHPD] ⚠️  No se encontró el archivo de configuración WiFi temporal."
fi

# Apagar hotspot
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Reiniciar interfaz
sudo ip link set wlan0 down
sleep 2
sudo ip link set wlan0 up
sleep 1

# Conectarse a la nueva red
sudo wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
sleep 5

# Solicitar IP del router
sudo dhclient wlan0

# --- LIMPIEZA PARA ARRANQUE NORMAL ---
# 1. Eliminar configuración estática de wlan0 en /etc/dhcpcd.conf
sudo sed -i '/^interface wlan0$/,/^$/d' /etc/dhcpcd.conf

# 2. Deshabilitar servicios de hotspot para el arranque normal
sudo systemctl disable hostapd
sudo systemctl disable dnsmasq

# 3. Eliminar bandera de hotspot activo
rm -f /home/rodo/.hotspot_active

# Reiniciar
sudo reboot
