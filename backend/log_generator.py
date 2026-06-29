"""
log_generator.py
================
Synthetic security-log generator for the AI SOC Assistant project.

Each public function accepts (attacker_ip, target_ip) and returns a
list of dicts with at minimum:
    source   : str   – originating dataset / sub-system
    severity : str   – CRITICAL | HIGH | MEDIUM | LOW | INFO
    message  : str   – human-readable alert line
    raw      : str   – JSON string (structured) or syslog-style line

The raw JSON fields are kept dataset-authentic so downstream Spark
feature engineering and the ML pipeline receive familiar column names.

Kafka integration is wired through send_log(); that function is a no-op
when KafkaProducer is None (mock mode used by the test harness).
"""

from __future__ import annotations

import json
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Any

# ---------------------------------------------------------------------------
# Optional Kafka – graceful fallback when not installed
# ---------------------------------------------------------------------------
try:
    from kafka import KafkaProducer
    from kafka.errors import NoBrokersAvailable
except Exception:
    KafkaProducer = None  # type: ignore
    NoBrokersAvailable = Exception

_PRODUCER: Any = None
KAFKA_TOPIC_MAP: dict[str, str] = {
    "CIC": "cic-logs",
    "UNSW": "unsw-logs",
    "BETH": "beth-logs",
    "SYSLOG": "syslog-logs",
}


def _get_producer(bootstrap: str = "localhost:9092"):
    global _PRODUCER
    if KafkaProducer is None:
        return None
    if _PRODUCER is None:
        try:
            _PRODUCER = KafkaProducer(
                bootstrap_servers=[bootstrap],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except NoBrokersAvailable:
            _PRODUCER = None
    return _PRODUCER


def send_log(log: dict, topic: str = "soc-logs") -> None:
    """Push a single log dict to Kafka; silent no-op if unavailable."""
    producer = _get_producer()
    if producer:
        try:
            producer.send(topic, log)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _ts(offset_seconds: float = 0.0) -> str:
    """ISO-8601 UTC timestamp, optionally shifted by offset_seconds."""
    t = datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)
    return t.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _rand_port(exclude_well_known: bool = False) -> int:
    low = 1024 if exclude_well_known else 1
    return random.randint(low, 65535)


def _rand_proto() -> str:
    return random.choice(["TCP", "UDP", "ICMP"])


def _rand_bytes() -> int:
    return random.randint(40, 65535)


def _make_log(source: str, severity: str, message: str, raw: Any) -> dict:
    raw_str = json.dumps(raw) if isinstance(raw, dict) else str(raw)
    return {
        "timestamp": _ts(),
        "source": source,
        "severity": severity,
        "message": message,
        "raw": raw_str,
    }


# ===========================================================================
# CIC-IDS2018 / CIC-APT-IDS2023
# ===========================================================================

def cic_brute_force(attacker: str, target: str, n: int = 8) -> list[dict]:
    """SSH / FTP brute-force — high-frequency short-duration flows."""
    logs = []
    for i in range(n):
        raw = {
            "Timestamp": _ts(i * 0.5),
            "Dst IP": target,
            "Src IP": attacker,
            "Dst Port": random.choice([22, 21, 3389]),
            "Protocol": "TCP",
            "Flow Duration": random.randint(100_000, 500_000),
            "Tot Fwd Pkts": random.randint(4, 12),
            "Tot Bwd Pkts": random.randint(1, 4),
            "TotLen Fwd Pkts": random.randint(200, 800),
            "TotLen Bwd Pkts": random.randint(50, 300),
            "Flow Byts/s": round(random.uniform(500, 5000), 2),
            "Flow Pkts/s": round(random.uniform(10, 100), 2),
            "SYN Flag Cnt": 1,
            "RST Flag Cnt": random.randint(0, 1),
            "Label": "Brute Force",
        }
        logs.append(_make_log(
            source="CIC-IDS2018",
            severity="HIGH",
            message=(
                f"Brute-force attempt from {attacker} → {target}:"
                f"{raw['Dst Port']} ({raw['Tot Fwd Pkts']} pkts)"
            ),
            raw=raw,
        ))
    return logs


