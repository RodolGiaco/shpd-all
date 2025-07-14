#!/bin/bash

set -e

echo "📡 [SHPD] Configurando hotspot WiFi temporal (SSID: SHPD_SETUP)..."

# Asegurar instalación de dependencias
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq

# Detener servicios previos
sudo systemctl stop hostapd || true
sudo systemctl stop dnsmasq || true

# Configuración estática para wlan0 si no existe
if ! grep -q "interface wlan0" /etc/dhcpcd.conf; then
  echo "🔧 Configurando IP estática para wlan0..."
  cat <<EOF | sudo tee -a /etc/dhcpcd.conf > /dev/null
interface wlan0
    static ip_address=10.0.0.1/24
    nohook wpa_supplicant
EOF
fi

sudo service dhcpcd restart

echo "🔧 Configurando dnsmasq..."
cat <<EOF | sudo tee /etc/dnsmasq.conf > /dev/null
interface=wlan0
dhcp-range=10.0.0.10,10.0.0.100,255.255.255.0,12h
EOF



echo "🔧 Configurando hostapd..."
cat <<EOF | sudo tee /etc/hostapd/hostapd.conf > /dev/null
interface=wlan0
driver=nl80211
ssid=SHPD_SETUP
hw_mode=g
channel=7
wmm_enabled=0
auth_algs=1
ignore_broadcast_ssid=0
EOF

sudo sed -i 's|^#DAEMON_CONF=.*|DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd

# Habilitar en el arranque
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

# Iniciar servicios de AP
sudo systemctl start hostapd
sudo systemctl start dnsmasq
sudo systemctl restart hostapd

sleep 10

sudo ip addr flush dev wlan0
sudo ip addr add 10.0.0.1/24 dev wlan0
sudo ip link set wlan0 up


echo "✅ Hotspot activo. SSID: SHPD_SETUP (IP: 10.0.0.1)"
