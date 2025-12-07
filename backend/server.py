import paho.mqtt.client as mqtt
import json
import base64
import struct
import time
import logging

# Configuration
BROKER_ADDRESS = "localhost" # ChirpStack MQTT Broker
BROKER_PORT = 1883
TOPIC_PATTERN = "application/+/device/+/event/up" # ChirpStack v4 Topic

# Thresholds
ALARM_FULL_ML = 1800
ALARM_FLOW_LOW_MLH = 10
ALARM_BLOCKAGE_MINUTES = 120

# State Store (In-memory for demo; use Redis/DB in production)
# Structure: { "dev_eui": { "last_vol": 0, "last_ts": 0, "flow_buffer": [] } }
device_state = {}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def decode_payload(payload_base64):
    """
    Decodes the custom packed binary payload from the Firmware.
    Format (6 Bytes):
    [0]: Status Flags (Bit 0: LowBatt, 1: Full, 2: Blockage)
    [1]: Battery %
    [2-3]: Volume (mL) - uint16 Little Endian
    [4-5]: Flow (mL/h) - uint16 Little Endian
    """
    try:
        data = base64.b64decode(payload_base64)
        if len(data) < 6:
            logging.error(f"Payload too short: {len(data)} bytes")
            return None

        status = data[0]
        batt = data[1]
        volume = struct.unpack('<H', data[2:4])[0]
        flow_fw = struct.unpack('<H', data[4:6])[0] # Flow calculated by FW

        return {
            "status": status,
            "battery_percent": batt,
            "volume_ml": volume,
            "flow_mlh_fw": flow_fw,
            "flags": {
                "low_batt": bool(status & 0x01),
                "full_alarm": bool(status & 0x02),
                "blockage": bool(status & 0x04)
            }
        }
    except Exception as e:
        logging.error(f"Decoding failed: {e}")
        return None

def process_business_logic(dev_eui, telemetry):
    """
    Analyzes the data for critical conditions.
    """
    current_vol = telemetry['volume_ml']
    timestamp = time.time()
    
    # 1. Server-Side Flow Calculation (Verification)
    if dev_eui in device_state:
        prev = device_state[dev_eui]
        delta_t_hours = (timestamp - prev['last_ts']) / 3600.0
        
        if delta_t_hours > 0 and delta_t_hours < 24: # Ignore massive jumps or div0
            delta_v = current_vol - prev['last_vol']
            
            # Simple rejection of negative flow (sensor noise vs bag emptying)
            if delta_v < -100:
                logging.info(f"[{dev_eui}] Bag Emptying Detected (Delta: {delta_v}mL)")
                # Reset logic could go here
            elif delta_v >= 0:
                server_flow = delta_v / delta_t_hours
                logging.info(f"[{dev_eui}] Calculated Flow: {server_flow:.2f} mL/h")
                
                # Blockage Detection
                if server_flow < ALARM_FLOW_LOW_MLH:
                    logging.warning(f"[{dev_eui}] POTENTIAL BLOCKAGE! Flow {server_flow:.2f} < {ALARM_FLOW_LOW_MLH}")
                    # Trigger Alert (SMS/Pager)
    
    # Update State
    device_state[dev_eui] = {
        "last_vol": current_vol,
        "last_ts": timestamp
    }

    # 2. Critical Thresholds
    if telemetry['volume_ml'] > ALARM_FULL_ML:
        logging.critical(f"[{dev_eui}] URINE BAG FULL! {current_vol}mL")
        # Trigger Alert

    if telemetry['flags']['low_batt']:
        logging.warning(f"[{dev_eui}] Low Battery")

def on_connect(client, userdata, flags, rc):
    logging.info(f"Connected to MQTT Broker (RC: {rc})")
    client.subscribe(TOPIC_PATTERN)

def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode('utf-8')
        json_msg = json.loads(payload_str)
        
        # ChirpStack v4 JSON Structure
        dev_eui = json_msg.get('deviceInfo', {}).get('devEui', 'UNKNOWN')
        data_base64 = json_msg.get('data', '')
        
        logging.info(f"Received Uplink from {dev_eui}")
        
        telemetry = decode_payload(data_base64)
        if telemetry:
            logging.info(f"Decoded: {telemetry}")
            process_business_logic(dev_eui, telemetry)
            
            # TODO: Insert into InfluxDB here
            # write_api.write(bucket, org, Point("urine_monitor").tag("dev_eui", dev_eui).field("volume", telemetry['volume_ml'])...)

    except Exception as e:
        logging.error(f"Error processing message: {e}")

if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    logging.info("Starting Urine Monitoring Server...")
    try:
        client.connect(BROKER_ADDRESS, BROKER_PORT, 60)
        client.loop_forever()
    except Exception as e:
        logging.error(f"Connection failed: {e}")
