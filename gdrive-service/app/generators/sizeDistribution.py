"""Solves for how many large files (streamed synthetically, see
app/generators/largeFileStream.py) must be mixed into a batch of `count`
files so the batch's actual mean lands on the caller's requested average —
scaling with `count` rather than using a fixed number of large files
regardless of batch size. Large files are spread across multiple bucket
sizes (not collapsed into a single bucket) using fixed ratios per band, so a
150MB average still produces a 50MB/100MB/500MB mix, just sized to `count`."""
import random
from dataclasses import dataclass

from app.config import settings

SMALL_FILE_MAX_BYTES = 10 * 1024 * 1024  # <10MB

LARGE_FILE_BUCKET_BYTES = {
    "50MB": 50 * 1024 * 1024,
    "100MB": 100 * 1024 * 1024,
    "500MB": 500 * 1024 * 1024,
    "1GB": 1 * 1024 * 1024 * 1024,
    "5GB": 5 * 1024 * 1024 * 1024,
}

# Small files are uniformly sized between the configured min/max (default
# 1KB-2MB), so their expected mean is the midpoint of that range.
_SMALL_FILE_MEAN_BYTES = (settings.minFileSizeBytes + settings.maxFileSizeBytes) / 2


@dataclass(frozen=True)
class SizeDistributionPlan:
    smallFileCount: int
    largeFileCountsByBucket: dict[str, int]

    @property
    def totalLargeFileCount(self) -> int:
        return sum(self.largeFileCountsByBucket.values())


# Each band names a "combo" of 1-2 smaller buckets (blended by a fixed
# count ratio, e.g. 50MB:100MB = 2:3) that acts as a single point of known
# weighted-mean size, plus one larger bucket. The requested average is
# bracketed between (small-file-mean or combo-mean) and the larger bucket,
# solved by exact two-point linear interpolation for the total large-file
# count, and that count is split between the combo's own buckets by its
# fixed ratio — so the result always keeps 2-3 distinct sizes represented
# (matching the original multi-bucket blend) while still landing on the
# exact requested average, and scaling correctly with `count`.
_BANDS: list[tuple[int, dict[str, int], str]] = [
    (10 * 1024 * 1024, {}, "50MB"),
    (50 * 1024 * 1024, {}, "50MB"),
    (150 * 1024 * 1024, {"50MB": 2, "100MB": 3}, "500MB"),
    (500 * 1024 * 1024, {"100MB": 2, "500MB": 3}, "1GB"),
    (1 * 1024 * 1024 * 1024, {"500MB": 2, "1GB": 3}, "5GB"),
]
_TOP_BAND_COMBO = {"1GB": 2, "5GB": 3}  # used when the average exceeds every band above


def _pickBand(averageFileSizeBytes: int) -> tuple[dict[str, int], str]:
    for bandCeilingBytes, comboWeights, hiBucket in _BANDS:
        if averageFileSizeBytes <= bandCeilingBytes:
            return comboWeights, hiBucket
    # Above the top explicit band: blend the two largest buckets by a fixed
    # ratio instead of a combo + separate hi-bucket (there's nothing larger
    # than 5GB to act as the "hi" point).
    return {}, max(LARGE_FILE_BUCKET_BYTES, key=lambda name: LARGE_FILE_BUCKET_BYTES[name])


def _splitByRatio(total: int, weights: dict[str, int]) -> dict[str, int]:
    """Splits `total` across `weights`'s keys by their ratio, using
    largest-remainder rounding so the parts sum to exactly `total`."""
    totalWeight = sum(weights.values())
    rawShares = {name: total * weight / totalWeight for name, weight in weights.items()}
    result = {name: int(share) for name, share in rawShares.items()}
    remainder = total - sum(result.values())
    order = sorted(rawShares, key=lambda name: rawShares[name] - result[name], reverse=True)
    for name in order[:remainder]:
        result[name] += 1
    return result


