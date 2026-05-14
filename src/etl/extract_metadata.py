import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import os

def generate_external_recommendations():
    # Caminhos dos arquivos
    my_books_path = 'data/processed/enriched_books.csv'
    kaggle_books_path = 'data/raw/book_data.csv' # Verifique o nome exato do CSV que você baixou

    if not os.path.exists(my_books_path) or not os.path.exists(kaggle_books_path):
        print("Erro: Verifique se os arquivos CSV estão nas pastas corretas.")
        return

    # 1. Carregar seus dados e filtrar favoritos (Notas 4 e 5)
    meus_livros = pd.read_csv(my_books_path)
    meus_favs = meus_livros[meus_livros['My Rating'] >= 4].copy()
    
    # Criar 'sopa de tags' para seus livros
    meus_favs['metadata'] = (meus_favs['Author'].fillna('') + ' ' + 
                            meus_favs['All_Tags'].fillna('')).str.lower()

    # 2. Carregar dataset do Kaggle (usando uma amostra para performance)
    # 100.000 linhas costumam ser seguras para a maioria dos PCs pessoais
    externo = pd.read_csv(kaggle_books_path, nrows=100000)
    
    # Ajuste os nomes das colunas conforme o seu dataset do Kaggle (ex: 'book_title', 'genres', 'author')
    # Vou usar nomes genéricos, verifique as colunas do seu arquivo!
    externo['metadata'] = (externo['author'].fillna('') + ' ' + 
                          externo['genres'].fillna('')).str.lower()

    # 3. Unir bases para o cálculo
    # Marcamos o que é seu e o que é externo
    meus_favs['source'] = 'meu'
    externo['source'] = 'kaggle'
    
    df_total = pd.concat([
        meus_favs[['Title', 'metadata', 'source']], 
        externo[['book_title', 'metadata', 'source']].rename(columns={'book_title': 'Title'})
    ], ignore_index=True)

    # 4. Vetorização TF-IDF
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(df_total['metadata'].fillna(''))

    # 5. Função de recomendação
    def recommend_new_stuff(book_title):
        try:
            # Encontra o índice do seu livro na base total
            idx = df_total[df_total['Title'] == book_title].index[0]
            
            # Calcula similaridade apenas para esse livro (linear_kernel é mais rápido)
            cosine_sim = linear_kernel(tfidf_matrix[idx], tfidf_matrix).flatten()
            
            # Pega os índices mais similares
            sim_indices = cosine_sim.argsort()[::-1]
            
            # Filtra para retornar APENAS livros que estão na base do Kaggle (que você não leu)
            recoms = []
            for i in sim_indices:
                if df_total.iloc[i]['source'] == 'kaggle':
                    recoms.append(df_total.iloc[i]['Title'])
                if len(recoms) >= 5: break
            
            return recoms
        except Exception as e:
            return f"Erro: {e}"

    # Teste com um favorito seu
    exemplo = meus_favs.iloc[0]['Title']
    print(f"\nSe você gostou de '{exemplo}', talvez goste de:")
    print(recommend_new_stuff(exemplo))

if __name__ == "__main__":
    generate_external_recommendations()