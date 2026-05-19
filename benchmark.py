import csv
import os
import time
import threading
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

# URL base da PokéAPI para buscar dados por ID
BASE_URL = "https://pokeapi.co/api/v2/pokemon/{}"

# Diretório onde as imagens baixadas serão armazenadas
IMAGE_DIR = Path("images")

# Arquivo de saída com os resultados do benchmark
RESULTS_FILE = "results.csv"

# Configurações do benchmark: tamanhos de carga, número de workers e repetições
TOTALS = [100, 500, 1000]
WORKERS = [2, 4, 8]
RUNS = 10


def ensure_dirs():
    """Garante que o diretório de imagens existe antes de iniciar os testes."""
    IMAGE_DIR.mkdir(exist_ok=True)


def clear_images():
    """Remove todas as imagens baixadas anteriormente para garantir condições idênticas entre execuções."""
    if not IMAGE_DIR.exists():
        return
    for f in IMAGE_DIR.glob("*.png"):
        try:
            f.unlink()
        except FileNotFoundError:
            # Arquivo já removido por outro processo (condição de corrida no Windows)
            pass
        except PermissionError:
            # Arquivo ainda em uso; aguarda brevemente e tenta novamente
            time.sleep(0.1)
            try:
                f.unlink()
            except Exception:
                pass


def get_and_save(pokemon_id):
    """Faz a requisição à PokéAPI, obtém a URL da imagem e salva em disco."""
    try:
        # Busca os dados do Pokémon com timeout de 15 segundos
        r = requests.get(BASE_URL.format(pokemon_id), timeout=15)
        r.raise_for_status()  # Lança exceção para erros HTTP (4xx, 5xx)
        data = r.json()

        # Extrai a URL da imagem frontal padrão do campo sprites
        img_url = data["sprites"]["front_default"]
        if not img_url:
            return  # Ignora Pokémon sem imagem disponível

        # Baixa o conteúdo da imagem com timeout de 15 segundos
        img = requests.get(img_url, timeout=15)
        img.raise_for_status()

        # Salva a imagem em disco usando o ID como nome do arquivo
        with open(IMAGE_DIR / f"{pokemon_id}.png", "wb") as f:
            f.write(img.content)

    except Exception as e:
        # Registra o erro sem interromper a execução
        print(f"Erro no pokémon {pokemon_id}: {e}")


def sequential(ids):
    """Executa o download de forma sequencial, sem qualquer paralelismo."""
    for pokemon_id in ids:
        get_and_save(pokemon_id)


def run_threading(ids, workers):
    """Executa o download usando threads manuais em lotes de tamanho 'workers'."""
    threads = []
    for pokemon_id in ids:
        # Cria e inicia uma thread para cada Pokémon
        t = threading.Thread(target=get_and_save, args=(pokemon_id,))
        threads.append(t)
        t.start()

        # Aguarda o lote terminar antes de iniciar o próximo
        if len(threads) >= workers:
            for th in threads:
                th.join()
            threads = []

    # Aguarda threads restantes que não completaram um lote inteiro
    for th in threads:
        th.join()


def run_multiprocessing(ids, workers):
    """Executa o download usando múltiplos processos com Pool.map()."""
    # Pool cria 'workers' processos independentes e distribui os IDs entre eles
    with Pool(processes=workers) as pool:
        pool.map(get_and_save, ids)


def run_futures(ids, workers):
    """Executa o download usando ThreadPoolExecutor do concurrent.futures."""
    # ThreadPoolExecutor gerencia o pool automaticamente
    # list() força a espera de todas as tarefas antes de continuar
    with ThreadPoolExecutor(max_workers=workers) as executor:
        list(executor.map(get_and_save, ids))


def measure(fn, runs=RUNS):
    """Executa uma função 'runs' vezes e retorna a média dos tempos de execução."""
    times = []
    for _ in range(runs):
        clear_images()  # Garante estado limpo antes de cada execução
        start = time.perf_counter()  # Usa perf_counter para maior precisão
        fn()
        times.append(time.perf_counter() - start)
    return round(sum(times) / len(times), 2)


def main():
    ensure_dirs()
    results = []

    for total in TOTALS:
        ids = list(range(1, total + 1))  # Lista de IDs dos Pokémons a baixar
        print(f"\n=== {total} pokémons ===")

        # Mede o tempo médio da abordagem sequencial
        avg = measure(lambda: sequential(ids))
        results.append({"abordagem": "Sequential", "workers": "-", "total": total, "media_s": avg})
        print(f"  Sequential: {avg}s")

        # Mede o tempo médio da abordagem com threading para cada número de workers
        for w in WORKERS:
            avg = measure(lambda w=w: run_threading(ids, w))
            results.append({"abordagem": "Threading", "workers": w, "total": total, "media_s": avg})
            print(f"  Threading-{w}: {avg}s")

        # Mede o tempo médio da abordagem com multiprocessing para cada número de processos
        for w in WORKERS:
            avg = measure(lambda w=w: run_multiprocessing(ids, w))
            results.append({"abordagem": "Multiprocessing", "workers": w, "total": total, "media_s": avg})
            print(f"  Multiprocessing-{w}: {avg}s")

        # Mede o tempo médio da abordagem com concurrent.futures para cada número de workers
        for w in WORKERS:
            avg = measure(lambda w=w: run_futures(ids, w))
            results.append({"abordagem": "concurrent.futures", "workers": w, "total": total, "media_s": avg})
            print(f"  Futures-{w}: {avg}s")

    # Salva todos os resultados em um arquivo CSV
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["abordagem", "workers", "total", "media_s"])
        writer.writeheader()
        writer.writerows(results)

    # Exibe a tabela de resultados finais no terminal
    print("\n\n=== RESULTADO FINAL ===")
    print(f"{'Abordagem':<22} {'Workers':<10} {'Total':<8} {'Média (s)'}")
    print("-" * 55)
    for r in results:
        print(f"{r['abordagem']:<22} {str(r['workers']):<10} {r['total']:<8} {r['media_s']}")
    print(f"\nSalvo em {RESULTS_FILE}")


if __name__ == "__main__":
    main()