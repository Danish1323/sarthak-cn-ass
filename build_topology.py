#!/usr/bin/env python3
"""
Sudsline Artisan Soap Manufacturing Network Builder
Builds the complete Packet Tracer topology and deploys configurations.
"""

import sys
import time
import json
from pathlib import Path

# Add MCP module path to python path
sys.path.insert(0, '/Users/danishshaikh1423/Downloads/OMKAR-KI-CN-WALI-ASS/MCP-Packet-Tracer/src')
from packet_tracer_mcp.infrastructure.execution.file_bridge import FileBridge
from packet_tracer_mcp.domain.services.canvas import decode_pt_image

fb = FileBridge()

def check_alive():
    if not fb.pt_alive():
        print("ERROR: Packet Tracer bridge is not responding.")
        sys.exit(1)
    print("Bridge connection: ACTIVE")

def execute_js(js_code, timeout=20.0):
    res = fb.send_and_wait(js_code, timeout=timeout)
    return res

def clear_canvas():
    print("Clearing canvas...")
    js = """
    try {
        var net = ipc.network();
        var count = net.getDeviceCount();
        for (var i = count - 1; i >= 0; i--) {
            var dev = net.getDeviceAt(i);
            if (dev && dev.getModel() !== "Power Distribution Device") {
                net.removeDevice(dev.getName());
            }
        }
        var lw = ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();
        lw.clearAnnotations();
        reportResult("CLEARED");
    } catch (e) {
        reportResult("ERR:" + e);
    }
    """
    res = execute_js(js)
    print("Clear result:", res)
    time.sleep(1)

if __name__ == "__main__":
    check_alive()
    clear_canvas()
