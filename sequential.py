import requests
import os
import time

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


def run_sequential(total):
    """Executa o download sequencial de 'total' Pokémons, repetindo 10 vezes para calcular a média."""
    times = []

    for run in range(10):
        # Remove as imagens da execução anterior para garantir condições idênticas
        for f in os.listdir("images"):
            os.remove(f"images/{f}")

        start = time.time()

        # Baixa cada Pokémon um por vez, sem paralelismo
        for i in range(1, total + 1):
            get_and_save(i)

        elapsed = time.time() - start
        times.append(elapsed)
        print(f"[Sequential-{total}] Execução {run+1}/10: {elapsed:.2f}s")

    # Calcula e exibe a média dos tempos
    avg = sum(times) / len(times)
    print(f"[Sequential-{total}] MÉDIA: {avg:.2f}s\n")
    return avg


if __name__ == "__main__":
    # Executa o benchmark sequencial para 100, 500 e 1000 Pokémons
    for total in [100, 500, 1000]:
        run_sequential(total)