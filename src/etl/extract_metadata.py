import pandas as pd
import requests
import time
import os

def fetch_metadata():
    input_path = 'data/processed/cleaned_books.csv'
    output_path = 'data/processed/enriched_books.csv'
    
    if not os.path.exists(input_path):
        print("Erro: cleaned_books.csv não encontrado. Executa o transform.py primeiro.")
        return

    df = pd.read_csv(input_path)
    
    # Filtramos os teus favoritos (notas 4 e 5)
    # Exemplos: Witch Hat Atelier e Sakamoto Days
    favoritos = df[df['My Rating'] >= 4].copy()
    
    # A URL agora aponta para o nome do serviço no Docker Compose
    # De acordo com o README, os endpoints começam com /api
    base_url = os.getenv('SCRAPER_API_URL', 'http://scraper-api:3000/api')
    
    metadata_list = []
    print(f"Iniciando enriquecimento de {len(favoritos)} livros...")

    for index, row in favoritos.iterrows():
        book_id = str(row['Book Id'])
        print(f"-> A processar: {row['Title']} (ID: {book_id})")
        
        try:
            # Novo endpoint conforme o README: /api/book/details/:id
            response = requests.get(f"{base_url}/book/details/{book_id}", timeout=15)
            
            if response.status_code == 200:
                json_data = response.json()
                
                # O README diz que o formato é: {"success": true, "data": {...}}
                if json_data.get('success') and json_data.get('data'):
                    book_data = json_data['data']
                    
                    # Extraímos os géneros (genres) e a descrição
                    # Nota: os nomes das chaves dependem do que a API retorna no campo 'data'
                    description = book_data.get('description', '')
                    genres = book_data.get('genres', []) # Lista de géneros
                    
                    metadata_list.append({
                        'Book Id': int(book_id),
                        'Description': description,
                        'Genres': "|".join(genres) if isinstance(genres, list) else str(genres)
                    })
                else:
                    print(f"API retornou erro para o livro {book_id}")
            else:
                print(f"Erro na API: Status {response.status_code}")
                
        except Exception as e:
            print(f"Falha na requisição: {e}")
        
        # Delay para não sobrecarregar a API local e evitar erros de timeout
        time.sleep(0.5)

    # Converter resultados para DataFrame e unir com os teus favoritos
    enriched_results_df = pd.DataFrame(metadata_list)
    
    if not enriched_results_df.empty:
        # Fazemos o merge para garantir que não perdemos as colunas originais do CSV
        final_df = favoritos.merge(enriched_results_df, on='Book Id', how='left')
        
        os.makedirs('data/processed', exist_ok=True)
        final_df.to_csv(output_path, index=False)
        print(f"\nSucesso! {len(enriched_results_df)} livros enriquecidos.")
        print(f"Ficheiro guardado em: {output_path}")
    else:
        print("\nNenhum dado foi recuperado da API.")

if __name__ == "__main__":
    fetch_metadata()