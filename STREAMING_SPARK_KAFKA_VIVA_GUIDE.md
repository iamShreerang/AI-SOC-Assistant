# ⚡ AI SOC Assistant — Big Data Pipeline (Kafka & Spark) Viva Guide

> **Official Role**: **Ayush Dandge** — **`Big Data Pipeline`**

---

## 🎯 1. 30-Second Elevator Pitch for Ayush's Role

> *"In this project, my primary role was designing and building the **Big Data Pipeline**. I architected the real-time log ingestion and stream processing engine using **Apache Kafka** for decoupled message queuing and **Apache Spark Structured Streaming** for micro-batch processing. I implemented the data normalization layer (`feature_mapper.py`), structured schema enforcement (`_LOG_SCHEMA`), the heuristic threat rules engine (`threat_rules.py`), fault-tolerant checkpointing, and high-throughput HTTP ingestion into our backend REST services."*

---

## 🏗️ 2. Big Data Streaming Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                1. LOG GENERATION LAYER                                 │
│  streaming/sample_logs/generate.py & streaming/kafka/producer.py                       │
│  • Reads UNSW-NB15 flow datasets or generates synthetic network flow records           │
│  • Serializes JSON payload → Pushes to Kafka Broker                                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ (Port 9092)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              2. MESSAGE BROKER (KAFKA)                                 │
│  streaming/docker-compose.yml                                                          │
│  • Zookeeper Service (Port 2181) — Coordinates Kafka cluster state & metadata          │
│  • Kafka Service (Port 9092) — Topic: 'unsw-logs' (Auto-created by kafka-init container) │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ (Consumer Strategy: Subscribe to 'unsw-logs')
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       3. STREAM PROCESSING ENGINE (PYSPARK)                            │
│  streaming/spark/streaming_job.py                                                      │
│  • SparkSession with spark-sql-kafka-0-10 package                                      │
│  • Reads streaming DataFrames via spark.readStream                                    │
│  • Schema Parsing: F.from_json(col("value"), _LOG_SCHEMA, {"mode": "PERMISSIVE"})      │
│  • Micro-batch Trigger: 5-second processing windows                                    │
└──────────────┬────────────────────────────┬────────────────────────────┬───────────────┘
               │                            │                            │
               ▼                            ▼                            ▼
┌────────────────────────────┐┌────────────────────────────┐┌───────────────────────────┐
│     4A. FEATURE MAPPER     ││  4B. CNN-LSTM INFERENCE    ││   4C. HEURISTIC THREAT    │
│ feature_mapper.py          ││ ml/inference/predictor.py  ││       RULES ENGINE        │
│ Normalizes 39 UNSW features││ PyTorch Neural Network     ││ threat_rules.py           │
│ Maps raw keys to model schema│ Evaluates anomaly score   ││ DDoS, Exfiltration, Scans │
└──────────────┬─────────────┘└─────────────┬──────────────┘└─────────────┬─────────────┘
               │                            │                            │
               └────────────────────────────┼────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              5. BACKEND INGESTION CLIENT                               │
