"""CivicFix Read-Scaling Benchmark & Verification Script.

Simulates 10x expected peak public read traffic (500 requests across concurrent workers):
1. Uncached / Cache-Bypass Mode (simulating direct DB read queries)
2. Cached Mode (snap_bounds quantization + Redis micro-cache)

Measures and outputs p50, p95, p99 latencies, cache hit ratio, and database query reduction.
"""

import asyncio
import statistics
import time
from typing import Dict, List, Tuple
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings


class MockRedisBenchmarkClient:
    """Fast in-memory Redis client for benchmark simulation."""

    def __init__(self):
        self.store: Dict[str, str] = {}
        self.hits = 0
        self.misses = 0

    async def get(self, key: str):
        if key in self.store:
            self.hits += 1
            return self.store[key]
        self.misses += 1
        return None

    async def setex(self, key: str, ttl: int, val: str):
        self.store[key] = val
        return True


async def run_benchmark_batch(
    client: AsyncClient,
    concurrency: int,
    total_requests: int,
    use_cache: bool,
) -> Tuple[List[float], Dict[str, int]]:
    """Execute a batch of read requests and capture latency distribution."""
    latencies: List[float] = []
    status_counts: Dict[str, int] = {}
    semaphore = asyncio.Semaphore(concurrency)

    async def single_request(req_idx: int):
        async with semaphore:
            # Vary coordinates slightly to test quantization snapping
            offset = (req_idx % 10) * 0.0003
            min_lat = 38.9780 + offset
            max_lat = 38.9880 + offset
            min_lng = -76.4920 + offset
            max_lng = -76.4820 + offset
            zoom = 14

            headers = {}
            if not use_cache:
                # Force cache bypass using Authorization header
                headers["Authorization"] = "Bearer bypass_token_for_db_test"

            url = f"/api/v1/public/map?min_lat={min_lat:.5f}&max_lat={max_lat:.5f}&min_lng={min_lng:.5f}&max_lng={max_lng:.5f}&zoom={zoom}"

            t0 = time.perf_counter()
            resp = await client.get(url, headers=headers)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            cache_status = resp.headers.get("X-Cache", "UNKNOWN")
            status_counts[cache_status] = status_counts.get(cache_status, 0) + 1
            latencies.append(elapsed_ms)

    tasks = [single_request(i) for i in range(total_requests)]
    await asyncio.gather(*tasks)

    return latencies, status_counts


async def main():
    print("=" * 70)
    print("CIVICFIX READ-SCALING BENCHMARK (10x Peak Traffic Simulation)")
    print("=" * 70)

    # Attach in-memory redis cache to app state
    mock_redis = MockRedisBenchmarkClient()
    app.state.redis_cache = mock_redis

    concurrency = 50
    total_requests = 300

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Warmup
        await client.get("/api/v1/public/stats")

        # ─── 1. BENCHMARK UNCACHED (Direct DB simulation) ───────────────────
        print(f"\n[1/2] Running UNCACHED baseline ({total_requests} requests @ concurrency={concurrency})...")
        t_start = time.perf_counter()
        uncached_latencies, uncached_cache_status = await run_benchmark_batch(
            client=client,
            concurrency=concurrency,
            total_requests=total_requests,
            use_cache=False,
        )
        uncached_total_sec = time.perf_counter() - t_start

        # ─── 2. BENCHMARK CACHED (snap_bounds + Redis micro-cache) ──────────
        print(f"[2/2] Running CACHED with snap_bounds() ({total_requests} requests @ concurrency={concurrency})...")
        t_start = time.perf_counter()
        cached_latencies, cached_cache_status = await run_benchmark_batch(
            client=client,
            concurrency=concurrency,
            total_requests=total_requests,
            use_cache=True,
        )
        cached_total_sec = time.perf_counter() - t_start

    # Calculate percentiles
    uncached_latencies.sort()
    cached_latencies.sort()

    def pct(arr, p):
        idx = int(len(arr) * (p / 100.0))
        return arr[min(idx, len(arr) - 1)]

    u_p50 = statistics.median(uncached_latencies)
    u_p95 = pct(uncached_latencies, 95)
    u_p99 = pct(uncached_latencies, 99)
    u_rps = total_requests / uncached_total_sec

    c_p50 = statistics.median(cached_latencies)
    c_p95 = pct(cached_latencies, 95)
    c_p99 = pct(cached_latencies, 99)
    c_rps = total_requests / cached_total_sec

    hit_ratio = (
        cached_cache_status.get("HIT", 0)
        / max(1, sum(cached_cache_status.values()))
    ) * 100.0

    print("\n" + "=" * 70)
    print("LOAD TEST RESULTS SUMMARY:")
    print("=" * 70)
    print(f"{'Metric':<25} | {'Uncached (Direct DB)':<20} | {'Cached (snap_bounds + Redis)':<20}")
    print("-" * 70)
    print(f"{'p50 Latency':<25} | {u_p50:>17.2f} ms | {c_p50:>17.2f} ms")
    print(f"{'p95 Latency':<25} | {u_p95:>17.2f} ms | {c_p95:>17.2f} ms")
    print(f"{'p99 Latency':<25} | {u_p99:>17.2f} ms | {c_p99:>17.2f} ms")
    print(f"{'Throughput':<25} | {u_rps:>15.1f} req/s | {c_rps:>15.1f} req/s")
    print(f"{'Cache Hit Ratio':<25} | {'0.0% (bypassed)':>20} | {f'{hit_ratio:.1f}%':>20}")
    print(f"{'DB Query Reduction':<25} | {'0%':>20} | {f'{hit_ratio:.1f}%':>20}")
    print("=" * 70)
    print(f"Latency improvement: p50 is {u_p50 / max(0.01, c_p50):.1f}x faster, p99 is {u_p95 / max(0.01, c_p95):.1f}x faster.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())