def planSizeDistribution(count: int, averageFileSizeBytes: int) -> SizeDistributionPlan:
    """Picks the band for the requested average (a small "combo" of 1-2
    smaller bucket sizes blended by a fixed ratio, plus one larger bucket),
    then solves exactly — via linear interpolation between the combo's
    weighted-mean size and the larger bucket's size — for how many large
    files (split across the combo's buckets by ratio, plus the larger
    bucket) are needed so the batch mean lands on the requested average.
    Always keeps multiple bucket sizes represented and scales correctly
    with `count` (unlike a fixed absolute count regardless of batch size)."""
    if count <= 0:
        return SizeDistributionPlan(smallFileCount=0, largeFileCountsByBucket={})

    if averageFileSizeBytes <= _SMALL_FILE_MEAN_BYTES:
        return SizeDistributionPlan(smallFileCount=count, largeFileCountsByBucket={})

    comboWeights, hiBucketName = _pickBand(averageFileSizeBytes)
    hiBytes = LARGE_FILE_BUCKET_BYTES[hiBucketName]

    if not comboWeights:
        # No combo point (average below the smallest bucket, or above the
        # top band): bracket directly between small-file-mean and hiBucket.
        loBytes = _SMALL_FILE_MEAN_BYTES
        hiShare = (averageFileSizeBytes - loBytes) / (hiBytes - loBytes) if hiBytes != loBytes else 1.0
        hiShare = min(1.0, max(0.0, hiShare))
        hiCount = round(count * hiShare)
        smallFileCount = count - hiCount
        largeFileCountsByBucket = {hiBucketName: hiCount} if hiCount > 0 else {}
        return SizeDistributionPlan(smallFileCount=smallFileCount, largeFileCountsByBucket=largeFileCountsByBucket)

    comboTotalWeight = sum(comboWeights.values())
    comboMeanBytes = sum(
        LARGE_FILE_BUCKET_BYTES[name] * weight for name, weight in comboWeights.items()
    ) / comboTotalWeight

    if averageFileSizeBytes <= comboMeanBytes:
        # Bracket between small-file-mean and the combo's weighted mean.
        loBytes = _SMALL_FILE_MEAN_BYTES
        comboShare = (averageFileSizeBytes - loBytes) / (comboMeanBytes - loBytes)
        comboShare = min(1.0, max(0.0, comboShare))
        comboCount = round(count * comboShare)
        smallFileCount = count - comboCount
        largeFileCountsByBucket = _splitByRatio(comboCount, comboWeights) if comboCount > 0 else {}
    else:
        # Bracket between the combo's weighted mean and the larger bucket.
        hiShare = (averageFileSizeBytes - comboMeanBytes) / (hiBytes - comboMeanBytes)
        hiShare = min(1.0, max(0.0, hiShare))
        hiCount = round(count * hiShare)
        comboCount = count - hiCount
        smallFileCount = 0
        largeFileCountsByBucket = _splitByRatio(comboCount, comboWeights) if comboCount > 0 else {}
        if hiCount > 0:
            largeFileCountsByBucket[hiBucketName] = largeFileCountsByBucket.get(hiBucketName, 0) + hiCount

    largeFileCountsByBucket = {name: n for name, n in largeFileCountsByBucket.items() if n > 0}
    smallFileCount = count - sum(largeFileCountsByBucket.values())

    return SizeDistributionPlan(smallFileCount=smallFileCount, largeFileCountsByBucket=largeFileCountsByBucket)


# A bucket's actual file size is randomized within +/-20% of its nominal
# value rather than being exactly 50MB/1GB/etc every time.
_BUCKET_SIZE_JITTER_FRACTION = 0.2


def buildSizeAssignments(plan: SizeDistributionPlan, seed: int) -> list[tuple[str, int]]:
    """Expands a SizeDistributionPlan into one (bucketLabel, sizeBytes) entry
    per file, shuffled so large files are spread across the job rather than
    clustered at the start. bucketLabel is "small" or one of
    LARGE_FILE_BUCKET_BYTES's keys."""
    rng = random.Random(seed)
    assignments: list[tuple[str, int]] = []

    for _ in range(plan.smallFileCount):
        assignments.append(("small", 0))  # actual small size chosen per-file by the existing generators

    for bucketName, bucketCount in plan.largeFileCountsByBucket.items():
        nominalBytes = LARGE_FILE_BUCKET_BYTES[bucketName]
        for _ in range(bucketCount):
            jitter = rng.uniform(1 - _BUCKET_SIZE_JITTER_FRACTION, 1 + _BUCKET_SIZE_JITTER_FRACTION)
            assignments.append((bucketName, int(nominalBytes * jitter)))

    rng.shuffle(assignments)
    return assignments