def cic_ddos(attacker: str, target: str, n: int = 10) -> list[dict]:
    """DDoS (SYN-flood / UDP-flood) — massive packet rates, short flows."""
    logs = []
    for i in range(n):
        proto = random.choice(["TCP", "UDP"])
        raw = {
            "Timestamp": _ts(i * 0.1),
            "Dst IP": target,
            "Src IP": attacker,
            "Dst Port": random.choice([80, 443, 53]),
            "Protocol": proto,
            "Flow Duration": random.randint(1000, 50_000),
            "Tot Fwd Pkts": random.randint(500, 5000),
            "Tot Bwd Pkts": random.randint(0, 10),
            "TotLen Fwd Pkts": random.randint(30_000, 200_000),
            "TotLen Bwd Pkts": random.randint(0, 500),
            "Flow Byts/s": round(random.uniform(50_000, 1_000_000), 2),
            "Flow Pkts/s": round(random.uniform(1_000, 50_000), 2),
            "SYN Flag Cnt": random.randint(0, 1) if proto == "TCP" else 0,
            "Label": "DDoS",
        }
        logs.append(_make_log(
            source="CIC-IDS2018",
            severity="CRITICAL",
            message=(
                f"DDoS flood from {attacker} → {target}:{raw['Dst Port']}"
                f" [{proto}] {raw['Flow Pkts/s']:.0f} pkts/s"
            ),
            raw=raw,
        ))
    return logs


def cic_bot(attacker: str, target: str, n: int = 6) -> list[dict]:
    """Bot / C2 beacon — periodic low-volume encrypted flows."""
    logs = []
    for i in range(n):
        raw = {
            "Timestamp": _ts(i * 30),
            "Dst IP": target,
            "Src IP": attacker,
            "Dst Port": random.choice([443, 8443, 4444, 6667]),
            "Protocol": "TCP",
            "Flow Duration": random.randint(200_000, 2_000_000),
            "Tot Fwd Pkts": random.randint(2, 8),
            "Tot Bwd Pkts": random.randint(2, 8),
            "TotLen Fwd Pkts": random.randint(100, 600),
            "TotLen Bwd Pkts": random.randint(100, 600),
            "Flow Byts/s": round(random.uniform(50, 500), 2),
            "Idle Mean": round(random.uniform(1e6, 5e6), 2),
            "Label": "Bot",
        }
        logs.append(_make_log(
            source="CIC-IDS2018",
            severity="HIGH",
            message=(
                f"Bot C2 beacon from {attacker} → {target}:{raw['Dst Port']}"
                f" every ~30 s"
            ),
            raw=raw,
        ))
    return logs


def cic_sql_injection(attacker: str, target: str, n: int = 5) -> list[dict]:
    """SQL injection probe — short HTTP flows with payload signatures."""
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users;--",
        "' UNION SELECT NULL,NULL--",
        "admin'--",
        "1' AND SLEEP(5)--",
    ]
    logs = []
    for i in range(n):
        raw = {
            "Timestamp": _ts(i * 2),
            "Dst IP": target,
            "Src IP": attacker,
            "Dst Port": 80,
            "Protocol": "TCP",
            "Flow Duration": random.randint(50_000, 300_000),
            "Tot Fwd Pkts": random.randint(3, 10),
            "Tot Bwd Pkts": random.randint(2, 8),
            "TotLen Fwd Pkts": random.randint(300, 2000),
            "TotLen Bwd Pkts": random.randint(500, 5000),
            "Payload Hint": payloads[i % len(payloads)],
            "Label": "SQL Injection",
        }
        logs.append(_make_log(
            source="CIC-IDS2018",
            severity="HIGH",
            message=(
                f"SQL-injection attempt from {attacker} → {target}:80"
                f" payload={payloads[i % len(payloads)]!r}"
            ),
            raw=raw,
        ))
    return logs


def cic_infiltration(attacker: str, target: str, n: int = 5) -> list[dict]:
    """Infiltration — lateral movement flows after initial compromise."""
    ports = [445, 135, 139, 3389, 5985]
    logs = []
    for i in range(n):
        raw = {
            "Timestamp": _ts(i * 10),
            "Dst IP": target,
            "Src IP": attacker,
            "Dst Port": ports[i % len(ports)],
            "Protocol": "TCP",
            "Flow Duration": random.randint(500_000, 5_000_000),
            "Tot Fwd Pkts": random.randint(20, 200),
            "Tot Bwd Pkts": random.randint(20, 200),
            "TotLen Fwd Pkts": random.randint(5000, 50_000),
            "TotLen Bwd Pkts": random.randint(5000, 50_000),
            "Label": "Infiltration",
        }
        logs.append(_make_log(
            source="CIC-IDS2018",
            severity="CRITICAL",
            message=(
                f"Infiltration lateral-move {attacker} → {target}:{ports[i % len(ports)]}"
            ),
            raw=raw,
        ))
    return logs


