import csv
import os
import time
import threading
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE_URL = "https://pokeapi.co/api/v2/pokemon/{}"
IMAGE_DIR = Path("images")
RESULTS_FILE = "results.csv"
TOTALS = [100, 500, 1000]
WORKERS = [2, 4, 8]
RUNS = 10


def ensure_dirs():
    IMAGE_DIR.mkdir(exist_ok=True)


def clear_images():
    if not IMAGE_DIR.exists():
        return
    for f in IMAGE_DIR.glob("*.png"):
        try:
            f.unlink()
        except FileNotFoundError:
            pass
        except PermissionError:
            time.sleep(0.1)
            try:
                f.unlink()
            except Exception:
                pass


def get_and_save(pokemon_id):
    try:
        r = requests.get(BASE_URL.format(pokemon_id), timeout=15)
        r.raise_for_status()
        data = r.json()

        img_url = data["sprites"]["front_default"]
        if not img_url:
            return

        img = requests.get(img_url, timeout=15)
        img.raise_for_status()

        with open(IMAGE_DIR / f"{pokemon_id}.png", "wb") as f:
            f.write(img.content)

    except Exception as e:
        print(f"Erro no pokémon {pokemon_id}: {e}")


def sequential(ids):
    for pokemon_id in ids:
        get_and_save(pokemon_id)


def run_threading(ids, workers):
    threads = []
    for pokemon_id in ids:
        t = threading.Thread(target=get_and_save, args=(pokemon_id,))
        threads.append(t)
        t.start()

        if len(threads) >= workers:
            for th in threads:
                th.join()
            threads = []

    for th in threads:
        th.join()


def run_multiprocessing(ids, workers):
    with Pool(processes=workers) as pool:
        pool.map(get_and_save, ids)


def run_futures(ids, workers):
    with ThreadPoolExecutor(max_workers=workers) as executor:
        list(executor.map(get_and_save, ids))


def measure(fn, runs=RUNS):
    times = []
    for _ in range(runs):
        clear_images()
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return round(sum(times) / len(times), 2)


def main():
    ensure_dirs()
    results = []

    for total in TOTALS:
        ids = list(range(1, total + 1))
        print(f"\n=== {total} pokémons ===")

        avg = measure(lambda: sequential(ids))
        results.append({"abordagem": "Sequential", "workers": "-", "total": total, "media_s": avg})
        print(f"  Sequential: {avg}s")

        for w in WORKERS:
            avg = measure(lambda w=w: run_threading(ids, w))
            results.append({"abordagem": "Threading", "workers": w, "total": total, "media_s": avg})
            print(f"  Threading-{w}: {avg}s")

        for w in WORKERS:
            avg = measure(lambda w=w: run_multiprocessing(ids, w))
            results.append({"abordagem": "Multiprocessing", "workers": w, "total": total, "media_s": avg})
            print(f"  Multiprocessing-{w}: {avg}s")

        for w in WORKERS:
            avg = measure(lambda w=w: run_futures(ids, w))
            results.append({"abordagem": "concurrent.futures", "workers": w, "total": total, "media_s": avg})
            print(f"  Futures-{w}: {avg}s")

    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["abordagem", "workers", "total", "media_s"])
        writer.writeheader()
        writer.writerows(results)

    print("\n\n=== RESULTADO FINAL ===")
    print(f"{'Abordagem':<22} {'Workers':<10} {'Total':<8} {'Média (s)'}")
    print("-" * 55)
    for r in results:
        print(f"{r['abordagem']:<22} {str(r['workers']):<10} {r['total']:<8} {r['media_s']}")
    print(f"\nSalvo em {RESULTS_FILE}")


if __name__ == "__main__":
    main()