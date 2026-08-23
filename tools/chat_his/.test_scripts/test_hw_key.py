import os
import platform
import multiprocessing
import uuid
import hashlib

def get_hardware_key():
    components = []
    
    # 1. OS Name
    components.append(platform.system())
    
    # 2. CPU Cores
    try:
        components.append(str(multiprocessing.cpu_count()))
    except NotImplementedError:
        pass
        
    # 3. Architecture
    components.append(platform.machine())
    
    # 4. Hostname
    components.append(platform.node())
    
    # 5. MAC Address (Hardware address)
    components.append(str(uuid.getnode()))
    
    # 6. /etc/machine-id (Unique to the OS installation, changes on format)
    try:
        with open("/etc/machine-id", "r") as f:
            components.append(f.read().strip())
    except Exception:
        pass
        
    # 7. CPU Model (Linux specific)
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    components.append(line.split(":")[1].strip())
                    break
    except Exception:
        pass

    raw_string = "|".join(components)
    print("Raw HW string:", raw_string)
    
    # Hash to get a deterministic 256-bit (32-byte) hex string for SQLCipher
    key = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
    print("Derived Key:", key)
    return key

get_hardware_key()