# ===========================================================================
# UNSW-NB15
# ===========================================================================

def unsw_recon(attacker: str, target: str, n: int = 8) -> list[dict]:
    """Network reconnaissance — port scans, OS fingerprinting."""
    logs = []
    for i in range(n):
        raw = {
            "srcip": attacker,
            "dstip": target,
            "sport": _rand_port(exclude_well_known=True),
            "dsport": random.randint(1, 1024),
            "proto": _rand_proto(),
            "dur": round(random.uniform(0.0, 0.5), 6),
            "sbytes": random.randint(40, 200),
            "dbytes": random.randint(0, 100),
            "Spkts": random.randint(1, 5),
            "Dpkts": random.randint(0, 3),
            "state": random.choice(["RST", "FIN", "CON"]),
            "attack_cat": "Reconnaissance",
            "Label": 1,
        }
        logs.append(_make_log(
            source="UNSW-NB15",
            severity="MEDIUM",
            message=(
                f"Reconnaissance scan from {attacker} → {target}:{raw['dsport']}"
                f" proto={raw['proto']}"
            ),
            raw=raw,
        ))
    return logs


def unsw_shellcode(attacker: str, target: str, n: int = 4) -> list[dict]:
    """Shellcode injection flows — anomalous payload entropy."""
    logs = []
    for i in range(n):
        raw = {
            "srcip": attacker,
            "dstip": target,
            "sport": _rand_port(exclude_well_known=True),
            "dsport": random.choice([21, 22, 80, 445]),
            "proto": "TCP",
            "dur": round(random.uniform(0.5, 5.0), 6),
            "sbytes": random.randint(500, 4000),
            "dbytes": random.randint(200, 2000),
            "Spkts": random.randint(5, 30),
            "Dpkts": random.randint(3, 20),
            "state": "CON",
            "ct_srv_dst": random.randint(1, 10),
            "attack_cat": "Shellcode",
            "Label": 1,
        }
        logs.append(_make_log(
            source="UNSW-NB15",
            severity="CRITICAL",
            message=(
                f"Shellcode injection detected {attacker} → {target}:{raw['dsport']}"
            ),
            raw=raw,
        ))
    return logs


def unsw_exploits(attacker: str, target: str, n: int = 5) -> list[dict]:
    """Exploit attempts — CVE-style service exploits."""
    cves = [
        "CVE-2017-0144",   # EternalBlue
        "CVE-2021-44228",  # Log4Shell
        "CVE-2019-0708",   # BlueKeep
        "CVE-2018-11776",  # Struts2 RCE
        "CVE-2022-26134",  # Confluence RCE
    ]
    logs = []
    for i in range(n):
        raw = {
            "srcip": attacker,
            "dstip": target,
            "sport": _rand_port(exclude_well_known=True),
            "dsport": random.choice([445, 443, 80, 3389, 8080]),
            "proto": "TCP",
            "dur": round(random.uniform(0.1, 3.0), 6),
            "sbytes": random.randint(1000, 10_000),
            "dbytes": random.randint(500, 5000),
            "Spkts": random.randint(10, 80),
            "Dpkts": random.randint(5, 40),
            "state": "CON",
            "cve": cves[i % len(cves)],
            "attack_cat": "Exploits",
            "Label": 1,
        }
        logs.append(_make_log(
            source="UNSW-NB15",
            severity="CRITICAL",
            message=(
                f"Exploit attempt {cves[i % len(cves)]} from {attacker} → "
                f"{target}:{raw['dsport']}"
            ),
            raw=raw,
        ))
    return logs


