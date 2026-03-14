#!/usr/bin/env python3
"""
OmniRemote Pi Hub Discovery Script

Scans local network for Raspberry Pi devices and can auto-install OmniRemote.

Usage:
    python3 find-pihub.py              # Scan for Pi devices
    python3 find-pihub.py --install    # Scan and offer to install

© 2026 One Eye Enterprises LLC
"""

import socket
import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Raspberry Pi MAC prefixes
PI_MAC_PREFIXES = [
    "b8:27:eb",  # Pi Zero W, Pi 3
    "dc:a6:32",  # Pi 4, Pi Zero 2 W
    "e4:5f:01",  # Pi 4, Pi 5
    "d8:3a:dd",  # Pi 5
]

def get_local_network():
    """Get the local network range."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Assume /24 network
        network = ".".join(local_ip.split(".")[:-1]) + ".0/24"
        return local_ip, network
    except Exception:
        return None, "192.168.1.0/24"

def check_host(ip):
    """Check if host is reachable and get info."""
    try:
        # Quick ping check
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True,
            timeout=2
        )
        if result.returncode != 0:
            return None
        
        # Check SSH port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        ssh_open = sock.connect_ex((ip, 22)) == 0
        sock.close()
        
        # Check OmniRemote port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        omni_open = sock.connect_ex((ip, 8125)) == 0
        sock.close()
        
        if ssh_open or omni_open:
            # Try to get MAC address from ARP
            mac = get_mac(ip)
            is_pi = is_raspberry_pi(mac) if mac else False
            
            return {
                "ip": ip,
                "mac": mac,
                "ssh": ssh_open,
                "omniremote": omni_open,
                "is_pi": is_pi,
            }
    except Exception:
        pass
    return None

def get_mac(ip):
    """Get MAC address from ARP cache."""
    try:
        result = subprocess.run(
            ["arp", "-n", ip],
            capture_output=True,
            text=True,
            timeout=2
        )
        for line in result.stdout.split("\n"):
            if ip in line:
                parts = line.split()
                for part in parts:
                    if ":" in part and len(part) == 17:
                        return part.lower()
    except Exception:
        pass
    return None

def is_raspberry_pi(mac):
    """Check if MAC address belongs to Raspberry Pi."""
    if not mac:
        return False
    mac_prefix = mac[:8].lower()
    return mac_prefix in PI_MAC_PREFIXES

def scan_network(network_range=None):
    """Scan network for devices."""
    local_ip, default_network = get_local_network()
    network = network_range or default_network
    
    print(f"\n🔍 Scanning network: {network}")
    print(f"   Your IP: {local_ip}\n")
    
    # Generate IP list
    base = ".".join(network.split("/")[0].split(".")[:-1])
    ips = [f"{base}.{i}" for i in range(1, 255)]
    
    devices = []
    pi_devices = []
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_host, ip): ip for ip in ips}
        done = 0
        for future in as_completed(futures):
            done += 1
            print(f"\r   Progress: {done}/254 ", end="", flush=True)
            result = future.result()
            if result:
                devices.append(result)
                if result["is_pi"]:
                    pi_devices.append(result)
    
    print("\n")
    return devices, pi_devices

def display_results(devices, pi_devices):
    """Display scan results."""
    if pi_devices:
        print("🍓 Raspberry Pi devices found:\n")
        print("   IP Address       MAC Address        SSH   OmniRemote")
        print("   " + "-" * 55)
        for d in pi_devices:
            ssh = "✓" if d["ssh"] else "✗"
            omni = "✓" if d["omniremote"] else "✗"
            mac = d["mac"] or "unknown"
            print(f"   {d['ip']:<16} {mac:<18} {ssh:<5} {omni}")
        print()
    else:
        print("❌ No Raspberry Pi devices found\n")
        print("   Tip: Make sure your Pi is:")
        print("   - Powered on and connected to WiFi")
        print("   - On the same network as this device")
        print("   - Has SSH enabled\n")
    
    # Show other devices with SSH
    other_ssh = [d for d in devices if d["ssh"] and not d["is_pi"]]
    if other_ssh:
        print(f"📡 Other devices with SSH ({len(other_ssh)}):\n")
        for d in other_ssh[:10]:  # Show max 10
            mac = d["mac"] or "unknown"
            omni = " [OmniRemote]" if d["omniremote"] else ""
            print(f"   {d['ip']:<16} {mac}{omni}")
        if len(other_ssh) > 10:
            print(f"   ... and {len(other_ssh) - 10} more")
        print()

def install_on_pi(ip, username="pi", password="raspberry"):
    """SSH into Pi and install OmniRemote."""
    print(f"\n🚀 Installing OmniRemote on {ip}...")
    
    try:
        import paramiko
    except ImportError:
        print("❌ paramiko not installed. Run: pip install paramiko")
        print(f"\n   Or manually SSH and run:")
        print(f"   ssh {username}@{ip}")
        print(f"   curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/quick-install.sh | sudo bash")
        return False
    
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password, timeout=10)
        
        install_cmd = "curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/quick-install.sh | sudo bash"
        
        stdin, stdout, stderr = client.exec_command(install_cmd, timeout=300)
        
        # Stream output
        for line in stdout:
            print(line, end="")
        
        client.close()
        print(f"\n✅ Installation complete! Access at: https://{ip}:8125")
        return True
        
    except Exception as e:
        print(f"❌ SSH connection failed: {e}")
        print(f"\n   Try manually:")
        print(f"   ssh {username}@{ip}")
        print(f"   curl -sSL https://raw.githubusercontent.com/HunterAviator/OmniRemote/main/pi-hub/quick-install.sh | sudo bash")
        return False

def main():
    print("\n" + "=" * 60)
    print("  OmniRemote Pi Hub Discovery")
    print("  © 2026 One Eye Enterprises LLC")
    print("=" * 60)
    
    devices, pi_devices = scan_network()
    display_results(devices, pi_devices)
    
    # Offer to install if --install flag and Pi found
    if "--install" in sys.argv and pi_devices:
        for pi in pi_devices:
            if not pi["omniremote"]:
                response = input(f"Install OmniRemote on {pi['ip']}? (y/N): ")
                if response.lower() == "y":
                    username = input("SSH username [pi]: ") or "pi"
                    password = input("SSH password [raspberry]: ") or "raspberry"
                    install_on_pi(pi["ip"], username, password)

if __name__ == "__main__":
    main()
