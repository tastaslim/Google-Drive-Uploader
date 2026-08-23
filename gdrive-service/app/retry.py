"""Exponential backoff with jitter for retryable Google API errors."""
import logging
import random
import time
from typing import Callable, TypeVar

from googleapiclient.errors import HttpError

from app.config import RETRYABLE_HTTP_STATUS_CODES, RETRYABLE_REASON_CODES, settings

logger = logging.getLogger("gdrive_service.retry")

ResultType = TypeVar("ResultType")


def isRetryableHttpError(error: HttpError) -> bool:
    statusCode = getattr(error.resp, "status", None)
    if statusCode not in RETRYABLE_HTTP_STATUS_CODES:
        return False
    try:
        reasons = {detail.get("reason") for detail in error.error_details} if hasattr(error, "error_details") else set()
    except Exception:
        reasons = set()
    if statusCode == 403 and reasons and not (reasons & RETRYABLE_REASON_CODES):
        return False
    return True


def computeBackoffSeconds(attempt: int) -> float:
    exponential = settings.baseBackoffSeconds * (2 ** attempt)
    capped = min(exponential, settings.maxBackoffSeconds)
    return capped * (0.5 + random.random())


def callWithRetry(operation: Callable[[], ResultType], operationName: str = "drive_operation") -> ResultType:
    lastError: Exception | None = None
    for attempt in range(settings.maxRetries):
        try:
            return operation()
        except HttpError as httpError:
            lastError = httpError
            if not isRetryableHttpError(httpError):
                raise
            sleepSeconds = computeBackoffSeconds(attempt)
            logger.warning(
                "Retryable error on %s (attempt %d/%d): %s. Backing off %.2fs",
                operationName, attempt + 1, settings.maxRetries, httpError, sleepSeconds,
            )
            time.sleep(sleepSeconds)
        except (ConnectionError, TimeoutError) as transientError:
            lastError = transientError
            sleepSeconds = computeBackoffSeconds(attempt)
            logger.warning(
                "Transient error on %s (attempt %d/%d): %s. Backing off %.2fs",
                operationName, attempt + 1, settings.maxRetries, transientError, sleepSeconds,
            )
            time.sleep(sleepSeconds)
    assert lastError is not None
    raise lastError
