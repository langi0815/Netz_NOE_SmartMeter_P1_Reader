#!/usr/bin env python3

'''
V0.1, 2021-12-14

Etschlüsselung und Aufbereitung von Smart Meter Telegrammen:
* Smart Meter: Sagemcom Drehstromzähler T210-D
* Netzbetreiber: Netz NÖ

Für die Verwendung des Skripts muss der Entschlüsselungs-Key
vom smartmeter@netz-noe.at angefordert werden.
'''

import serial
import binascii as ba
import os
import logging
import paho.mqtt.publish as mp
from Cryptodome.Cipher import AES
from gurux_dlms import *
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

# Conifg-Patameter aus .env auslesen
PORT = os.getenv('PORT')
BAUD = os.getenv('BAUD')
KEY = ba.unhexlify(os.getenv('KEY'))
LOGLEVEL = os.getenv('LOGLEVEL')

MQTT_USER = os.getenv('MQTT_USER')
MQTT_PASS = os.getenv('MQTT_PASS')
MQTT_HOST = os.getenv('MQTT_HOST')
MQTT_PORT = int(os.getenv('MQTT_PORT'))
MQTT_TOPIC = os.getenv('MQTT_TOPIC')

# Logger und Translator initialisieren
logging.basicConfig(filename='/var/log/decrypter.log', encoding='utf-8', level=LOGLEVEL)
t = GXDLMSTranslator(TranslatorOutputType.SIMPLE_XML)

if __name__ == '__main__':

    # Vierbindung zu seriellem Port aufbauen
    try:
        connection = serial.Serial(
            port=PORT,
            baudrate=BAUD,
            parity=serial.PARITY_NONE,
            bytesize=serial.EIGHTBITS,
        timeout=4)
    except (serial.SerialException, OSError) as err:
        logging.error(f'{datetime.now()}:Serial connection error: {err}')

    # Daten in Endlos-Schleife auslesen und interpretieren
    while True:
        data = connection.read(1024)
        if data:
            data = ba.hexlify(data)
            logging.debug(ba.hexlify(data))

            # Telegram Elemente statsich extrahieren
            # TO DO: dynamischen Parser implemenrieren
            systitle = data[22:38]
            frameCounter = data[44:52]
            payload = data[52:-4]
            iv = systitle+frameCounter

            # payload entschlüsseln mit Key von Netz NÖ
            iv = ba.unhexlify(iv)
            payload = ba.unhexlify(payload)

            cipher = AES.new(KEY, AES.MODE_GCM, nonce=iv)
            decrypted = cipher.decrypt(payload)
            logging.debug(f'{datetime.now()}:Decrypted PDU: {ba.hexlify(decrypted)}')
            
            # Dekodierung und Konveriterung des XML
            # TO DO: Dynamischen XML Parser implementieren
            try:
                raw_tree = t.pduToXml(decrypted)

                tree = ET.ElementTree(ET.fromstring(raw_tree))
                root = tree.getroot()
                timestamp = root[2][0][0][0].attrib['Value']
                energy_total_pos = root[2][0][0][2].attrib['Value']
                energy_total_neg = root[2][0][0][5].attrib['Value'] 
                power_pos = root[2][0][0][8].attrib['Value']
                power_neg = root[2][0][0][11].attrib['Value']

            except Exception as e:
                logging.warning(f'{datetime.now()}:PDU invalid: {e}')
                continue


            # changeType Data Types siehe:
            # Gurux.DLMS.Python/Gurux.DLMS.python/gurux_dlms/enums/DataType.py 
            timestamp = GXDLMSClient.changeType(timestamp, 0x19)
            energy_total_pos = GXDLMSClient.changeType(energy_total_pos, 6) * 0.01
            energy_total_neg = GXDLMSClient.changeType(energy_total_neg, 6) * 0.01
            power_pos = GXDLMSClient.changeType(power_pos, 6)
            power_neg = GXDLMSClient.changeType(power_neg, 6)


            #Sende Werte zum MQTT broker
            auth = {
                'username': MQTT_USER,
                'password': MQTT_PASS
            }

            msgs = [
                {
                    'topic': MQTT_TOPIC,
                    'payload': f'{{\
                        "kWh_in": {energy_total_pos}, \
                        "kWh_out": {energy_total_neg}, \
                        "pwr_in": {power_pos}, \
                        "pwr_out": {power_neg} \
                    }}',
                    'qos': 2
                }
            ]

            # To DO: TLS konfigurieren !!!!
            try:
                mp.multiple(msgs, hostname=MQTT_HOST, port=MQTT_PORT, auth=auth)
            except Exception as e:
                logging.error(f'{datetime.now()}:Connecting to mqtt broker: {e}')
                continue

            data = b''
