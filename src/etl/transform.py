import pandas as pd
import os

def run_transformation():
    # Caminhos dos arquivos
    input_path = 'data/raw/goodreads_library_export.csv'
    output_path = 'data/processed/cleaned_books.csv'

    if not os.path.exists(input_path):
        print(f"Erro: Arquivo {input_path} não encontrado.")
        return

    # 1. Extração: Lendo o CSV
    df = pd.read_csv(input_path)
    print(f"Dados carregados: {len(df)} linhas.")

    # 2. Transformação: Limpeza de Notas
    # Removemos livros sem nota (geralmente os 'to-read' que ainda não foram avaliados)
    df_cleaned = df[df['My Rating'] > 0].copy()

    # 3. Transformação: Normalização de ISBN
    # Seu export tem o formato ="valor". Vamos limpar para deixar apenas os números.
    df_cleaned['ISBN'] = df_cleaned['ISBN'].str.extract(r'(\d+)')
    df_cleaned['ISBN13'] = df_cleaned['ISBN13'].str.extract(r'(\d+)')

    # 4. Transformação: Filtragem de DNF (Opcional)
    # Você tem alguns livros como 'The Awakening' marcados como did-not-finish[cite: 27].
    # Vamos manter, mas criar uma flag para o modelo saber que você não terminou.
    df_cleaned['is_dnf'] = df_cleaned['Exclusive Shelf'] == 'did-not-finish'

    # 5. Carga: Salvando os dados limpos
    os.makedirs('data/processed', exist_ok=True)
    df_cleaned.to_csv(output_path, index=False)
    print(f"Transformação concluída! {len(df_cleaned)} livros salvos em {output_path}")

if __name__ == "__main__":
    run_transformation()