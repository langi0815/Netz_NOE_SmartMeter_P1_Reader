# Netz-NÖ SmartMeter-P1-Reader

https://www.netz-noe.at/Download-(1)/Smart-Meter/218_9_SmartMeter_Kundenschnittstelle_lektoriert_14.aspx

Dieses Skript entschlüsselt Telegramme (DLMS) von der P1 Schnittstelle eines Sagemcom T210-D. Die Telegramme werden anschließend geparst und folgende Werte an einen MQTT-Broker gesendent:
- kWh_in: Bezogene Energie in kWh (Gesamtwert)
- kWh_out: Eingespeiste Energie in kWh (Gesamtwert)
- pwr_in: Aktueller Verbrauch in Watt
- pwr_out: Aktuelle Einspeisung in Watt

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
- Die Parameter "ExecStart", "User" und "Group" anpassen nicht vergessen!
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

Mit folgendem Befehl kann überprüft werden, ob der Service ordnungsgemäß läuft:
- sudo systemctl status smart

Falls es Probleme gibt:
- sudo journalctl -u smart (nach unten scrollen nicht vergessen)

## Verwendete Hardware:
* BELTI USB-zu-MBUS-Slave-Modul (von Amazon)
* RJ12 Kabel
* Raspberry Pi

-------------
Für die Aufbereitung der Daten wird Hassio + Mossquito-Broker empfohlen

Beispielconfig der Sensoren (Hassio):
```
 - platform: mqtt
    state_topic: /home/smartmeter/vals
    name: SmartMeter_kWh_in
    value_template: "{{value_json.kWh_in}}"
    unit_of_measurement: "kWh"
    last_reset_topic: '/home/smartmeter/vals'
    last_reset_value_template: '1970-01-01T00:00:00+00:00'
    device_class: energy
    state_class: measurement
  - platform: mqtt
    state_topic: /home/smartmeter/vals
    name: SmartMeter_kWh_out
    value_template: "{{value_json.kWh_out}}"
    unit_of_measurement: "kWh"
    last_reset_topic: '/home/smartmeter/vals'
    last_reset_value_template: '1970-01-01T00:00:00+00:00'
    device_class: energy
    state_class: measurement
  - platform: mqtt
    state_topic: /home/smartmeter/vals
    name: SmartMeter_power_in
    value_template: "{{value_json.pwr_in}}"
    unit_of_measurement: "W"
    last_reset_topic: '/home/smartmeter/vals'
    last_reset_value_template: '1970-01-01T00:00:00+00:00'
    device_class: energy
    state_class: measurement
  - platform: mqtt
    state_topic: /home/smartmeter/vals
    name: SmartMeter_power_out
    value_template: "{{value_json.pwr_out}}"
    unit_of_measurement: "W"
    last_reset_topic: '/home/smartmeter/vals'
    last_reset_value_template: '1970-01-01T00:00:00+00:00'
    device_class: energy
    state_class: measurement
```
