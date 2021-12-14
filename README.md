# Netz-NÖ SmartMeter-P1-Reader

https://www.netz-noe.at/Download-(1)/Smart-Meter/218_9_SmartMeter_Kundenschnittstelle_lektoriert_14.aspx

Dieses Skript entschlüsselt Telegramme (DLMS) von der P1 Schnittstelle eines Sagemcom T210-D. Die Telegramme werden anschließend geparst und folgende Werte an einen MQTT-Broker gesendent:
- kWh in: Bezogene Energie in kWh (Gesamtwert)
- kWh out: Eingespeiste Energie in kWh (Gesamtwert)
- Power in: Aktueller Verbrauch in Watt
- Power out: Aktuelle Einspeisung in Watt

## Installation:
* Python libraries installieren (pip install -r requirements.txt)
* Konfigurationsparameter im .env-File eintragen. Der KEY ist der Entschlüsselungskey, welcher von Netz-NÖ beantragt werden muss.
* Falls das Skript nicht als root ausgeführt wird: Anlegen der Datei "/var/log/decrypter.log" (Setzen der Rechte auf die Datei nicht vergessen).

Beispiel-Konfiguration:
```
PORT='/dev/ttyUSB0'
BAUD=2400
KEY=XXXXXXXXXXXXXXXXXXXXXXX
LOGLEVEL=WARNING
MQTT_USER=mqttuser
MQTT_PASS=mqttpassword
MQTT_HOST='192.168.0.666'
MQTT_PORT=1883
MQTT_TOPIC='/haus/smartmeter/vals'
```

## Run as a Service
- Folgende Datei anlegen: /etc/systemd/system/smart.service
- Den Parameter "ExecStart" auf die eigenen Pfade anpassen nicht vergessen!
 ```
 [Unit]
Description=Smart Meter Decrypter
Documentation=https://github.com/langi0815/Netz_NOE_SmartMeter_P1_Reader
After=networking.service
[Service]
Type=simple
User=pi
Group=pi
TimeoutStartSec=0
Restart=on-failure
RestartSec=30s
ExecStart=/usr/bin/python3 /home/pi/scripts/decrypter.py
[Install]
WantedBy=multi-user.target
 ```
 
 Danach folgende Befehle ausführen:
 - sudo systemctl enable smart
 - sudo systemctl start smart

## Verwendete Hardware:
* BELTI USB-zu-MBUS-Slave-Modul (von Amazon)
* RJ12 Kabel
* Raspberry Pi

-------------
Für die Aufbereitung der Daten wird Hassio + Mossquito-Broker empfohlen
