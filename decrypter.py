#!/usr/bin env python3

'''
V0.1, 2021-12-14

Etschlüsselung und Aufbereitung von Smart Meter Telegrammen:
* Smart Meter: Sagemcom Drehstromzähler T210-D
* Netzbetreiber: Netz NÖ

Für die Verwendung des Skripts muss der Entschlüsselungs-Key
vom smartmeter@netz-noe.at angefordert werden.
'''

'''
V0.2, 2023-10-23

Crypto Library umbenannt
Werte für Spannung und Strom von L1,L2 und L3 hinzugefügt
QoS und Retain Flag hinzugefügt und angepasst
Konsolenausage optional für Debugging hinzugefügt
'''

import serial
import binascii as ba
import os
import logging
import paho.mqtt.publish as mp
from Crypto.Cipher import AES
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
                voltage_l1 = root[2][0][0][14].attrib['Value']
                voltage_l2 = root[2][0][0][17].attrib['Value']
                voltage_l3 = root[2][0][0][20].attrib['Value']
                current_l1 = root[2][0][0][23].attrib['Value']
                current_l2 = root[2][0][0][26].attrib['Value']
                current_l3 = root[2][0][0][29].attrib['Value']

            except Exception as e:
                logging.warning(f'{datetime.now()}:PDU invalid: {e}')
                continue


            # changeType() Data Types siehe:
            # Gurux.DLMS.Python/Gurux.DLMS.python/gurux_dlms/enums/DataType.py 
            timestamp = GXDLMSClient.changeType(timestamp, 0x19)
            energy_total_pos = GXDLMSClient.changeType(energy_total_pos, 6) * 0.001
            energy_total_neg = GXDLMSClient.changeType(energy_total_neg, 6) * 0.001
            power_pos = GXDLMSClient.changeType(power_pos, 6)
            power_neg = GXDLMSClient.changeType(power_neg, 6)
            voltage_l1 = GXDLMSClient.changeType(voltage_l1, 0x12) * 0.1
            voltage_l2 = GXDLMSClient.changeType(voltage_l2, 0x12) * 0.1
            voltage_l3 = GXDLMSClient.changeType(voltage_l3, 0x12) * 0.1
            current_l1 = GXDLMSClient.changeType(current_l1, 0x12) * 0.01
            current_l2 = GXDLMSClient.changeType(current_l2, 0x12) * 0.01
            current_l3 = GXDLMSClient.changeType(current_l3, 0x12) * 0.01


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
                        "pwr_out": {power_neg}, \
                        "v_l1": {voltage_l1}, \
                        "v_l2": {voltage_l2}, \
                        "v_l3": {voltage_l3}, \
                        "c_l1": {current_l1}, \
                        "c_l2": {current_l2}, \
                        "c_l3": {current_l3} \
                    }}',
                    'qos': 2,
                    'retain': False
                }
            ]

            # Für Debugging auskommentieren:
            # print("msgs %s",msgs)

            # To DO: TLS konfigurieren !!!!
            try:
                mp.multiple(msgs, hostname=MQTT_HOST, port=MQTT_PORT, auth=auth)
            except Exception as e:
                logging.error(f'{datetime.now()}:Connecting to mqtt broker: {e}')
                continue

            data = b''
