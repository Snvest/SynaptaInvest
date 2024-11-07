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
        if response.status_code in [401, 403]:
            print(f"Requer login: {url}")
            return False
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
        df = df[df['link'].apply(lambda x: is_trusted(x) and is_accessible_without_login(x))]
    return df

# Função para remover notícias que contenham "[removed]" ou que não são confiáveis/acessíveis
def filter_removed_articles(df):
    if not df.empty:
        df = df.astype(str)
        df = df[~df.apply(lambda x: x.str.contains(r'\[removed\]|removed.com', case=False, na=False).any(), axis=1)]
        df = filter_trusted_and_accessible_articles(df)
    return df

# Função para verificar se o arquivo Excel existe
def check_excel_exists(excel_name):
    return os.path.exists(excel_name)

# Função para buscar notícias do NewsAPI (filtrar para o dia atual)
def fetch_newsapi(query):
    today = datetime.now().strftime('%Y-%m-%d')  # Data de hoje
    url = f"https://newsapi.org/v2/everything?q={query}&apiKey=e485851e82b94d78a79bc0535d7a9226"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('articles', [])
        else:
            print(f"Erro na requisição ao NewsAPI: {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro ao buscar dados do NewsAPI: {e}")
        return []

# Função para buscar notícias do GNews (filtrar para o dia atual)
def fetch_gnews(query):
    today = datetime.now().strftime('%Y-%m-%d')  # Data de hoje
    url = f"https://gnews.io/api/v4/search?q={query}&lang=pt&country=br&max=50&apikey=e485851e82b94d78a79bc0535d7a9226"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('articles', [])
        else:
            print(f"Erro na requisição ao GNews: {response.status_code}")
            return []
    except Exception as e:
        print(f"Erro ao buscar dados do GNews: {e}")
        return []

# Função para atualizar Excel com NewsAPI
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
        new_df = filter_removed_articles(new_df)

        if not new_df.empty:
            print("Novos dados do NewsAPI a serem salvos:", new_df.head())
        else:
            print("Nenhuma notícia nova do NewsAPI para salvar.")

        if check_excel_exists(excel_name):
            existing_df = pd.read_excel(excel_name)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
        else:
            combined_df = new_df

        combined_df.to_excel(excel_name, index=False)
        print("Notícias do NewsAPI atualizadas com sucesso.")
    
    except Exception as e:
        print(f"Erro ao atualizar Excel com NewsAPI: {e}")

# Função para atualizar Excel com GNews
def update_excel_gnews(excel_name, query):
    try:
        additional_news = fetch_gnews(query)

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
        new_df = filter_removed_articles(new_df)

        if not new_df.empty:
            print("Novos dados do GNews a serem salvos:", new_df.head())
        else:
            print("Nenhuma notícia nova do GNews para salvar.")

        if check_excel_exists(excel_name):
            existing_df = pd.read_excel(excel_name)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
        else:
            combined_df = new_df

        combined_df.to_excel(excel_name, index=False)
        print("Notícias do GNews atualizadas com sucesso.")
    
    except Exception as e:
        print(f"Erro ao atualizar Excel com GNews: {e}")

# Função para rodar as atualizações a cada hora
def job():
    excel_name = './database/finance_news.xlsx'
    query = 'fin'
    update_excel_newsapi(excel_name, query)
    update_excel_gnews(excel_name, query)

# Agenda a função para rodar a cada 1 hora
schedule.every(1).hours.do(job)

# Mantém o script rodando
while True:
    schedule.run_pending()
    time.sleep(1)

