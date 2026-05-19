import requests
import os
import time
import threading

# Cria a pasta onde as imagens serão salvas, se ainda não existir
os.makedirs("images", exist_ok=True)


def get_and_save(pokemon_id):
    """Busca os dados do Pokémon pela API e salva a imagem principal em disco."""
    # Faz a requisição à PokéAPI usando o ID do Pokémon
    data = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}").json()

    # Obtém a URL da imagem frontal padrão
    img_url = data["sprites"]["front_default"]

    if img_url:
        # Baixa o conteúdo da imagem
        img = requests.get(img_url).content

        # Salva a imagem no disco com o nome baseado no ID do Pokémon
        with open(f"images/{pokemon_id}.png", "wb") as f:
            f.write(img)


def run_threading(total, num_workers):
    """Executa o download usando threads em lotes de tamanho 'num_workers'."""
    times = []

    for run in range(10):
        # Remove as imagens da execução anterior
        for f in os.listdir("images"):
            os.remove(f"images/{f}")

        start = time.time()
        threads = []

        for i in range(1, total + 1):
            # Cria uma thread para cada Pokémon
            t = threading.Thread(target=get_and_save, args=(i,))
            threads.append(t)
            t.start()

            # Quando o lote atingir o número de workers, aguarda todas terminarem
            if len(threads) >= num_workers:
                for t in threads:
                    t.join()
                threads = []  # Reinicia o lote

        # Aguarda eventuais threads restantes que não completaram o lote
        for t in threads:
            t.join()

        elapsed = time.time() - start
        times.append(elapsed)
        print(f"[Threading-{total}-{num_workers}t] Execução {run+1}/10: {elapsed:.2f}s")

    # Calcula e exibe a média dos tempos
    avg = sum(times) / len(times)
    print(f"[Threading-{total}-{num_workers}t] MÉDIA: {avg:.2f}s\n")
    return avg


if __name__ == "__main__":
    # Executa o benchmark com threading para 100, 500 e 1000 Pokémons
    # e para 2, 4 e 8 workers
    for total in [100, 500, 1000]:
        for workers in [2, 4, 8]:
            run_threading(total, workers)