│  streaming/backend_client.py                                                           │
│  • Transmits stream logs & alerts via HTTP POST → FastAPI /ingest/*                    │
│  • Emits heartbeat status every 30s to service_heartbeats                              │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 3. File-by-File Directory & Technical Purpose

### A. Infrastructure & Configuration
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`streaming/docker-compose.yml`** | Defines Docker containers for **Zookeeper** (port `2181`), **Kafka** (port `9092`), and **`kafka-init`** (runs `kafka-topics.sh` on startup to auto-create topic `unsw-logs` with 1 partition and replication factor 1). |
| **`streaming/config.py`** | Central pipeline configuration. Loads environment variables: <br>• `KAFKA_BROKER = "localhost:9092"`<br>• `KAFKA_INPUT_TOPIC = "unsw-logs"`<br>• `SPARK_BATCH_INTERVAL = 5` (seconds)<br>• `SPARK_CHECKPOINT_DIR = "streaming/checkpoint"`. |

### B. Kafka Producer & Generator
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`streaming/kafka/producer.py`** | **Kafka Log Producer**. Reads UNSW-NB15 JSONL sample files, serializes each flow record into UTF-8 JSON bytes, and publishes records continuously into topic `unsw-logs`. Handles broker connection retries. |
| **`streaming/sample_logs/generate.py`** | **Synthetic Log Generator**. Generates realistic random flow logs (Normal, Exploits, DoS, Fuzzers, Reconnaissance) with live UTC timestamps. Supports direct streaming via `--kafka` flag. |

### C. Spark Streaming Core (`streaming/spark/`)
| File Path | Description & Viva Importance |
| :--- | :--- |
| **`streaming/spark/streaming_job.py`** | **Main Spark Execution Entry Point**. <br>• Initializes `SparkSession` with `spark-sql-kafka-0-10_2.12` package.<br>• Defines `_LOG_SCHEMA` (StructType of 45+ network metrics).<br>• Runs `_kafka_stream()` with `startingOffsets="earliest"` and `mode="PERMISSIVE"`.<br>• Invokes `foreachBatch(_process_batch)` to pass DataFrame micro-batches to the ML Predictor & Threat Engine.<br>• Spawns background thread `_heartbeat_loop()` sending heartbeats to backend. |
| **`streaming/spark/feature_mapper.py`** | **Data Normalization Layer**. Preprocesses incoming heterogeneous log formats (e.g. converting raw keys like `Src IP`, `TotLen Fwd Pkts` into model features like `srcip`, `sbytes`). Ensures data types match PyTorch model expectations. |
| **`streaming/spark/threat_rules.py`** | **Deterministic Threat Rules Engine**. Evaluates heuristic rules against each micro-batch: <br>1. **DDoS Attack**: Packet rate > 10,000/sec.<br>2. **Data Exfiltration**: Outbound bytes > 1,000,000.<br>3. **Port Scanning**: Destination ports > 50 in short time window.<br>4. **Repeat Attacker**: Single IP triggering > 5 anomalies.<br>5. **Suspicious Service**: Malicious protocol/service combinations. |
| **`streaming/spark/metrics.py`** | **In-Memory Streaming Performance Tracker**. Calculates live metrics: total requests processed, requests per second (RPS), average ML inference latency (ms), attack vs. normal counts. |
| **`streaming/backend_client.py`** | **Backend Ingestion Client**. Handles robust REST communication with FastAPI (`POST /ingest/logs`, `/ingest/alerts`, `/ingest/heartbeat`). Implements 2-second timeout and retry logic. |

---

## 🔬 4. Deep-Dive Concepts & Performance Engineering

### 1. Micro-Batching Trigger & Processing Execution
Spark Structured Streaming uses a **Micro-Batch Execution Model**:
```python
query = (
    parsed_df.writeStream
    .foreachBatch(_process_batch)
    .option("checkpointLocation", SPARK_CHECKPOINT_DIR)
    .trigger(processingTime=f"{SPARK_BATCH_INTERVAL} seconds")
    .start()
)
```
- Every 5 seconds (`SPARK_BATCH_INTERVAL`), Spark queries Kafka for new offsets, collects records into a micro-batch DataFrame, passes it to `_process_batch`, and commits offset progress to the checkpoint directory.

### 2. Schema Enforcement & PERMISSIVE Parsing Mode
Raw JSON streams from Kafka can contain corrupted records or missing fields. We enforce a explicit `StructType` (`_LOG_SCHEMA`) with **`PERMISSIVE`** mode:
```python
parsed = raw.select(F.from_json(F.col("value").cast("string"), _LOG_SCHEMA, {"mode": "PERMISSIVE"}).alias("data"))
```
- **PERMISSIVE Mode**: Prevents corrupted or misformatted JSON records from crashing the entire streaming query. Invalid fields are set to `null` while valid fields are safely extracted.

### 3. Offsets & Fault Tolerance (`SPARK_CHECKPOINT_DIR`)
- **Fault Tolerance**: Spark records read offsets in `streaming/checkpoint/offsets/`. If Spark crashes or restarts, it reads the checkpoint file to resume exactly where it left off without duplicating or losing data.
- **Starting Offsets (`startingOffsets="earliest"`)**: Forces Spark to process all messages sitting on the Kafka topic starting from offset 0, ensuring zero log loss even if the producer started before Spark.

### 4. Sliding Windowing for Sequence Models
The PyTorch CNN-LSTM neural network expects sequences of 10 consecutive flow records (`seq_len = 10`). In `_process_batch`, records are ordered by timestamp and grouped into sliding windows of length 10 before invoking `predictor.predict_batch()`.

---

## ❓ 5. Top 20 Viva Questions & Answers for Big Data Pipeline

### Q1: What was your specific contribution to this project?
**Answer:** I engineered the **Big Data Pipeline**. I set up the Apache Kafka ingestion broker in Docker, developed the PySpark Structured Streaming consumer (`streaming_job.py`), built the feature mapping layer (`feature_mapper.py`) for data normalization, implemented the heuristic threat detection engine (`threat_rules.py`), configured checkpoint fault-tolerance, and built the HTTP ingestion client (`backend_client.py`).

### Q2: Why did you choose Apache Kafka for log ingestion instead of traditional message queues like RabbitMQ?
**Answer:** Kafka is a distributed, append-only commit log designed for high-throughput, sequential disk I/O. Unlike RabbitMQ (which deletes messages once acknowledged), Kafka retains messages on disk by offsets. This allows multiple downstream consumers (Spark, long-term archival, auditing) to replay streams at different speeds independently without data loss.

### Q3: What is the difference between Apache Spark DStreams and Spark Structured Streaming?
**Answer:** DStreams were built on RDDs and processed micro-batches as discrete objects without schema awareness. Structured Streaming is built on the Spark SQL engine and DataFrames. It provides event-time processing, automatic schema optimization via the Catalyst Optimizer, watermarking for out-of-order data, and seamless integration with ML models.

### Q4: How does Spark Structured Streaming integrate with Apache Kafka?
**Answer:** We use the `spark-sql-kafka-0-10` connector package. Spark acts as a Kafka consumer, connecting to broker `localhost:9092`, subscribing to topic `unsw-logs`, and continuously polling for new topic partition offsets.

### Q5: How do you handle schema evolution and malformed JSON records from Kafka?
**Answer:** We define a strict PySpark `StructType` (`_LOG_SCHEMA`) and use `F.from_json(..., {"mode": "PERMISSIVE"})`. In `PERMISSIVE` mode, if a field is missing or malformed, Spark parses valid fields into the DataFrame and sets corrupted elements to `null` rather than failing the micro-batch query.

### Q6: How does fault tolerance work in your Spark streaming job?
**Answer:** Fault tolerance is achieved through **Write-Ahead Logging (WAL) and Checkpointing**. We specify `.option("checkpointLocation", "streaming/checkpoint")`. Spark records the exact Kafka topic partition offsets processed in each batch. Upon restart, Spark reads the checkpoint directory and resumes processing from the exact uncommitted offset.

### Q7: Explain `startingOffsets="earliest"` vs `startingOffsets="latest"`.
**Answer:** `startingOffsets="latest"` only reads messages produced *after* the Spark query starts, ignoring existing unread topic messages. `startingOffsets="earliest"` forces Spark to start reading from offset 0 of the Kafka topic, ensuring that all log records sent before Spark started are processed.

### Q8: What is the function of `foreachBatch` in your streaming job?
**Answer:** `foreachBatch(_process_batch)` allows us to execute custom arbitrary code (such as passing DataFrames to PyTorch ML models, running threat rules, and sending HTTP POST payloads to FastAPI) on the output DataFrame of each micro-batch.

### Q9: How do you feed network flow features into the CNN-LSTM PyTorch model inside Spark?
**Answer:** In `_process_batch`, the PySpark micro-batch DataFrame is converted into a list of row dictionaries. `feature_mapper.py` normalizes raw keys into 39 numerical features, reshapes the data into sequence tensors of shape `(batch_size, 10, 39)`, and passes them to PyTorch `predictor.predict_batch()`.

### Q10: How does your rule-based engine (`threat_rules.py`) complement the ML model?
**Answer:** Machine learning models excel at detecting unknown anomalies, but can suffer from false positives. Our threat rules engine evaluates deterministic heuristics (e.g., packet rate > 10,000 for DDoS, outbound bytes > 1MB for exfiltration). Combining both guarantees high-precision alerts for known attack signatures while retaining ML sensitivity for zero-day threats.

### Q11: What performance metrics do you track in the pipeline?
**Answer:** In `metrics.py`, we track:
1. **Total Requests Processed**
2. **Requests Per Second (RPS)**
3. **Average ML Inference Latency (ms)**
4. **Anomalies vs Normal Traffic Count**
5. **Threat Rules Triggered Count**

### Q12: What is Zookeeper's role in your Kafka setup?
**Answer:** Zookeeper manages Kafka cluster state, tracks broker health, maintains topic partition leader assignments, and handles cluster notification updates.

### Q13: What happens if the FastAPI backend goes down while Spark is running?
**Answer:** In `backend_client.py`, HTTP POST requests have explicit timeouts (2 seconds) wrapped in `try...except` blocks. If the backend is temporarily unavailable, Spark logs a warning, skips the failed HTTP post, and continues processing micro-batches without crashing the streaming job.

### Q14: Why is the micro-batch interval set to 5 seconds (`SPARK_BATCH_INTERVAL = 5`)?
**Answer:** 5 seconds balances low latency with computational efficiency. It gives enough time for 500+ records to accumulate, allowing the CNN-LSTM model to process sequence windows (`seq_len = 10`) in batches while maintaining real-time SOC updates.

### Q15: How would you scale this pipeline to handle 100,000 logs per second?
**Answer:**
1. **Kafka**: Increase topic `unsw-logs` partitions from 1 to 10+ and deploy a multi-broker Kafka cluster.
2. **Spark**: Deploy Spark on a distributed YARN or Kubernetes cluster with multiple worker nodes. Each worker task will consume from a distinct Kafka partition in parallel.
3. **Model Inference**: Run PyTorch inference on GPU-enabled worker nodes (`device="cuda"`).
