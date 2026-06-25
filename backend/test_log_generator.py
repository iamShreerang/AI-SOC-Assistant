"""Test log generator output without Kafka."""
import json, sys, types

# Mock kafka so log_generator imports without Kafka installed
kafka_mock = types.ModuleType("kafka")
kafka_mock.KafkaProducer = None
errors_mock = types.ModuleType("kafka.errors")
errors_mock.NoBrokersAvailable = Exception
sys.modules["kafka"] = kafka_mock
sys.modules["kafka.errors"] = errors_mock

from log_generator import (
    cic_brute_force, cic_ddos, cic_bot, cic_sql_injection, cic_infiltration,
    unsw_recon, unsw_shellcode, unsw_exploits, unsw_worm, unsw_brute_force,
    beth_privilege_escalation, beth_lateral_movement, beth_c2,
    syslog_brute_force, syslog_sql_injection, syslog_port_scan,
    syslog_ransomware, syslog_c2, syslog_privilege_escalation, syslog_data_exfiltration,
)

attacker = "45.23.11.98"
target   = "10.0.0.14"

TESTS = {
    "CIC-IDS2018 / CIC-APT-IDS2023": [
        ("brute_force",   cic_brute_force),
        ("ddos",          cic_ddos),
        ("bot/c2",        cic_bot),
        ("sql_injection",  cic_sql_injection),
        ("infiltration",  cic_infiltration),
    ],
    "UNSW-NB15": [
        ("reconnaissance", unsw_recon),
        ("shellcode",      unsw_shellcode),
        ("exploits",       unsw_exploits),
        ("worm",           unsw_worm),
        ("brute_force",    unsw_brute_force),
    ],
    "BETH": [
        ("privilege_escalation", beth_privilege_escalation),
        ("lateral_movement",     beth_lateral_movement),
        ("c2_beacon",            beth_c2),
    ],
    "SYSLOG": [
        ("brute_force",          syslog_brute_force),
        ("sql_injection",        syslog_sql_injection),
        ("port_scan",            syslog_port_scan),
        ("ransomware",           syslog_ransomware),
        ("c2_beacon",            syslog_c2),
        ("privilege_escalation", syslog_privilege_escalation),
        ("data_exfiltration",    syslog_data_exfiltration),
    ],
}

for dataset, scenarios in TESTS.items():
    print(f"\n{'='*65}")
    print(f"  DATASET: {dataset}")
    print(f"{'='*65}")
    for name, fn in scenarios:
        logs = fn(attacker, target)
        s = logs[0]
        print(f"\n  [{name}] — {len(logs)} logs generated")
        print(f"    source   : {s['source']}")
        print(f"    severity : {s['severity']}")
        print(f"    message  : {s['message']}")
        raw = s["raw"]
        if raw.startswith("{"):
            r = json.loads(raw)
            keys = list(r.keys())[:8]
            label = r.get("Label") or r.get("attack_cat") or r.get("evil")
            print(f"    raw keys : {keys}")
            print(f"    label    : {label}")
        else:
            print(f"    raw      : {raw[:100]}")

print("\n\nAll scenarios generated successfully.")
