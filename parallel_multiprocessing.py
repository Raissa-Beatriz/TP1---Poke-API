import requests
import os
import time
from multiprocessing import Pool

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


def run_multiprocessing(total, num_processes):
    """Executa o download usando múltiplos processos com Pool.map()."""
    times = []

    for run in range(10):
        # Remove as imagens da execução anterior
        for f in os.listdir("images"):
            os.remove(f"images/{f}")

        start = time.time()

        # Cria um pool de processos e distribui os IDs entre eles
        # Pool.map() divide automaticamente a lista de IDs entre os processos
        with Pool(processes=num_processes) as pool:
            pool.map(get_and_save, range(1, total + 1))

        elapsed = time.time() - start
        times.append(elapsed)
        print(f"[Multiprocessing-{total}-{num_processes}p] Execução {run+1}/10: {elapsed:.2f}s")

    # Calcula e exibe a média dos tempos
    avg = sum(times) / len(times)
    print(f"[Multiprocessing-{total}-{num_processes}p] MÉDIA: {avg:.2f}s\n")
    return avg


if __name__ == "__main__":
    # Executa o benchmark com multiprocessing para 100, 500 e 1000 Pokémons
    # e para 2, 4 e 8 processos
    for total in [100, 500, 1000]:
        for procs in [2, 4, 8]:
            run_multiprocessing(total, procs)