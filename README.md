# Netz-NÖ SmartMeter-P1-Reader

Dieses Skript entschlüsselt Telegramme von der P1 Schnittstelle eines Sagemcom T210-D. Die Telegramme werden anschließend geparst und folgende Werte an einen MQTT-Broker gesendent:
- kWh in: Bezogene Energie in kWh (Gesamtwert)
- kWh out: Eingespeiste Energie in kWh (Gesamtwert)
- Power in: Aktueller Verbrauch in Watt
- Power out: Aktuelle Einspeisung in Watt

## Installation:
* Python libraries installieren (pip install -r requirements.txt)
* Konfigurationsparameter im .env-File eintragen

## Verwendete Hardware:
* BELTI USB-zu-MBUS-Slave-Modul (von Amazon)
* RJ12 Kabel
* Raspberry Pi

-------------
Für die Aufbereitung der Daten wird Hassio + Mossquito-Broker empfohlen
