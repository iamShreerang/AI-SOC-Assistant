"""
Live Attack Log Generator — simulates attack logs matching real dataset formats.

Supported dataset formats:
  cic      — CIC-IDS2018 & CIC-APT-IDS2023 (network flow features)
  unsw     — UNSW-NB15 (network flow + protocol features)
  beth     — BETH dataset (Linux host/process logs)
  syslog   — Generic syslog (original format)

Usage:
    python log_generator.py                              # syslog, random attacks, 1/sec
    python log_generator.py --dataset cic               # CIC-IDS2018 format
    python log_generator.py --dataset unsw              # UNSW-NB15 format
    python log_generator.py --dataset beth              # BETH format
    python log_generator.py --dataset all               # cycle all formats
    python log_generator.py --dataset cic --scenario brute_force
    python log_generator.py --rate 3 --dataset unsw
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone

# Windows UTF-8 fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

KAFKA_BROKER = "localhost:9092"
KAFKA_TOPIC  = "raw-logs"


def ts() -> str:
    return datetime.now(timezone.utc).isoformat()

def rand_ip() -> str:
    return f"{random.randint(1,254)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"

def rand_internal_ip() -> str:
    return f"10.0.0.{random.randint(1, 50)}"

def rand_port() -> int:
    return random.randint(1024, 65535)

def rand_mac() -> str:
    return ":".join(f"{random.randint(0,255):02x}" for _ in range(6))


# ── CIC-IDS2018 / CIC-APT-IDS2023 format ─────────────────────────────────────
# Mimics network flow feature vector used by CIC datasets

CIC_LABELS = {
    "brute_force":          "Brute Force -Web",
    "sql_injection":        "SQL Injection",
    "port_scan":            "Infilteration",
    "privilege_escalation": "Infilteration",
    "data_exfiltration":    "Infilteration",
    "ransomware":           "Bot",
    "c2_beacon":            "Bot",
    "ddos":                 "DDoS attacks-LOIC-HTTP",
    "normal":               "Benign",
}

def cic_flow(src_ip: str, dst_ip: str, label: str, attack: bool = True) -> dict:
    proto = random.choice([6, 17])  # TCP=6, UDP=17
    fwd_pkts = random.randint(1, 500)
    bwd_pkts = random.randint(1, 200)
    fwd_bytes = fwd_pkts * random.randint(40, 1500)
    bwd_bytes = bwd_pkts * random.randint(40, 1500)
    duration = random.randint(0, 120000000)  # microseconds

    return {
        "source": "cic-flowmeter",
        "severity": "critical" if attack else "info",
        "message": f"Network flow: {src_ip} → {dst_ip} | Label: {label}",
        "timestamp": ts(),
        "raw": json.dumps({
            "Dst Port":            random.choice([22, 80, 443, 3306, 8080]) if attack else rand_port(),
            "Protocol":            proto,
            "Flow Duration":       duration,
            "Tot Fwd Pkts":        fwd_pkts,
            "Tot Bwd Pkts":        bwd_pkts,
            "TotLen Fwd Pkts":     fwd_bytes,
            "TotLen Bwd Pkts":     bwd_bytes,
            "Fwd Pkt Len Max":     random.randint(40, 1500),
            "Fwd Pkt Len Min":     random.randint(20, 40),
            "Fwd Pkt Len Mean":    round(fwd_bytes / max(fwd_pkts, 1), 2),
            "Bwd Pkt Len Max":     random.randint(40, 1500),
            "Bwd Pkt Len Mean":    round(bwd_bytes / max(bwd_pkts, 1), 2),
            "Flow Byts/s":         round(random.uniform(0, 1000000), 2),
            "Flow Pkts/s":         round(random.uniform(0, 10000), 2),
            "Flow IAT Mean":       round(random.uniform(0, 100000), 2),
            "Flow IAT Std":        round(random.uniform(0, 50000), 2),
            "Fwd IAT Mean":        round(random.uniform(0, 100000), 2),
            "Bwd IAT Mean":        round(random.uniform(0, 100000), 2),
            "Fwd PSH Flags":       random.randint(0, 1),
            "SYN Flag Cnt":        random.randint(0, 10) if attack else random.randint(0, 2),
            "RST Flag Cnt":        random.randint(0, 5),
            "ACK Flag Cnt":        random.randint(0, fwd_pkts),
            "URG Flag Cnt":        random.randint(0, 2) if attack else 0,
            "Init Fwd Win Byts":   random.randint(0, 65535),
            "Init Bwd Win Byts":   random.randint(0, 65535),
            "Src IP":              src_ip,
            "Dst IP":              dst_ip,
            "Label":               label,
        })
    }


def cic_brute_force(attacker: str, target: str) -> list[dict]:
    logs = [cic_flow(attacker, target, CIC_LABELS["brute_force"]) for _ in range(random.randint(6, 15))]
    logs.append(cic_flow(attacker, target, "Brute Force -SSH"))
    return logs

def cic_sql_injection(attacker: str, target: str) -> list[dict]:
    return [cic_flow(attacker, target, CIC_LABELS["sql_injection"]) for _ in range(random.randint(3, 8))]

def cic_infiltration(attacker: str, target: str) -> list[dict]:
    return [cic_flow(attacker, target, CIC_LABELS["port_scan"]) for _ in range(random.randint(4, 10))]

def cic_bot(attacker: str, target: str) -> list[dict]:
    return [cic_flow(attacker, target, CIC_LABELS["c2_beacon"]) for _ in range(random.randint(3, 7))]

def cic_ddos(attacker: str, target: str) -> list[dict]:
    return [cic_flow(attacker, target, CIC_LABELS["ddos"]) for _ in range(random.randint(5, 12))]


# ── UNSW-NB15 format ──────────────────────────────────────────────────────────
# Mimics UNSW-NB15 feature set

UNSW_CATEGORIES = {
    "brute_force":          "Backdoors",
    "sql_injection":        "Exploits",
    "port_scan":            "Reconnaissance",
    "privilege_escalation": "Shellcode",
    "data_exfiltration":    "Worms",
    "ransomware":           "Generic",
    "c2_beacon":            "Backdoors",
}

UNSW_PROTOS  = ["tcp", "udp", "icmp", "ospf", "arp"]
UNSW_STATES  = ["FIN", "INT", "CON", "REQ", "RST", "URN", "no"]
UNSW_SERVICES = ["-", "http", "ftp", "smtp", "dns", "ssh", "ftp-data", "irc"]

def unsw_record(src_ip: str, dst_ip: str, category: str) -> dict:
    proto = random.choice(UNSW_PROTOS)
    sbytes = random.randint(100, 100000)
    dbytes = random.randint(100, 50000)
    dur = round(random.uniform(0, 60), 6)

    return {
        "source": "unsw-sensor",
        "severity": "error" if category != "-" else "info",
        "message": f"UNSW flow: {src_ip}:{rand_port()} → {dst_ip}:{rand_port()} | {proto.upper()} | Category: {category}",
        "timestamp": ts(),
        "raw": json.dumps({
            "srcip":     src_ip,
            "sport":     rand_port(),
            "dstip":     dst_ip,
            "dsport":    random.choice([22, 80, 443, 21, 25, 53]),
            "proto":     proto,
            "state":     random.choice(UNSW_STATES),
            "dur":       dur,
            "sbytes":    sbytes,
            "dbytes":    dbytes,
            "sttl":      random.randint(1, 255),
            "dttl":      random.randint(1, 255),
            "sloss":     random.randint(0, 10),
            "dloss":     random.randint(0, 10),
            "service":   random.choice(UNSW_SERVICES),
            "Sload":     round(random.uniform(0, 1000000), 2),
            "Dload":     round(random.uniform(0, 1000000), 2),
            "Spkts":     random.randint(1, 500),
            "Dpkts":     random.randint(1, 200),
            "Swin":      random.randint(0, 65535),
            "Dwin":      random.randint(0, 65535),
            "ct_srv_src": random.randint(1, 50),
            "ct_dst_ltm": random.randint(1, 50),
            "ct_src_ltm": random.randint(1, 50),
            "ct_srv_dst": random.randint(1, 50),
            "is_sm_ips_ports": random.randint(0, 1),
            "attack_cat": category,
            "label":     0 if category == "-" else 1,
        })
    }

def unsw_brute_force(attacker: str, target: str) -> list[dict]:
    return [unsw_record(attacker, target, UNSW_CATEGORIES["brute_force"]) for _ in range(random.randint(5, 12))]

def unsw_recon(attacker: str, target: str) -> list[dict]:
    return [unsw_record(attacker, target, UNSW_CATEGORIES["port_scan"]) for _ in range(random.randint(4, 10))]

def unsw_exploits(attacker: str, target: str) -> list[dict]:
    return [unsw_record(attacker, target, UNSW_CATEGORIES["sql_injection"]) for _ in range(random.randint(3, 8))]

def unsw_shellcode(attacker: str, target: str) -> list[dict]:
    return [unsw_record(attacker, target, UNSW_CATEGORIES["privilege_escalation"]) for _ in range(random.randint(2, 6))]

def unsw_worm(attacker: str, target: str) -> list[dict]:
    targets = [rand_internal_ip() for _ in range(random.randint(3, 8))]
    return [unsw_record(attacker, t, UNSW_CATEGORIES["data_exfiltration"]) for t in targets]


# ── BETH dataset format ───────────────────────────────────────────────────────
# Mimics BETH (enterprise Linux host logs) — process/syscall based

BETH_PROCESSES = ["bash", "python3", "curl", "wget", "nc", "nmap", "ssh", "sudo", "chmod", "useradd"]
BETH_SYSCALLS  = ["execve", "open", "read", "write", "connect", "fork", "clone", "ptrace", "kill", "mmap"]

def beth_event(host_ip: str, user: str, evil: bool) -> dict:
    proc = random.choice(BETH_PROCESSES)
    syscall = random.choice(BETH_SYSCALLS)
    uid = 0 if evil else random.randint(1000, 2000)
    ppid = random.randint(1, 1000)
    pid = random.randint(1001, 9999)

    return {
        "source": "beth-host",
        "severity": "critical" if evil and uid == 0 else ("warning" if evil else "info"),
        "message": f"Host event on {host_ip}: {'[EVIL]' if evil else '[BENIGN]'} {proc} by uid={uid}",
        "timestamp": ts(),
        "raw": json.dumps({
            "processId":       pid,
            "parentProcessId": ppid,
            "userId":          uid,
            "mountNamespace":  random.randint(4026531840, 4026531850),
            "processName":     proc,
            "hostName":        host_ip,
            "eventId":         random.randint(1, 400),
            "eventName":       syscall,
            "stackAddresses":  [hex(random.randint(0x7f0000000000, 0x7fffffffffff)) for _ in range(3)],
            "argsNum":         random.randint(0, 5),
            "returnValue":     0 if not evil else random.choice([0, -1, -13]),
            "args": [
                {"name": "filename", "type": "const char*", "value": random.choice([
                    "/etc/shadow", "/etc/passwd", "/tmp/exploit", "/bin/bash",
                    "/root/.ssh/authorized_keys", "/var/log/auth.log"
                ]) if evil else f"/home/{user}/file.txt"}
            ],
            "sus":   1 if evil else 0,
            "evil":  1 if evil else 0,
        })
    }

def beth_privilege_escalation(attacker: str, target: str) -> list[dict]:
    user = random.choice(["www-data", "apache", "postgres", "nobody"])
    logs = [beth_event(target, user, evil=False) for _ in range(3)]
    logs += [beth_event(target, user, evil=True) for _ in range(random.randint(3, 7))]
    return logs

def beth_lateral_movement(attacker: str, target: str) -> list[dict]:
    logs = []
    for ip in [rand_internal_ip() for _ in range(random.randint(2, 5))]:
        logs += [beth_event(ip, "root", evil=True) for _ in range(random.randint(2, 4))]
    return logs

def beth_c2(attacker: str, target: str) -> list[dict]:
    logs = [beth_event(target, "root", evil=True) for _ in range(random.randint(4, 8))]
    return logs


# ── Syslog format (original) ──────────────────────────────────────────────────

def syslog_brute_force(attacker: str, target: str) -> list[dict]:
    user = random.choice(["root", "admin", "ubuntu", "svc_account"])
    logs = []
    for i in range(random.randint(8, 20)):
        logs.append({
            "source": "auth-server", "severity": "warning",
            "message": f"Failed SSH login for user '{user}' from {attacker} (attempt {i+1})",
            "timestamp": ts(),
            "raw": f"sshd[{random.randint(1000,9999)}]: Failed password for {user} from {attacker} port {rand_port()} ssh2",
        })
    logs.append({
        "source": "auth-server", "severity": "critical",
        "message": f"Brute force SUCCESS — '{user}' logged in from {attacker}",
        "timestamp": ts(),
        "raw": f"sshd[{random.randint(1000,9999)}]: Accepted password for {user} from {attacker} port {rand_port()} ssh2",
    })
    return logs

def syslog_sql_injection(attacker: str, target: str) -> list[dict]:
    payloads = ["' OR '1'='1", "'; DROP TABLE users--", "' UNION SELECT username,password FROM users--"]
    logs = []
    for p in payloads:
        logs.append({
            "source": "ids-sensor", "severity": "error",
            "message": f"SQL injection attempt from {attacker} on {target}",
            "timestamp": ts(),
            "raw": f"ALERT sql_injection SRC={attacker} DST={target} URI=/api/login payload=\"{p}\"",
        })
    logs.append({
        "source": "ids-sensor", "severity": "critical",
        "message": f"SQL injection SUCCESSFUL — DB dump from {attacker}",
        "timestamp": ts(),
        "raw": f"ALERT sql_injection_success SRC={attacker} DST={target} rows_returned=1500",
    })
    return logs

def syslog_port_scan(attacker: str, target: str) -> list[dict]:
    open_ports = random.sample([22, 80, 443, 3306, 5432, 8080], 3)
    return [
        {"source": "firewall-01", "severity": "warning",
         "message": f"Port scan from {attacker} → {target}", "timestamp": ts(),
         "raw": f"PORTSCAN SRC={attacker} DST={target} PORTS_PROBED=1024"},
        {"source": "ids-sensor", "severity": "error",
         "message": f"Exploitation attempt on {target}:{open_ports[0]} from {attacker}", "timestamp": ts(),
         "raw": f"EXPLOIT SRC={attacker} DST={target} PORT={open_ports[0]} CVE=CVE-2024-{random.randint(1000,9999)}"},
        {"source": "ids-sensor", "severity": "critical",
         "message": f"RCE on {target} — shell spawned by {attacker}", "timestamp": ts(),
         "raw": f"RCE SRC={attacker} DST={target} shell=/bin/bash pid={random.randint(1000,9999)}"},
    ]

def syslog_ransomware(attacker: str, target: str) -> list[dict]:
    return [
        {"source": "syslog", "severity": "warning",
         "message": f"Mass file encryption on {target}", "timestamp": ts(),
         "raw": f"inotify: mass rename /home/data/*.docx -> *.encrypted count=342"},
        {"source": "ids-sensor", "severity": "critical",
         "message": f"Ransomware detected on {target}", "timestamp": ts(),
         "raw": f"RANSOMWARE host={target} files_encrypted=1024 extension=.locked"},
        {"source": "firewall-01", "severity": "critical",
         "message": f"Ransomware C2 to {attacker} from {target}", "timestamp": ts(),
         "raw": f"C2_BEACON SRC={target} DST={attacker} DPT=8443 interval=30s"},
    ]

def syslog_c2(attacker: str, target: str) -> list[dict]:
    interval = random.choice([30, 60, 120])
    return [
        {"source": "firewall-01", "severity": "warning",
         "message": f"Periodic beacon from {target} → {attacker} every {interval}s", "timestamp": ts(),
         "raw": f"BEACON SRC={target} DST={attacker} DPT=443 interval={interval}s"},
        {"source": "ids-sensor", "severity": "critical",
         "message": f"Cobalt Strike C2 detected: {target} → {attacker}", "timestamp": ts(),
         "raw": f"C2_DETECTED SRC={target} DST={attacker} signature=cobaltstrike jitter=10%"},
    ]

def syslog_privilege_escalation(attacker: str, target: str) -> list[dict]:
    user = random.choice(["www-data", "apache", "nginx", "postgres"])
    return [
        {"source": "syslog", "severity": "warning",
         "message": f"Unusual sudo by '{user}' on {target}", "timestamp": ts(),
         "raw": f"sudo: {user} TTY=pts/0 PWD=/tmp USER=root COMMAND=/bin/bash"},
        {"source": "syslog", "severity": "critical",
         "message": f"Privilege escalation SUCCESS — '{user}' → root on {target}", "timestamp": ts(),
         "raw": f"sudo: pam_unix: session opened for user root by {user}(uid=0)"},
        {"source": "syslog", "severity": "critical",
         "message": f"Backdoor account created on {target}", "timestamp": ts(),
         "raw": f"useradd: new user name=backdoor UID=0 GID=0 shell=/bin/bash"},
    ]

def syslog_data_exfiltration(attacker: str, target: str) -> list[dict]:
    size_mb = random.randint(50, 500)
    return [
        {"source": "ids-sensor", "severity": "error",
         "message": f"Large outbound transfer {target} → {attacker} ({size_mb}MB)", "timestamp": ts(),
         "raw": f"OUTBOUND SRC={target} DST={attacker} DPT=443 BYTES={size_mb*1024*1024}"},
        {"source": "ids-sensor", "severity": "critical",
         "message": f"Sensitive file access before exfiltration on {target}", "timestamp": ts(),
         "raw": f"FILE_ACCESS path=/etc/shadow user=root src_ip={attacker} action=read"},
    ]


# ── Scenario registry per dataset ─────────────────────────────────────────────

DATASETS = {
    "cic": {
        "brute_force":          cic_brute_force,
        "sql_injection":        cic_sql_injection,
        "infiltration":         cic_infiltration,
        "bot":                  cic_bot,
        "ddos":                 cic_ddos,
    },
    "unsw": {
        "brute_force":          unsw_brute_force,
        "reconnaissance":       unsw_recon,
        "exploits":             unsw_exploits,
        "shellcode":            unsw_shellcode,
        "worm":                 unsw_worm,
    },
    "beth": {
        "privilege_escalation": beth_privilege_escalation,
        "lateral_movement":     beth_lateral_movement,
        "c2_beacon":            beth_c2,
    },
    "syslog": {
        "brute_force":          syslog_brute_force,
        "sql_injection":        syslog_sql_injection,
        "port_scan":            syslog_port_scan,
        "privilege_escalation": syslog_privilege_escalation,
        "data_exfiltration":    syslog_data_exfiltration,
        "ransomware":           syslog_ransomware,
        "c2_beacon":            syslog_c2,
    },
}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Attack log generator → Kafka")
    parser.add_argument("--rate",     type=float, default=1.0,   help="Logs per second (default: 1)")
    parser.add_argument("--dataset",  default="syslog",          help="Dataset format: cic | unsw | beth | syslog | all")
    parser.add_argument("--scenario", default="random",          help="Scenario name or 'random'")
    parser.add_argument("--broker",   default=KAFKA_BROKER,      help="Kafka broker")
    parser.add_argument("--topic",    default=KAFKA_TOPIC,       help="Kafka topic")
    args = parser.parse_args()

    if args.dataset != "all" and args.dataset not in DATASETS:
        print(f"❌ Unknown dataset '{args.dataset}'. Choose from: {list(DATASETS.keys()) + ['all']}")
        return

    try:
        producer = KafkaProducer(
            bootstrap_servers=args.broker,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        print(f"✅ Connected to Kafka at {args.broker}")
    except NoBrokersAvailable:
        print(f"❌ Could not connect to Kafka at {args.broker}. Is it running?")
        return

    interval = 1.0 / args.rate
    count = 0
    dataset_cycle = list(DATASETS.keys())
    cycle_idx = 0

    print(f"🚨 Publishing attack logs → '{args.topic}' | dataset={args.dataset} | rate={args.rate}/sec\n")

    try:
        while True:
            # pick dataset
            if args.dataset == "all":
                ds_name = dataset_cycle[cycle_idx % len(dataset_cycle)]
                cycle_idx += 1
            else:
                ds_name = args.dataset

            scenarios = DATASETS[ds_name]

            # pick scenario
            if args.scenario == "random" or args.scenario not in scenarios:
                fn = random.choice(list(scenarios.values()))
            else:
                fn = scenarios[args.scenario]

            attacker = rand_ip()
            target   = rand_internal_ip()
            logs     = fn(attacker, target)
            label    = fn.__name__.replace("_", " ").upper()

            print(f"\n{'─'*65}")
            print(f"  🔴 [{ds_name.upper()}] {label}")
            print(f"  Attacker: {attacker}  →  Target: {target}")
            print(f"{'─'*65}")

            for log in logs:
                producer.send(args.topic, value=log)
                count += 1
                sev = log["severity"].upper()
                print(f"  [{count:>4}] [{sev:>8}] {log['message']}")
                time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n⛔ Stopped. {count} logs published.")
    finally:
        producer.flush()
        producer.close()


if __name__ == "__main__":
    main()
