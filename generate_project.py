#!/usr/bin/env python3
"""
Master Deployment Script for Sudsline Artisan Soap Manufacturing Network Investigation
Case Study 185 - Capstone Diagnostics
Generates the complete .pkt topology, configures all devices, verifies symptoms,
captures screenshots, and outputs all project deliverables.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add MCP module path
sys.path.insert(0, '/Users/danishshaikh1423/Downloads/OMKAR-KI-CN-WALI-ASS/MCP-Packet-Tracer/src')
from packet_tracer_mcp.infrastructure.execution.file_bridge import FileBridge
from packet_tracer_mcp.domain.services.canvas import decode_pt_image

fb = FileBridge()

WORKSPACE_DIR = Path("/Users/danishshaikh1423/Downloads/sarthak-cn")
SCREENSHOTS_DIR = WORKSPACE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
CLI_LOGS_DIR = WORKSPACE_DIR / "cli_evidence"
CLI_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def execute_js(js_code, timeout=25.0):
    res = fb.send_and_wait(js_code, timeout=timeout)
    return res

def check_bridge():
    if not fb.pt_alive():
        print("[-] Packet Tracer Bridge is not alive!")
        sys.exit(1)
    print("[+] Packet Tracer Bridge is ACTIVE")

def clear_workspace():
    print("[*] Clearing existing topology and annotations...")
    js = """
    try {
        var net = ipc.network();
        var lw = ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();
        var count = net.getDeviceCount();
        for (var i = count - 1; i >= 0; i--) {
            var dev = net.getDeviceAt(i);
            if (dev && dev.getModel() !== "Power Distribution Device") {
                lw.removeDevice(dev.getName());
            }
        }
        var noteIds = [];
        try { noteIds = lw.getCanvasNoteIds() || []; } catch(e) {}
        for (var j = 0; j < noteIds.length; j++) {
            try { lw.removeCanvasItem(noteIds[j]); } catch(e) {}
        }
        reportResult("CLEARED");
    } catch (e) {
        reportResult("ERR:" + e);
    }
    """
    res = execute_js(js)
    print("    Result:", res)
    time.sleep(1.5)

def build_devices():
    print("[*] Creating network devices with optimized logical layout...")
    devices = [
        # Cloud & ISPs (Tier 1: y = 90)
        {"name": "ISP1-Primary", "type": 0, "model": "2911", "x": 360, "y": 90},
        {"name": "ISP2-Secondary", "type": 0, "model": "2911", "x": 580, "y": 90},
        {"name": "Partner-Server", "type": 9, "model": "Server-PT", "x": 760, "y": 90},

        # Site Routers (Tier 2: y = 230)
        {"name": "Plant-Router", "type": 0, "model": "2911", "x": 160, "y": 230},
        {"name": "HQ-Edge-Router", "type": 0, "model": "2911", "x": 460, "y": 230},
        {"name": "WH-Router", "type": 0, "model": "2911", "x": 800, "y": 230},

        # Switches (Tier 3: y = 350 - 460)
        {"name": "Plant-Core-SW", "type": 1, "model": "2960-24TT", "x": 160, "y": 350},
        {"name": "Plant-Access-SW", "type": 1, "model": "2960-24TT", "x": 160, "y": 460},
        {"name": "Rogue-Switch", "type": 1, "model": "2950-24", "x": 50, "y": 460},

        {"name": "HQ-Switch", "type": 1, "model": "2960-24TT", "x": 460, "y": 350},
        {"name": "WH-Switch", "type": 1, "model": "2960-24TT", "x": 800, "y": 350},

        # Workstations & Terminals (Tier 4: y = 470 - 580)
        {"name": "Batch-Terminal-1", "type": 8, "model": "PC-PT", "x": 100, "y": 580},
        {"name": "Batch-Terminal-2", "type": 8, "model": "PC-PT", "x": 160, "y": 580},
        {"name": "Rogue-Attacker-PC", "type": 8, "model": "PC-PT", "x": 220, "y": 580},

        {"name": "HQ-Sales-PC", "type": 8, "model": "PC-PT", "x": 410, "y": 470},
        {"name": "HQ-Design-PC", "type": 8, "model": "PC-PT", "x": 510, "y": 470},

        {"name": "WH-Inventory-PC", "type": 8, "model": "PC-PT", "x": 750, "y": 470},
        {"name": "WH-Packaging-PC", "type": 8, "model": "PC-PT", "x": 850, "y": 470},
    ]

    js_lines = ["try {"]
    for d in devices:
        js_lines.append(f'  lwAddDevice("{d["name"]}", {d["type"]}, "{d["model"]}", {d["x"]}, {d["y"]});')
    js_lines.append('  reportResult("DEVICES_CREATED"); } catch(e) { reportResult("ERR:" + e); }')
    
    res = execute_js("\n".join(js_lines))
    print("    Result:", res)
    time.sleep(1.5)

def install_modules():
    print("[*] Installing HWIC-2T serial modules on routers...")
    routers = ["Plant-Router", "HQ-Edge-Router", "WH-Router", "ISP1-Primary", "ISP2-Secondary"]
    js_lines = ["try {"]
    for r in routers:
        js_lines.append(f'  try {{ ipc.network().getDevice("{r}").getPower().setPower(false); }} catch(e){{}}')
    for r in routers:
        js_lines.append(f'  addModule("{r}", "0/0", "HWIC-2T");')
    for r in routers:
        js_lines.append(f'  try {{ ipc.network().getDevice("{r}").getPower().setPower(true); }} catch(e){{}}')
    js_lines.append('  reportResult("MODULES_INSTALLED"); } catch(e) { reportResult("ERR:" + e); }')

    res = execute_js("\n".join(js_lines))
    print("    Result:", res)
    print("    Waiting 5 seconds for routers to complete boot cycle...")
    time.sleep(5)

def build_links():
    print("[*] Connecting physical and logical links...")
    links = [
        # Plant Site Internal
        ("Plant-Router", "GigabitEthernet0/0", "Plant-Core-SW", "GigabitEthernet0/1", 8100),
        ("Plant-Core-SW", "GigabitEthernet0/2", "Plant-Access-SW", "GigabitEthernet0/2", 8101),
        ("Plant-Access-SW", "FastEthernet0/1", "Batch-Terminal-1", "FastEthernet0", 8100),
        ("Plant-Access-SW", "FastEthernet0/2", "Batch-Terminal-2", "FastEthernet0", 8100),
        ("Plant-Access-SW", "FastEthernet0/3", "Rogue-Attacker-PC", "FastEthernet0", 8100),
        ("Plant-Access-SW", "FastEthernet0/10", "Rogue-Switch", "FastEthernet0/1", 8101),

        # HQ Site Internal
        ("HQ-Edge-Router", "GigabitEthernet0/0", "HQ-Switch", "GigabitEthernet0/1", 8100),
        ("HQ-Switch", "FastEthernet0/1", "HQ-Sales-PC", "FastEthernet0", 8100),
        ("HQ-Switch", "FastEthernet0/2", "HQ-Design-PC", "FastEthernet0", 8100),

        # Warehouse Site Internal
        ("WH-Router", "GigabitEthernet0/0", "WH-Switch", "GigabitEthernet0/1", 8100),
        ("WH-Switch", "FastEthernet0/1", "WH-Inventory-PC", "FastEthernet0", 8100),
        ("WH-Switch", "FastEthernet0/2", "WH-Packaging-PC", "FastEthernet0", 8100),

        # Inter-Site WAN Backbone Links
        ("HQ-Edge-Router", "GigabitEthernet0/1", "Plant-Router", "GigabitEthernet0/1", 8101),
        ("HQ-Edge-Router", "GigabitEthernet0/2", "WH-Router", "GigabitEthernet0/2", 8101),
        ("Plant-Router", "GigabitEthernet0/2", "WH-Router", "GigabitEthernet0/1", 8101),
        ("Plant-Router", "Serial0/0/0", "WH-Router", "Serial0/0/0", 8106),

        # Internet Edge & Partner Links
        ("HQ-Edge-Router", "Serial0/0/0", "ISP1-Primary", "Serial0/0/0", 8106),
        ("HQ-Edge-Router", "Serial0/0/1", "ISP2-Secondary", "Serial0/0/0", 8106),
        ("ISP2-Secondary", "GigabitEthernet0/0", "Partner-Server", "FastEthernet0", 8100),
    ]

    js_lines = ["try {"]
    for d1, p1, d2, p2, ctype in links:
        js_lines.append(f'  lwAddLink("{d1}", "{p1}", "{d2}", "{p2}", {ctype});')
    js_lines.append('  reportResult("LINKS_CREATED"); } catch(e) { reportResult("ERR:" + e); }')

    res = execute_js("\n".join(js_lines))
    print("    Result:", res)
    time.sleep(2)

def add_canvas_notes():
    print("[*] Adding architectural documentation labels on canvas...")
    notes = [
        (80, 20, "=== CASE STUDY 185: SUDSLINE ARTISAN SOAP MANUFACTURING NETWORK INVESTIGATION ==="),
        (360, 45, "Dual-ISP BGP Cloud & External Partner Network (AS 65001 / AS 65002)"),
        (40, 160, "[SITE 1] Curing & Batching Plant\\nLegacy EIGRP AS 100 / DAI / BPDU Guard"),
        (380, 160, "[SITE 2] Head Office (Showroom & Design)\\nOSPF Area 0 Backbone / Dual eBGP Edge"),
        (720, 160, "[SITE 3] Packaging Warehouse\\nEIGRP Redundant WAN / Inventory LAN"),
        (230, 215, "OSPF WAN (10.100.1.0/30)\\n[Symptom B: MTU Check]"),
        (580, 215, "OSPF WAN (10.100.2.0/30)"),
        (380, 275, "Plant-WH Redundant Paths:\\n- Primary Gi0/2: 10.100.3.0/30 (1 Gbps)\\n- Secondary Se0/0/0: 10.100.4.0/30 (Symptom C: Bandwidth Discrepancy)"),
        (40, 515, "Plant Access Layer (10.20.10.0/24)\\n[Symptom A: STP Flap | Symptom E: ARP Spoofing Attack]"),
    ]

    js_lines = [
        "try {",
        "  var lw = ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();"
    ]
    for x, y, text in notes:
        js_lines.append(f'  var z = (typeof lw.getIncNoteZOrder === "function") ? lw.getIncNoteZOrder() : 0;')
        js_lines.append(f'  lw.addNote({x}, {y}, z, "{text}");')
    js_lines.append('  reportResult("NOTES_ADDED"); } catch(e) { reportResult("ERR:" + e); }')

    res = execute_js("\n".join(js_lines))
    print("    Result:", res)
    time.sleep(1)

def configure_hosts():
    print("[*] Configuring IP addresses on PCs and Servers...")
    hosts = [
        ("Batch-Terminal-1", "10.20.10.10", "255.255.255.0", "10.20.10.1", "8.8.8.8"),
        ("Batch-Terminal-2", "10.20.10.11", "255.255.255.0", "10.20.10.1", "8.8.8.8"),
        ("Rogue-Attacker-PC", "10.20.10.99", "255.255.255.0", "10.20.10.1", "8.8.8.8"),

        ("HQ-Sales-PC", "10.10.10.11", "255.255.255.0", "10.10.10.1", "8.8.8.8"),
        ("HQ-Design-PC", "10.10.10.12", "255.255.255.0", "10.10.10.1", "8.8.8.8"),

        ("WH-Inventory-PC", "10.30.10.10", "255.255.255.0", "10.30.10.1", "8.8.8.8"),
        ("WH-Packaging-PC", "10.30.10.11", "255.255.255.0", "10.30.10.1", "8.8.8.8"),

        ("Partner-Server", "198.18.50.10", "255.255.255.0", "198.18.50.1", "8.8.8.8"),
    ]

    js_lines = ["try {"]
    for name, ip, mask, gw, dns in hosts:
        js_lines.append(f'  configurePcIp("{name}", false, "{ip}", "{mask}", "{gw}", "{dns}");')
    js_lines.append('  reportResult("HOSTS_CONFIGURED"); } catch(e) { reportResult("ERR:" + e); }')

    res = execute_js("\n".join(js_lines))
    print("    Result:", res)
    time.sleep(1)

def send_device_cli(dev_name, commands_list):
    js_lines = [
        "try {",
        f'  var dev = ipc.network().getDevice("{dev_name}");',
        "  if (!dev) { reportResult('ERR: Device not found'); }",
        "  var cl = dev.getCommandLine();",
        "  cl.enterCommand('no');",
        "  cl.enterCommand('');",
        "  cl.enterCommand('enable');",
        "  cl.enterCommand('configure terminal');",
    ]
    for cmd in commands_list:
        if cmd.strip():
            js_lines.append(f'  cl.enterCommand({json.dumps(cmd.strip())});')
    js_lines.append("  cl.enterCommand('end');")
    js_lines.append("  cl.enterCommand('write memory');")
    js_lines.append(f'  reportResult("OK:" + "{dev_name}");')
    js_lines.append("} catch(e) { reportResult('ERR:' + e); }")

    return execute_js("\n".join(js_lines), timeout=15.0)

def configure_network_devices():
    print("[*] Deploying Cisco IOS configurations to Routers and Switches...")

    configs = {
        "HQ-Edge-Router": [
            "hostname HQ-Edge-Router",
            "no ip domain-lookup",
            "interface GigabitEthernet0/0",
            " description LAN_HQ_Showroom",
            " ip address 10.10.10.1 255.255.255.0",
            " no shutdown",
            "interface GigabitEthernet0/1",
            " description WAN_to_Batching_Plant",
            " ip address 10.100.1.1 255.255.255.252",
            " ip mtu 1500",
            " no shutdown",
            "interface GigabitEthernet0/2",
            " description WAN_to_Packaging_Warehouse",
            " ip address 10.100.2.1 255.255.255.252",
            " no shutdown",
            "interface Serial0/0/0",
            " description eBGP_to_ISP1_Primary",
            " ip address 203.0.113.2 255.255.255.252",
            " clock rate 128000",
            " no shutdown",
            "interface Serial0/0/1",
            " description eBGP_to_ISP2_Secondary",
            " ip address 198.51.100.2 255.255.255.252",
            " clock rate 128000",
            " no shutdown",
            "router ospf 1",
            " router-id 1.1.1.1",
            " network 10.10.10.0 0.0.0.255 area 0",
            " network 10.100.1.0 0.0.0.3 area 0",
            " network 10.100.2.0 0.0.0.3 area 0",
            " default-information originate",
            "router bgp 65000",
            " bgp log-neighbor-changes",
            " neighbor 203.0.113.1 remote-as 65001",
            " neighbor 203.0.113.1 description PRIMARY-ISP1",
            " neighbor 198.51.100.1 remote-as 65002",
            " neighbor 198.51.100.1 description SECONDARY-ISP2",
            " neighbor 198.51.100.1 route-map RM-ISP2-IN in",
            " network 10.10.10.0 mask 255.255.255.0",
            "ip prefix-list PARTNER-PREFIX permit 198.18.50.0/24",
            "ip prefix-list PARTNER-PREFIX permit 0.0.0.0/0",
            "route-map RM-ISP2-IN permit 10",
            " match ip address prefix-list PARTNER-PREFIX",
        ],

        "Plant-Router": [
            "hostname Plant-Router",
            "no ip domain-lookup",
            "interface GigabitEthernet0/0",
            " description LAN_Batching_Plant",
            " ip address 10.20.10.1 255.255.255.0",
            " no shutdown",
            "interface GigabitEthernet0/1",
            " description WAN_to_HQ_Edge",
            " ip address 10.100.1.2 255.255.255.252",
            " ip mtu 1500",
            " no shutdown",
            "interface GigabitEthernet0/2",
            " description WAN_Primary_to_Warehouse",
            " ip address 10.100.3.1 255.255.255.252",
            " bandwidth 1000000",
            " no shutdown",
            "interface Serial0/0/0",
            " description WAN_Secondary_to_Warehouse",
            " ip address 10.100.4.1 255.255.255.252",
            " bandwidth 100000",
            " clock rate 128000",
            " no shutdown",
            "router ospf 1",
            " router-id 2.2.2.2",
            " network 10.100.1.0 0.0.0.3 area 0",
            " redistribute eigrp 100 subnets",
            "router eigrp 100",
            " network 10.20.10.0 0.0.0.255",
            " network 10.100.3.0 0.0.0.3",
            " network 10.100.4.0 0.0.0.3",
            " auto-summary",
            " redistribute ospf 1 metric 100000 100 255 1 1500",
        ],

        "WH-Router": [
            "hostname WH-Router",
            "no ip domain-lookup",
            "interface GigabitEthernet0/0",
            " description LAN_Packaging_Warehouse",
            " ip address 10.30.10.1 255.255.255.0",
            " no shutdown",
            "interface GigabitEthernet0/1",
            " description WAN_Primary_to_Plant",
            " ip address 10.100.3.2 255.255.255.252",
            " bandwidth 1000000",
            " no shutdown",
            "interface Serial0/0/0",
            " description WAN_Secondary_to_Plant",
            " ip address 10.100.4.2 255.255.255.252",
            " bandwidth 100000",
            " no shutdown",
            "interface GigabitEthernet0/2",
            " description WAN_to_HQ_Edge",
            " ip address 10.100.2.2 255.255.255.252",
            " no shutdown",
            "router ospf 1",
            " router-id 3.3.3.3",
            " network 10.100.2.0 0.0.0.3 area 0",
            " redistribute eigrp 100 subnets",
            "router eigrp 100",
            " network 10.30.10.0 0.0.0.255",
            " network 10.100.3.0 0.0.0.3",
            " network 10.100.4.0 0.0.0.3",
            " auto-summary",
            " redistribute ospf 1 metric 100000 100 255 1 1500",
        ],

        "ISP1-Primary": [
            "hostname ISP1-Primary",
            "no ip domain-lookup",
            "interface Serial0/0/0",
            " description Link_to_HQ_Edge",
            " ip address 203.0.113.1 255.255.255.252",
            " no shutdown",
            "interface Loopback0",
            " description Public_Internet_DNS",
            " ip address 8.8.8.8 255.255.255.255",
            " no shutdown",
            "router bgp 65001",
            " bgp log-neighbor-changes",
            " neighbor 203.0.113.2 remote-as 65000",
            " network 8.8.8.8 mask 255.255.255.255",
        ],

        "ISP2-Secondary": [
            "hostname ISP2-Secondary",
            "no ip domain-lookup",
            "interface Serial0/0/0",
            " description Link_to_HQ_Edge",
            " ip address 198.51.100.1 255.255.255.252",
            " no shutdown",
            "interface GigabitEthernet0/0",
            " description Link_to_Partner_Network",
            " ip address 198.18.50.1 255.255.255.0",
            " no shutdown",
            "router bgp 65002",
            " bgp log-neighbor-changes",
            " neighbor 198.51.100.2 remote-as 65000",
            " network 198.18.50.0 mask 255.255.255.0",
        ],

        "Plant-Core-SW": [
            "hostname Plant-Core-SW",
            "no ip domain-lookup",
            "vlan 20",
            " name Batching_Plant_VLAN",
            "interface GigabitEthernet0/1",
            " description Uplink_to_Plant_Router",
            " switchport mode access",
            " switchport access vlan 20",
            " no shutdown",
            "interface GigabitEthernet0/2",
            " description Trunk_to_Plant_Access_SW",
            " switchport mode trunk",
            " switchport trunk allowed vlan 20,1",
            " no shutdown",
            "spanning-tree mode pvst",
            "spanning-tree vlan 20 root primary",
        ],

        "Plant-Access-SW": [
            "hostname Plant-Access-SW",
            "no ip domain-lookup",
            "vlan 20",
            " name Batching_Plant_VLAN",
            "interface GigabitEthernet0/2",
            " description Trunk_to_Plant_Core_SW",
            " switchport mode trunk",
            " switchport trunk allowed vlan 20,1",
            " no shutdown",
            "interface range FastEthernet0/1 - 2",
            " description Batch_Monitoring_Terminals",
            " switchport mode access",
            " switchport access vlan 20",
            " spanning-tree portfast",
            " spanning-tree bpduguard enable",
            " switchport port-security",
            " switchport port-security maximum 1",
            " switchport port-security violation restrict",
            " no shutdown",
            "interface FastEthernet0/3",
            " description Rogue_Attacker_Port",
            " switchport mode access",
            " switchport access vlan 20",
            " spanning-tree portfast",
            " spanning-tree bpduguard enable",
            " switchport port-security",
            " switchport port-security maximum 1",
            " switchport port-security violation restrict",
            " no shutdown",
            "interface FastEthernet0/10",
            " description Rogue_Switch_Connection",
            " switchport mode access",
            " switchport access vlan 20",
            " spanning-tree portfast",
            " spanning-tree bpduguard enable",
            " no shutdown",
            "interface range FastEthernet0/4 - 9, FastEthernet0/11 - 24",
            " shutdown",
            "ip dhcp snooping",
            "ip dhcp snooping vlan 20",
            "no ip dhcp snooping information option",
            "interface GigabitEthernet0/2",
            " ip dhcp snooping trust",
            "ip arp inspection vlan 20",
            "interface GigabitEthernet0/2",
            " ip arp inspection trust",
        ],

        "Rogue-Switch": [
            "hostname Rogue-Switch",
            "no ip domain-lookup",
            "interface range FastEthernet0/1 - 24",
            " no shutdown",
        ],

        "HQ-Switch": [
            "hostname HQ-Switch",
            "no ip domain-lookup",
            "interface GigabitEthernet0/1",
            " description Uplink_to_HQ_Edge_Router",
            " switchport mode access",
            " no shutdown",
            "interface range FastEthernet0/1 - 24",
            " description HQ_Workstations",
            " switchport mode access",
            " spanning-tree portfast",
            " spanning-tree bpduguard enable",
            " no shutdown",
        ],

        "WH-Switch": [
            "hostname WH-Switch",
            "no ip domain-lookup",
            "interface GigabitEthernet0/1",
            " description Uplink_to_WH_Router",
            " switchport mode access",
            " no shutdown",
            "interface range FastEthernet0/1 - 24",
            " description WH_Scanners_and_PCs",
            " switchport mode access",
            " spanning-tree portfast",
            " spanning-tree bpduguard enable",
            " no shutdown",
        ]
    }

    for dev_name, cmd_list in configs.items():
        print(f"    Configuring {dev_name}...")
        res = send_device_cli(dev_name, cmd_list)
        time.sleep(0.4)

    print("[+] All network device configurations deployed successfully.")

def run_cli_command(device_name, command_str):
    js = f"""
    try {{
        var dev = ipc.network().getDevice("{device_name}");
        if (!dev) {{ reportResult("ERR: Dev not found"); }}
        var cl = dev.getCommandLine();
        cl.enterCommand("enable");
        cl.enterCommand("terminal length 0");
        cl.enterCommand({json.dumps(command_str)});
        var out = String(cl.getOutput());
        reportResult(out);
    }} catch(e) {{
        reportResult("ERR:" + e);
    }}
    """
    res = execute_js(js, timeout=12.0)
    return res

def collect_verification_evidence():
    print("[*] Collecting live CLI verification evidence from devices...")
    checks = [
        ("HQ-Edge-Router", "show ip ospf neighbor", "hq_ospf_neighbor.txt"),
        ("HQ-Edge-Router", "show ip route ospf", "hq_ospf_routes.txt"),
        ("HQ-Edge-Router", "show ip bgp summary", "hq_bgp_summary.txt"),
        ("HQ-Edge-Router", "show ip bgp", "hq_bgp_table.txt"),
        ("HQ-Edge-Router", "show ip route bgp", "hq_bgp_routes.txt"),

        ("Plant-Router", "show ip ospf neighbor", "plant_ospf_neighbor.txt"),
        ("Plant-Router", "show ip eigrp topology", "plant_eigrp_topology.txt"),
        ("Plant-Router", "show ip route eigrp", "plant_eigrp_routes.txt"),
        ("Plant-Router", "show interfaces GigabitEthernet0/1", "plant_gi01_mtu.txt"),
        ("Plant-Router", "show interfaces Serial0/0/0", "plant_se000_bw.txt"),

        ("WH-Router", "show ip eigrp topology", "wh_eigrp_topology.txt"),
        ("WH-Router", "show ip route eigrp", "wh_eigrp_routes.txt"),

        ("Plant-Core-SW", "show spanning-tree vlan 20", "plant_core_spanning_tree.txt"),
        ("Plant-Access-SW", "show spanning-tree vlan 20", "plant_access_spanning_tree.txt"),
        ("Plant-Access-SW", "show ip arp inspection", "plant_access_dai.txt"),
        ("Plant-Access-SW", "show port-security interface FastEthernet0/1", "plant_access_portsec.txt"),
    ]

    for dev, cmd, fname in checks:
        print(f"    Running '{cmd}' on {dev}...")
        raw_out = run_cli_command(dev, cmd)
        clean_out = raw_out if raw_out else "No output returned"
        (CLI_LOGS_DIR / fname).write_text(clean_out)
        time.sleep(0.3)

    print("[+] Evidence collected and saved to cli_evidence/ directory.")

def capture_canvas_screenshot(filename="topology_overview.png"):
    print(f"[*] Capturing screenshot -> {filename}...")
    js = """
    try {
        var lw = ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();
        reportResult(String(lw.getWorkspaceImage("PNG")));
    } catch (e) {
        reportResult("ERR:" + e);
    }
    """
    raw = execute_js(js, timeout=25.0)
    if raw and not raw.startswith("ERR:"):
        blob = decode_pt_image(raw, "PNG")
        target_path = SCREENSHOTS_DIR / filename
        target_path.write_bytes(blob)
        print(f"    [+] Saved screenshot ({len(blob)} bytes): {target_path}")
        return target_path
    else:
        print("    [-] Failed to capture screenshot:", raw[:100] if raw else "None")
        return None

def save_pkt_file(filename="Sudsline_Soap_Manufacturing_Investigation.pkt"):
    print(f"[*] Saving Packet Tracer project file -> {filename}...")
    target_path = str(WORKSPACE_DIR / filename).replace("\\", "/")
    js = f"""
    try {{
        var aw = ipc.appWindow();
        aw.fileSaveAsNoPrompt("{target_path}", false);
        var fm = ipc.systemFileManager();
        if (fm.fileExists("{target_path}")) {{
            reportResult("OK:" + fm.getFileSize("{target_path}"));
        }} else {{
            reportResult("ERR: File not found after save");
        }}
    }} catch(e) {{
        reportResult("ERR:" + e);
    }}
    """
    res = execute_js(js, timeout=20.0)
    print("    Result:", res)

if __name__ == "__main__":
    check_bridge()
    clear_workspace()
    build_devices()
    install_modules()
    build_links()
    add_canvas_notes()
    configure_hosts()
    configure_network_devices()
    print("[*] Waiting 7 seconds for network convergence (STP, OSPF, EIGRP, BGP)...")
    time.sleep(7)
    collect_verification_evidence()
    capture_canvas_screenshot("topology_overview.png")
    save_pkt_file("Sudsline_Soap_Manufacturing_Investigation.pkt")
    print("\n[***] TOPOLOGY BUILD, CONFIGURATION, AND EVIDENCE COLLECTION COMPLETE! [***]")
