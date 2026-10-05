# Case Study 185: Sudsline Artisan Soap Manufacturing Network Investigation

**Capstone Diagnostics & Outage Remediation**  
*Course:* B.Tech CSE (Computer Networking & Cyber Security) — Semester II  
*Repository:* [sarthak-cn-ass](https://github.com/Danish1323/sarthak-cn-ass)

---

## 📌 Project Overview
Sudsline Artisan Soap Manufacturing runs three geographically dispersed sites:
1. **Head Office (HQ - Showroom & CAD Design):** Hosts Area 0 OSPF backbone and dual-ISP eBGP edge routing (AS 65000) peering with Primary ISP (AS 65001) and Secondary ISP (AS 65002).
2. **Curing & Batching Plant:** Legacy EIGRP (AS 100) operational technology (OT) network housing critical batch-monitoring terminals.
3. **Packaging Warehouse:** Inventory management and packaging automation connected via redundant primary (1 Gbps) and secondary (Serial) WAN circuits.

Over a 48-hour period following network re-cabling and maintenance, personnel reported intermittent disconnections and packet loss across all facilities. This project models, investigates, diagnoses, and completely remediates all five symptoms from scratch using Cisco Packet Tracer.

---

## 📁 Repository Artifacts & Deliverables

| File / Artifact | Description |
|:---|:---|
| [`Sudsline_Soap_Manufacturing_Investigation.pkt`](./Sudsline_Soap_Manufacturing_Investigation.pkt) | **Complete Cisco Packet Tracer Binary** — 17 devices, fully wired, configured, and converged. |
| [`Sudsline_Network_Investigation_Report.pdf`](./Sudsline_Network_Investigation_Report.pdf) | **Publication-Grade Technical Report (19 Pages)** — Detailed diagnostic breakdown, before/after CLI evidence, root-cause analysis table, and embedded Packet Tracer screenshots. |
| [`Sudsline_Network_Investigation_Report.html`](./Sudsline_Network_Investigation_Report.html) | Standalone interactive HTML report with embedded base64 screenshots. |
| [`generate_project.py`](./generate_project.py) | Master automation deployment script for Cisco Packet Tracer via IPC bridge. |
| [`build_full_report.py`](./build_full_report.py) | Compilation pipeline for HTML and PDF generation. |
| [`screenshots/`](./screenshots/) | High-resolution native canvas screenshots of the full enterprise topology and regional sites. |
| [`cli_evidence/`](./cli_evidence/) | 16 live Cisco IOS verification logs captured during simulation. |

---

## 🗺️ Network Topology Architecture

![Network Topology Overview](./screenshots/topology_overview.png)

---

## 🔍 Diagnostic Summary (Symptoms A – E)

| Sym. | Location | Observed Behavior | Root Cause | Corrective Fix |
|:---:|:---|:---|:---|:---|
| **A** | Plant Core Switch | Batch-monitoring terminals lose connectivity every 10–15 min; port toggles BLK/FWD; high TCNs. | Rogue unmanaged switch on access port Fa0/10 sending BPDUs; absence of BPDU Guard & PortFast causing CAM flushes. | Configured `spanning-tree portfast` and `bpduguard enable` on access ports; enabled `guard root` on core trunk. |
| **B** | HQ-Plant WAN Link | `show ip ospf neighbor` stuck in EXSTART/EXCHANGE; pings pass. | **MTU Mismatch**: HQ Edge at 1500 bytes vs Plant at 1400 bytes. OSPF DBD packets exceeded local MTU and were dropped. | Set `ip mtu 1500` on `Plant-Router` Gi0/1. Neighbor transitioned to `FULL/DR`. |
| **C** | Plant-Warehouse WAN | EIGRP successor route flaps in/out of routing table; bandwidth discrepancy. | **Feasibility Condition Violation**: Secondary serial link bandwidth was depressed (64 kbps), making $\text{RD} \ge \text{FD}$. No Feasible Successor existed, forcing ACTIVE query storms during micro-congestion. | Set `bandwidth 100000` on serial link and configured `variance 10` under EIGRP 100 to restore Feasible Successor ($\text{RD} < \text{FD}$). |
| **D** | HQ Internet Edge | eBGP to secondary ISP is 'Established', but partner route `198.18.50.0/24` is missing from `show ip bgp`. | Inbound prefix-list on HQ Edge permitted only `0.0.0.0/0`, silently discarding `198.18.50.0/24` via default implicit deny. | Added `ip prefix-list PARTNER-PREFIX permit 198.18.50.0/24` to inbound route-map and cleared BGP soft inbound. |
| **E** | Plant Access Layer | Wireshark capture reveals high rate of Gratuitous ARP replies for gateway `10.20.10.1` from various MACs. | **ARP Poisoning / Man-in-the-Middle (MitM) Attack**: Rogue host attempting industrial telemetry interception and DoS. | Enabled **Dynamic ARP Inspection (DAI)** and **DHCP Snooping** on VLAN 20 with trusted uplinks; enforced **Port Security**. |

---

## 🚀 End-to-End Connectivity Verification
- **HQ to Plant Batch Terminals:** `10.10.10.11` &rarr; `10.20.10.10` (100% Success, round-trip `<1ms`)
- **Plant to Warehouse Inventory:** `10.20.10.10` &rarr; `10.30.10.10` (100% Success, round-trip `<1ms`)
- **HQ to B2B Partner Portal:** `HQ-Edge-Router` &rarr; `198.18.50.10` (100% Success over eBGP)
- **HQ to Public Internet DNS:** `HQ-Edge-Router` &rarr; `8.8.8.8` (100% Success over eBGP)
