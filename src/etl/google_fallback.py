import pandas as pd
import requests
import time
import os

def fetch_google_metadata():
    # 1. Configurações Iniciais
    input_path = 'data/processed/enriched_books.csv'
    # Pega a chave que você colocou no docker-compose
    api_key = os.getenv('GOOGLE_BOOKS_API_KEY')
    
    if not api_key:
        print("Erro: GOOGLE_BOOKS_API_KEY não encontrada no ambiente.")
        return

    df = pd.read_csv(input_path)
    # Filtra apenas o que precisa de correção
    mask = (df['My Rating'] >= 4) & (df['Genres_Enriched'].isna() | (df['Genres_Enriched'] == ""))
    livros_para_corrigir = df[mask].copy()

    print(f"Recuperando dados para {len(livros_para_corrigir)} livros com API Key...")

    for index, row in livros_para_corrigir.iterrows():
        # Limpa o título para a busca ser mais certeira
        title = str(row['Title']).split('(')[0].strip()
        author = str(row['Author'])
        
        # DEFINIMOS A QUERY AQUI
        query = f'intitle:"{title}"+inauthor:"{author}"'
        
        # AGORA MONTAMOS A URL (com a query e a key definidas)
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={api_key}&maxResults=1"

        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    info = data["items"][0]["volumeInfo"]
                    categories = "|".join(info.get("categories", []))
                    description = info.get("description", "")
                    
                    df.at[index, 'Genres_Enriched'] = categories
                    df.at[index, 'Description'] = description
                    print(f"[OK] {title} -> {categories}")
                else:
                    print(f"[?] {title} não encontrado.")
            
            elif response.status_code == 429:
                print("\n[!] Mesmo com Key, o limite foi atingido. Pausando 30s...")
                time.sleep(30)

        except Exception as e:
            print(f"[ERRO] {title}: {e}")
        
        # Com API Key, 0.5s costuma ser suficiente para não ser bloqueada
        time.sleep(0.5)

    # Consolida as tags para o recomendador
    df['All_Tags'] = df['Bookshelves'].fillna('') + "|" + df['Genres_Enriched'].fillna('')
    df.to_csv(input_path, index=False)
    print("\nEnriquecimento finalizado com sucesso!")

if __name__ == "__main__":
    fetch_google_metadata()