def unsw_worm(attacker: str, target: str, n: int = 6) -> list[dict]:
    """Worm propagation — self-replicating scan + infect flows."""
    logs = []
    for i in range(n):
        raw = {
            "srcip": attacker,
            "dstip": target,
            "sport": _rand_port(exclude_well_known=True),
            "dsport": random.choice([445, 139, 135]),
            "proto": "TCP",
            "dur": round(random.uniform(0.05, 1.0), 6),
            "sbytes": random.randint(300, 3000),
            "dbytes": random.randint(100, 1500),
            "Spkts": random.randint(3, 20),
            "Dpkts": random.randint(1, 10),
            "state": random.choice(["CON", "RST"]),
            "ct_dst_sport_ltm": random.randint(1, 100),
            "attack_cat": "Worms",
            "Label": 1,
        }
        logs.append(_make_log(
            source="UNSW-NB15",
            severity="CRITICAL",
            message=(
                f"Worm propagation detected {attacker} → {target}:{raw['dsport']}"
                f" ({raw['ct_dst_sport_ltm']} hosts targeted)"
            ),
            raw=raw,
        ))
    return logs


def unsw_brute_force(attacker: str, target: str, n: int = 7) -> list[dict]:
    """UNSW-flavoured brute-force (Fuzzers / credential stuffing)."""
    logs = []
    for i in range(n):
        raw = {
            "srcip": attacker,
            "dstip": target,
            "sport": _rand_port(exclude_well_known=True),
            "dsport": random.choice([22, 23, 21, 3306]),
            "proto": "TCP",
            "dur": round(random.uniform(0.01, 0.3), 6),
            "sbytes": random.randint(100, 600),
            "dbytes": random.randint(50, 300),
            "Spkts": random.randint(2, 8),
            "Dpkts": random.randint(1, 4),
            "state": random.choice(["RST", "FIN"]),
            "ct_src_dport_ltm": random.randint(10, 500),
            "attack_cat": "Fuzzers",
            "Label": 1,
        }
        logs.append(_make_log(
            source="UNSW-NB15",
            severity="HIGH",
            message=(
                f"Brute-force/fuzzer from {attacker} → {target}:{raw['dsport']}"
                f" attempts={raw['ct_src_dport_ltm']}"
            ),
            raw=raw,
        ))
    return logs


# ===========================================================================
# BETH (Linux kernel audit logs)
# ===========================================================================

def beth_privilege_escalation(attacker: str, target: str, n: int = 5) -> list[dict]:
    """BETH — sudo / SUID abuse privilege escalation events."""
    syscalls = ["execve", "setuid", "setgid", "capset", "ptrace"]
    commands = ["sudo su", "chmod u+s /bin/bash", "pkexec bash", "su root", "newgrp root"]
    logs = []
    for i in range(n):
        raw = {
            "timestamp": _ts(i * 3),
            "host": target,
            "user": f"user{random.randint(1000, 9999)}",
            "pid": random.randint(1000, 60000),
            "ppid": random.randint(1, 1000),
            "syscall": syscalls[i % len(syscalls)],
            "comm": commands[i % len(commands)],
            "exe": f"/usr/bin/{syscalls[i % len(syscalls)]}",
            "auid": random.randint(1000, 9999),
            "success": random.choice([True, False]),
            "evil": True,
            "sus": True,
        }
        logs.append(_make_log(
            source="BETH",
            severity="CRITICAL",
            message=(
                f"Privilege escalation on {target}: "
                f"user={raw['user']} cmd={raw['comm']!r} "
                f"syscall={raw['syscall']}"
            ),
            raw=raw,
        ))
    return logs


def beth_lateral_movement(attacker: str, target: str, n: int = 5) -> list[dict]:
    """BETH — SSH / rsync lateral movement across hosts."""
    tools = ["ssh", "scp", "rsync", "nc", "socat"]
    logs = []
    for i in range(n):
        raw = {
            "timestamp": _ts(i * 15),
            "host": target,
            "user": f"svc{random.randint(10, 99)}",
            "pid": random.randint(1000, 60000),
            "ppid": random.randint(1, 1000),
            "syscall": "execve",
            "comm": tools[i % len(tools)],
            "exe": f"/usr/bin/{tools[i % len(tools)]}",
            "argv": f"{tools[i % len(tools)]} {attacker}",
            "auid": random.randint(1000, 9999),
            "success": True,
            "evil": True,
            "sus": True,
        }
        logs.append(_make_log(
            source="BETH",
            severity="HIGH",
            message=(
                f"Lateral movement from {attacker} via {tools[i % len(tools)]}"
                f" on host {target}"
            ),
            raw=raw,
        ))
    return logs


