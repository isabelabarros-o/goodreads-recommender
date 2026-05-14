import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import os
import re

def clean_text(text):
    if pd.isna(text): return ""
    text = str(text).lower()
    # Mantemos 'coming' mas removemos apenas o lixo sistêmico
    blacklist = ['api', '404', 'erro', 'not', 'available', 'read', 'repertorio', 'currently', 'books', 'ebook', 'volume', 'vol']
    for word in blacklist:
        text = text.replace(word, '')
    text = re.sub(r'[^a-z\s]', ' ', text)
    return " ".join(text.split())

def generate_external_recommendations():
    # Caminho do arquivo que você acabou de enriquecer com a Google Key
    my_books_path = 'data/processed/enriched_books.csv'
    kaggle_books_path = 'data/raw/Goodreads_books_with_genres.csv'

    meus_livros = pd.read_csv(my_books_path)
    meus_favs = meus_livros[meus_livros['My Rating'] >= 4].copy()
    
    # Agora usamos a coluna Genres_Enriched que o Google preencheu!
    meus_favs['metadata'] = (
        meus_favs['Author'].apply(clean_text) + ' ' + 
        meus_favs['Genres_Enriched'].apply(clean_text) + ' ' +
        meus_favs['Bookshelves'].apply(clean_text)
    )

    print("Carregando base do Kaggle (500.000 livros para máxima precisão)...")
    externo = pd.read_csv(kaggle_books_path, nrows=500000)
    externo['metadata'] = (externo['Author'].apply(clean_text) + ' ' + 
                          externo['genres'].apply(clean_text))

    df_total = pd.concat([
        meus_favs[['Title', 'metadata']].assign(source='meu'), 
        externo[['Title', 'metadata']].assign(source='kaggle')
    ], ignore_index=True)

    # Aumentamos para ngrams de até 3 palavras para pegar "Coming of Age" ou "Graphic Novel Manga"
    tfidf = TfidfVectorizer(stop_words='english', ngram_range=(1, 3), min_df=2)
    tfidf_matrix = tfidf.fit_transform(df_total['metadata'].fillna(''))

    def recommend_flex(partial_title):
        try:
            mask = df_total['Title'].str.contains(partial_title, case=False, na=False)
            matches = df_total[mask & (df_total['source'] == 'meu')]
            if matches.empty: return [f"Nenhum favorito encontrado com '{partial_title}'."]
            
            idx = matches.index[0]
            print(f"\n[INFO] Perfil de '{df_total.iloc[idx]['Title']}': {df_total.iloc[idx]['metadata'][:100]}...")
            
            sim_indices = linear_kernel(tfidf_matrix[idx], tfidf_matrix).flatten().argsort()[::-1]
            
            recoms = []
            for i in sim_indices:
                row = df_total.iloc[i]
                if row['source'] == 'kaggle' and row['Title'] not in meus_livros['Title'].values:
                    recoms.append(f"{row['Title']} [{row['metadata'][:60]}]")
                if len(recoms) >= 5: break
            return recoms
        except Exception as e: return [f"Erro: {e}"]

    print("\n" + "="*60)
    print("RECOMENDAÇÕES FINAIS - PROJETO REPERTÓRIO")
    print("="*60)
    
    # Testando seus pilares de leitura
    testes = ['Sakamoto', 'Witch Hat', 'Poet Empress', 'Santo']
    for t in testes:
        print(f"\nSugeridos para quem leu '{t}':")
        for r in recommend_flex(t):
            print(f"  ⭐ {r}")

if __name__ == "__main__":
    generate_external_recommendations()