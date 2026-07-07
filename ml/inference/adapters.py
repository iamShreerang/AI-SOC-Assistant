"""Integration adapters for Kafka, Spark, and JSON inputs.

These adapters ONLY transform incoming data into the ML input format.
They do NOT implement Kafka consumers, Spark sessions, or any I/O clients.

External services use them like:
    # Kafka consumer (in kafka/ module)
    from ml.inference.adapters import KafkaAdapter
    adapter = KafkaAdapter(engine)
    result = adapter.predict_from_kafka_message(raw_message_bytes)

    # Spark job (in spark/ module)
    from ml.inference.adapters import SparkAdapter
    adapter = SparkAdapter(engine)
    results = adapter.predict_from_spark_dataframe(spark_df.toPandas())

    # FastAPI route
    from ml.inference.adapters import JSONAdapter
    adapter = JSONAdapter(engine)
    result = adapter.predict_from_json(request_body_dict)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ml.inference.engine import InferenceEngine, PredictionOutput
from ml.utils.logger import get_logger

logger = get_logger(__name__)


class KafkaAdapter:
    """Transform Kafka message bytes/dicts into ML predictions.

    TODO (external/kafka): Kafka consumer should instantiate this adapter
    and call predict_from_kafka_message() for each consumed message.
    """

    def __init__(self, engine: InferenceEngine) -> None:
        self.engine = engine

    def predict_from_kafka_message(
        self, message: bytes | str | Dict
    ) -> Optional[PredictionOutput]:
        """Parse a Kafka message and return a prediction.

        Accepts raw bytes (JSON-encoded), a JSON string, or a dict.
        Returns None if the message cannot be parsed.
        """
        try:
            features = self._parse(message)
            return self.engine.predict_dict(features)
        except Exception as exc:
            logger.error("KafkaAdapter: failed to predict from message: %s", exc)
            return None

    def predict_from_kafka_batch(
        self, messages: List[bytes | str | Dict]
    ) -> List[Optional[PredictionOutput]]:
        """Process a batch of Kafka messages."""
        return [self.predict_from_kafka_message(m) for m in messages]

    @staticmethod
    def _parse(message: bytes | str | Dict) -> Dict:
        if isinstance(message, dict):
            return message
        if isinstance(message, bytes):
            message = message.decode("utf-8")
        return json.loads(message)


class SparkAdapter:
    """Transform Spark/Pandas DataFrames into ML predictions.

    TODO (external/spark): Spark streaming job should call
    predict_from_spark_dataframe() after converting a micro-batch to Pandas.
    The Spark job must NOT import pyspark here — only pass a Pandas DataFrame.
    """

    def __init__(self, engine: InferenceEngine) -> None:
        self.engine = engine

    def predict_from_spark_dataframe(
        self, pandas_df: pd.DataFrame
    ) -> List[PredictionOutput]:
        """Predict on a Pandas DataFrame converted from a Spark micro-batch.

        The Spark job should call: spark_df.toPandas() before passing here.
        """
        if pandas_df.empty:
            return []
        try:
            return self.engine.predict_dataframe(pandas_df)
        except Exception as exc:
            logger.error("SparkAdapter: prediction failed: %s", exc)
            return []

    def predict_from_spark_array(self, array: np.ndarray) -> List[PredictionOutput]:
        """Predict on a NumPy array built by the Spark feature engineering step."""
        try:
            return self.engine.predict_array(array)
        except Exception as exc:
            logger.error("SparkAdapter: array prediction failed: %s", exc)
            return []


class JSONAdapter:
    """Transform JSON request bodies into ML predictions.

    TODO (external/fastapi): FastAPI routes should use this adapter
    to handle /predict and /predict/batch endpoints.
    """

    def __init__(self, engine: InferenceEngine) -> None:
        self.engine = engine

    def predict_from_json(self, body: Dict[str, Any]) -> Optional[PredictionOutput]:
        """Predict from a single JSON feature dict."""
        try:
            features = body.get("features", body)
            return self.engine.predict_dict(features)
        except Exception as exc:
            logger.error("JSONAdapter: prediction failed: %s", exc)
            return None

    def predict_from_json_batch(self, body: Dict[str, Any]) -> List[Optional[PredictionOutput]]:
        """Predict from a batch JSON body: {"samples": [{...}, {...}]}."""
        samples = body.get("samples", [])
        results = []
        for sample in samples:
            try:
                results.append(self.engine.predict_dict(sample))
            except Exception as exc:
                logger.error("JSONAdapter: batch item failed: %s", exc)
                results.append(None)
        return results