def beth_c2(attacker: str, target: str, n: int = 6) -> list[dict]:
    """BETH — C2 beacon via curl/wget/python calling back home."""
    agents = ["curl", "wget", "python3", "bash", "perl"]
    logs = []
    for i in range(n):
        raw = {
            "timestamp": _ts(i * 60),
            "host": target,
            "user": "root",
            "pid": random.randint(1000, 60000),
            "ppid": random.randint(1, 1000),
            "syscall": "connect",
            "comm": agents[i % len(agents)],
            "exe": f"/usr/bin/{agents[i % len(agents)]}",
            "argv": f"{agents[i % len(agents)]} http://{attacker}/beacon",
            "remote_addr": attacker,
            "remote_port": random.choice([80, 443, 4444, 8080]),
            "evil": True,
            "sus": True,
        }
        logs.append(_make_log(
            source="BETH",
            severity="CRITICAL",
            message=(
                f"C2 beacon from {target} → {attacker}:{raw['remote_port']}"
                f" via {agents[i % len(agents)]}"
            ),
            raw=raw,
        ))
    return logs


# ===========================================================================
# SYSLOG (RFC-3164 / RFC-5424 style)
# ===========================================================================

def _syslog_line(facility: int, severity_code: int, host: str,
                 program: str, pid: int, msg: str,
                 ts: str | None = None) -> str:
    """Assemble a minimal syslog line."""
    pri = facility * 8 + severity_code
    ts = ts or datetime.now(timezone.utc).strftime("%b %d %H:%M:%S")
    return f"<{pri}>{ts} {host} {program}[{pid}]: {msg}"


def syslog_brute_force(attacker: str, target: str, n: int = 8) -> list[dict]:
    """sshd failed-password lines — classic brute-force pattern."""
    logs = []
    users = ["root", "admin", "ubuntu", "pi", "oracle", "postgres"]
    for i in range(n):
        user = users[i % len(users)]
        port = _rand_port(exclude_well_known=True)
        pid = random.randint(10000, 59999)
        msg = (
            f"Failed password for {'invalid user ' if i % 3 == 0 else ''}"
            f"{user} from {attacker} port {port} ssh2"
        )
        raw = _syslog_line(4, 6, target, "sshd", pid, msg)
        logs.append(_make_log(
            source="SYSLOG/sshd",
            severity="HIGH",
            message=f"SSH brute-force: {attacker} → {target} user={user}",
            raw=raw,
        ))
    return logs


def syslog_sql_injection(attacker: str, target: str, n: int = 5) -> list[dict]:
    """Apache/nginx access-log lines containing SQLi payloads."""
    payloads = [
        "/index.php?id=1' OR '1'='1",
        "/login?user=admin'--&pass=x",
        "/search?q=' UNION SELECT 1,2,3--",
        "/api/user?id=1;DROP TABLE users--",
        "/wp-login.php?redirect_to=' AND SLEEP(5)--",
    ]
    logs = []
    for i in range(n):
        pid = random.randint(10000, 59999)
        code = random.choice([200, 400, 403, 500])
        payload = payloads[i % len(payloads)]
        msg = (
            f'{attacker} - - [{_ts()}] '
            f'"GET {payload} HTTP/1.1" {code} {random.randint(200, 5000)} '
            f'"-" "sqlmap/1.7"'
        )
        raw = _syslog_line(1, 5, target, "apache2", pid, msg)
        logs.append(_make_log(
            source="SYSLOG/apache2",
            severity="HIGH",
            message=f"SQL-injection in HTTP request from {attacker}: {payload}",
            raw=raw,
        ))
    return logs


def syslog_port_scan(attacker: str, target: str, n: int = 9) -> list[dict]:
    """iptables DROP entries for a rapid port scan."""
    logs = []
    for i in range(n):
        dst_port = random.randint(1, 1024)
        pid = random.randint(1000, 9999)
        msg = (
            f"[UFW BLOCK] IN=eth0 OUT= SRC={attacker} DST={target} "
            f"PROTO=TCP SPT={_rand_port(True)} DPT={dst_port} SYN"
        )
        raw = _syslog_line(4, 4, target, "kernel", pid, msg)
        logs.append(_make_log(
            source="SYSLOG/kernel",
            severity="MEDIUM",
            message=f"Port scan blocked: {attacker} → {target}:{dst_port}",
            raw=raw,
        ))
    return logs


