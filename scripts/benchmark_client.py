import argparse
import json
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests



def gerar_payload(i):
    return {
        "nome": f"Cliente Teste {i}",
        "email": f"benchmark_{i}_{time.time_ns()}@example.com",
        "cpf": f"9{i:010d}"[-11:],
        "cidade": random.choice(["Santa Maria", "Porto Alegre", "Pelotas"]),
        "idade": random.randint(18, 80),
    }


def worker(base_url, operation, index):
    start = time.perf_counter()
    try:
        if operation == "read":
            cliente_id = random.randint(1, 50000)
            response = requests.get(f"{base_url}/api/clientes/{cliente_id}", timeout=10)
        else:
            response = requests.post(
                f"{base_url}/api/clientes",
                json=gerar_payload(index),
                timeout=10,
            )
        elapsed_ms = (time.perf_counter() - start) * 1000
        return response.status_code, elapsed_ms
    except requests.RequestException:
        return 0, (time.perf_counter() - start) * 1000


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:5000")
    parser.add_argument("--clients", type=int, default=100)
    parser.add_argument("--requests", type=int, default=1000)
    parser.add_argument("--read-percent", type=int, default=50)
    args = parser.parse_args()

    operations = [
        "read" if random.random() < args.read_percent / 100 else "write"
        for _ in range(args.requests)
    ]

    start = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=args.clients) as executor:
        futures = [executor.submit(worker, args.url, op, i) for i, op in enumerate(operations)]
        for future in as_completed(futures):
            results.append(future.result())
    elapsed = time.perf_counter() - start

    latencies = [ms for status, ms in results if status != 0]
    successful = [status for status, _ in results if 200 <= status < 300]
    failed = len(results) - len(successful)

    summary = {
        "requests": len(results),
        "successful": len(successful),
        "failed": failed,
        "duration_s": round(elapsed, 3),
        "throughput_req_s": round(len(results) / elapsed, 2),
        "avg_latency_ms": round(statistics.mean(latencies), 2) if latencies else None,
        "p95_latency_ms": round(statistics.quantiles(latencies, n=100)[94], 2) if len(latencies) >= 20 else None,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
