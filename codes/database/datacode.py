import requests
import pandas as pd
import schedule
import time
import os
from datetime import datetime, timedelta

# Lista de domínios confiáveis
trusted_domains = [
    'bbc.com', 'cnn.com', 'reuters.com', 'nytimes.com', 'forbes.com', 'valor.globo.com', 
    'economia.uol.com.br', 'exame.com', 'g1.globo.com', 'folha.uol.com.br'
]

# Função para verificar se uma URL é confiável com base no domínio
def is_trusted(url):
    for domain in trusted_domains:
        if domain in url:
            return True
    return False

# Função para verificar se a URL requer login
def is_accessible_without_login(url):
    try:
        response = requests.get(url, timeout=5)
        # Verifica se o código de status é 401 ou 403 (requere login)
        if response.status_code in [401, 403]:
            print(f"Requer login: {url}")
            return False
        # Verifica se há redirecionamentos para uma página de login
        if 'login' in response.url or 'signin' in response.url:
            print(f"Redireciona para login: {url}")
            return False
        return True
    except Exception as e:
        print(f"Erro ao verificar URL: {url} - {e}")
        return False

# Função para filtrar as notícias confiáveis e acessíveis
def filter_trusted_and_accessible_articles(df):
    if not df.empty:
        # Filtrar URLs confiáveis e acessíveis
        df = df[df['link'].apply(lambda x: is_trusted(x) and is_accessible_without_login(x))]
    return df

# Função para remover notícias que contenham "[removed]" ou que não são confiáveis/acessíveis
def filter_removed_articles(df):
    if not df.empty:
        # Garantir que todos os valores de texto sejam strings
        df = df.astype(str)
        # Remover linhas onde qualquer campo contém "[removed]" ou "removed.com"
        df = df[~df.apply(lambda x: x.str.contains(r'\[removed\]|removed.com', case=False, na=False).any(), axis=1)]
        # Filtrar as confiáveis e acessíveis
        df = filter_trusted_and_accessible_articles(df)
    return df

# Exemplo para salvar as notícias confiáveis e acessíveis em Excel
def update_excel_newsapi(excel_name, query):
    try:
        additional_news = fetch_newsapi(query)
        if not additional_news:
            print("Nenhuma notícia adicional encontrada no NewsAPI.")
            return

        new_data = []
        for item in additional_news:
            new_data.append({
                'title': item.get('title', 'N/A'),
                'link': item.get('url', 'N/A'),
                'publisher': item.get('source', {}).get('name', 'N/A'),
                'provider': 'NewsAPI',
                'datetime': item.get('publishedAt', 'N/A')
            })

        new_df = pd.DataFrame(new_data)
        new_df = filter_removed_articles(new_df)  # Filtrar notícias removidas, confiáveis e acessíveis

        if not new_df.empty:
            print("Novos dados do NewsAPI a serem salvos:", new_df.head())
        else:
            print("Nenhuma notícia nova do NewsAPI para salvar.")

        # Atualiza o Excel
        if check_excel_exists(excel_name):
            existing_df = pd.read_excel(excel_name)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
        else:
            combined_df = new_df

        combined_df.to_excel(excel_name, index=False)
        print("Notícias do NewsAPI atualizadas com sucesso.")
    
    except Exception as e:
        print(f"Erro ao atualizar Excel com NewsAPI: {e}")

# Exemplo para o GNews:
def update_excel_gnews(excel_name, query):
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        ten_days_ago = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        additional_news = fetch_gnews(query=query, from_date=ten_days_ago, to_date=today)

        if not additional_news:
            print("Nenhuma notícia adicional encontrada.")
            return

        new_data = []
        for item in additional_news:
            new_data.append({
                'title': item.get('title', 'N/A'),
                'link': item.get('url', 'N/A'),
                'publisher': item.get('source', {}).get('name', 'N/A'),
                'provider': 'GNews',
                'datetime': item.get('publishedAt', 'N/A')
            })

        new_df = pd.DataFrame(new_data)
        new_df = filter_removed_articles(new_df)  # Filtrar as notícias removidas, confiáveis e acessíveis

        if not new_df.empty:
            print("Novos dados do GNews a serem salvos:", new_df.head())
        else:
            print("Nenhuma notícia nova do GNews para salvar.")

        # Atualiza o Excel
        if check_excel_exists(excel_name):
            existing_df = pd.read_excel(excel_name)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
        else:
            combined_df = new_df

        combined_df.to_excel(excel_name, index=False)
        print("Notícias do GNews atualizadas com sucesso.")
    
    except Exception as e:
        print(f"Erro ao atualizar Excel com GNews: {e}")