def syslog_ransomware(attacker: str, target: str, n: int = 6) -> list[dict]:
    """auditd lines showing mass file renames (.locked extension)."""
    exts = [".locked", ".encrypted", ".enc", ".crypt", ".crypto"]
    paths = ["/home/user/Documents", "/var/www/html", "/opt/app/data",
             "/srv/files", "/mnt/share", "/home/user/Desktop"]
    logs = []
    for i in range(n):
        pid = random.randint(10000, 59999)
        ext = exts[i % len(exts)]
        path = paths[i % len(paths)]
        fname = f"file{random.randint(100, 999)}.dat"
        msg = (
            f"type=SYSCALL arch=x86_64 syscall=rename pid={pid} "
            f"success=yes exe=/tmp/.x a0={path}/{fname} "
            f"a1={path}/{fname}{ext}"
        )
        raw = _syslog_line(4, 2, target, "auditd", pid, msg)
        logs.append(_make_log(
            source="SYSLOG/auditd",
            severity="CRITICAL",
            message=(
                f"Ransomware file encryption on {target}: "
                f"{path}/{fname} → {fname}{ext}"
            ),
            raw=raw,
        ))
    return logs


def syslog_c2(attacker: str, target: str, n: int = 6) -> list[dict]:
    """Cron-scheduled curl beacons — classic C2 persistence."""
    intervals = [60, 120, 300, 600]
    logs = []
    for i in range(n):
        interval = intervals[i % len(intervals)]
        pid = random.randint(10000, 59999)
        port = random.choice([80, 443, 8080, 4444])
        msg = (
            f"CMD (curl -s http://{attacker}:{port}/check?id="
            f"{random.randint(1000,9999)} > /dev/null 2>&1)"
        )
        raw = _syslog_line(9, 6, target, "CRON", pid, msg)
        logs.append(_make_log(
            source="SYSLOG/cron",
            severity="CRITICAL",
            message=(
                f"C2 beacon scheduled: {target} → {attacker}:{port} "
                f"every {interval}s"
            ),
            raw=raw,
        ))
    return logs


def syslog_privilege_escalation(attacker: str, target: str, n: int = 5) -> list[dict]:
    """sudo and su abuse lines."""
    cmds = [
        "sudo /bin/bash",
        "sudo chmod 777 /etc/shadow",
        "sudo -u root /tmp/payload",
        "su -c 'bash -i' root",
        "sudo visudo",
    ]
    logs = []
    for i in range(n):
        pid = random.randint(10000, 59999)
        user = f"user{random.randint(1000, 9999)}"
        cmd = cmds[i % len(cmds)]
        msg = f"{user} : TTY=pts/0 ; PWD=/tmp ; USER=root ; COMMAND={cmd}"
        raw = _syslog_line(4, 5, target, "sudo", pid, msg)
        logs.append(_make_log(
            source="SYSLOG/sudo",
            severity="CRITICAL",
            message=(
                f"Privilege escalation on {target}: user={user} cmd={cmd!r}"
            ),
            raw=raw,
        ))
    return logs


def syslog_data_exfiltration(attacker: str, target: str, n: int = 5) -> list[dict]:
    """Large outbound transfers flagged by iptables / DLP daemon."""
    methods = ["scp", "rsync", "curl", "nc", "python3 -c 'socket'"]
    paths = ["/etc/passwd", "/etc/shadow", "/var/lib/postgresql/data",
             "/home/user/.ssh/id_rsa", "/opt/app/config.env"]
    logs = []
    for i in range(n):
        pid = random.randint(10000, 59999)
        method = methods[i % len(methods)]
        fpath = paths[i % len(paths)]
        size_mb = round(random.uniform(10, 500), 1)
        msg = (
            f"OUTBOUND {method} from {target} to {attacker} "
            f"file={fpath} size={size_mb}MB FLAGGED"
        )
        raw = _syslog_line(4, 2, target, "dlp-agent", pid, msg)
        logs.append(_make_log(
            source="SYSLOG/dlp-agent",
            severity="CRITICAL",
            message=(
                f"Data exfiltration: {fpath} ({size_mb} MB) → {attacker}"
                f" via {method}"
            ),
            raw=raw,
        ))
    return logs
