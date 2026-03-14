#!/usr/bin/env python3
"""
OmniRemote™ Pi Zero IR Blaster v1.2.0
GPIO-based IR transmitter using pigpio.
© 2026 One Eye Enterprises LLC
"""

import argparse
import base64
import json
import logging
import os
import signal
import time
from pathlib import Path
from typing import List, Optional

import yaml
import paho.mqtt.client as mqtt

try:
    import pigpio
    PIGPIO = True
except ImportError:
    PIGPIO = False

VERSION = "1.2.0"


class IRBlaster:
    def __init__(self, config: dict):
        self.config = config
        self.pi = None
        self.mqtt = None
        self.running = False
        
        ir = config.get("ir_blaster", {})
        self.pin = ir.get("gpio_pin", 18)
        self.freq = ir.get("carrier_frequency", 38000)
        
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        self.log = logging.getLogger("IRBlaster")
    
    def connect_gpio(self) -> bool:
        if not PIGPIO:
            self.log.error("pigpio not available")
            return False
        
        try:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                self.log.error("pigpiod not running")
                return False
            self.pi.set_mode(self.pin, pigpio.OUTPUT)
            self.log.info(f"GPIO ready on pin {self.pin}")
            return True
        except Exception as e:
            self.log.error(f"GPIO error: {e}")
            return False
    
    def connect_mqtt(self) -> bool:
        cfg = self.config.get("mqtt", {})
        try:
            self.mqtt = mqtt.Client(client_id="omniremote-ir")
            if cfg.get("username"):
                self.mqtt.username_pw_set(cfg["username"], cfg.get("password", ""))
            
            self.mqtt.on_connect = self._on_connect
            self.mqtt.on_message = self._on_message
            
            self.mqtt.connect(cfg.get("broker", "localhost"), int(cfg.get("port", 1883)))
            self.mqtt.loop_start()
            return True
        except Exception as e:
            self.log.error(f"MQTT error: {e}")
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.log.info("MQTT connected")
            prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
            client.subscribe(f"{prefix}/ir/send")
            client.subscribe(f"{prefix}/ir/send_raw")
            client.subscribe(f"{prefix}/ir/send_broadlink")
    
    def _on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            prefix = self.config.get("mqtt", {}).get("topic_prefix", "omniremote")
            
            if msg.topic == f"{prefix}/ir/send":
                self.send_nec(data.get("address", 0), data.get("command", 0))
            elif msg.topic == f"{prefix}/ir/send_raw":
                self.send_raw(data.get("pulses", []))
            elif msg.topic == f"{prefix}/ir/send_broadlink":
                self.send_broadlink(data.get("code", ""))
        except Exception as e:
            self.log.error(f"Message error: {e}")
    
    def send_nec(self, addr: int, cmd: int):
        pulses = [9000, 4500]
        data = (addr & 0xFF) | ((~addr & 0xFF) << 8) | ((cmd & 0xFF) << 16) | ((~cmd & 0xFF) << 24)
        for i in range(32):
            pulses.extend([562, 1687 if (data >> i) & 1 else 562])
        pulses.append(562)
        self.log.info(f"NEC: addr=0x{addr:02X} cmd=0x{cmd:02X}")
        self._send(pulses)
    
    def send_raw(self, pulses: List[int]):
        self.log.info(f"Raw: {len(pulses)} pulses")
        self._send(pulses)
    
    def send_broadlink(self, code: str):
        try:
            data = base64.b64decode(code)
            pulses = []
            i = 4
            while i < len(data) - 1:
                val = data[i]
                if val == 0 and i + 2 < len(data):
                    val = (data[i + 1] << 8) | data[i + 2]
                    i += 2
                pulses.append(val * 269 // 8192)
                i += 1
            self._send(pulses)
        except Exception as e:
            self.log.error(f"Broadlink error: {e}")
    
    def _send(self, pulses: List[int]):
        if not self.pi:
            return
        
        wave = []
        cycle = 1000000 // self.freq
        on_time = int(cycle * 0.33)
        off_time = cycle - on_time
        
        for i, dur in enumerate(pulses):
            if i % 2 == 0:
                for _ in range(int(dur * self.freq / 1000000)):
                    wave.append(pigpio.pulse(1 << self.pin, 0, on_time))
                    wave.append(pigpio.pulse(0, 1 << self.pin, off_time))
            else:
                wave.append(pigpio.pulse(0, 1 << self.pin, dur))
        
        try:
            self.pi.wave_clear()
            self.pi.wave_add_generic(wave)
            wid = self.pi.wave_create()
            if wid >= 0:
                self.pi.wave_send_once(wid)
                while self.pi.wave_tx_busy():
                    time.sleep(0.001)
                self.pi.wave_delete(wid)
        except Exception as e:
            self.log.error(f"Send error: {e}")
    
    def run(self):
        self.running = True
        self.log.info(f"OmniRemote IR Blaster v{VERSION}")
        
        self.connect_gpio()
        if not self.connect_mqtt():
            return
        
        self.log.info("IR ready")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        if self.mqtt:
            self.mqtt.loop_stop()
        if self.pi:
            self.pi.stop()
    
    def stop(self):
        self.running = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", default="/etc/omniremote/config.yaml")
    args = parser.parse_args()
    
    cfg = yaml.safe_load(Path(args.config).read_text()) if Path(args.config).exists() else {}
    blaster = IRBlaster(cfg)
    
    signal.signal(signal.SIGINT, lambda s, f: blaster.stop())
    signal.signal(signal.SIGTERM, lambda s, f: blaster.stop())
    
    blaster.run()


if __name__ == "__main__":
    main()
