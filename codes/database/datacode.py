import requests
import pandas as pd
import schedule
import time
import os
from datetime import datetime, timedelta

# Nome do arquivo CSV com caminho relativo ao diretório atual
csv_name = './codes/database/finance_news.csv'  # Apenas o nome do arquivo

# Função para verificar se o arquivo CSV já existe
def check_csv_exists(csv_name):
    return os.path.exists(csv_name)

# Função para criar um arquivo CSV vazio com cabeçalhos, se ele ainda não existir
def init_csv(csv_name):
    if not check_csv_exists(csv_name):
        df = pd.DataFrame(columns=['title', 'link', 'publisher', 'provider', 'datetime'])
        df.to_csv(csv_name, index=False)

def fetch_newsapi(query='finance', language='pt'):
    try:
        api_key = 'e485851e82b94d78a79bc0535d7a9226'
        today = datetime.now().strftime('%Y-%m-%d')
        ten_days_ago = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        url = f'https://newsapi.org/v2/everything?q={query}&language={language}&sortBy=publishedAt&pageSize=20&from={ten_days_ago}&to={today}&apiKey={api_key}'
        
        print(f"Consultando NewsAPI com a URL: {url}")  # Debug

        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            print(f"Erro ao buscar da NewsAPI: {data}")
            return []

        articles = data.get('articles', [])
        print(f"Artigos retornados da NewsAPI: {len(articles)}")  # Debug
        return articles
    except Exception as e:
        print(f"Erro na função fetch_newsapi: {e}")
        return []

def fetch_gnews(query='finance', language='pt', from_date=None, to_date=None):
    try:
        api_key = 'f5765bad15b4cc6b79efedf898649d52'
        
        url = f'https://gnews.io/api/v4/search?q={query}&lang={language}&from={from_date}&to={to_date}&max=100&apikey={api_key}'

        print(f"Consultando GNews com a URL: {url}")  # Debug

        response = requests.get(url)
        data = response.json()

        if response.status_code != 200:
            print(f"Erro ao buscar da GNews: {data}")
            return []

        articles = data.get('articles', [])
        print(f"Artigos retornados da GNews: {len(articles)}")  # Debug
        return articles
    except Exception as e:
        print(f"Erro na função fetch_gnews: {e}")
        return []

# Função para remover notícias que contenham "[removed]"
def filter_removed_articles(df):
    if not df.empty:
        # Remover linhas onde qualquer campo contém "[removed]"
        df = df[~df.apply(lambda x: x.astype(str).str.contains(r'\[removed\]', case=False).any(), axis=1)]
    return df

# Função para atualizar o arquivo CSV com notícias adicionais do GNews
def update_csv_gnews(csv_name, query):
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
        new_df = filter_removed_articles(new_df)  # Filtrar as notícias que têm "[removed]"

        if not new_df.empty:
            print("Novos dados do GNews a serem salvos:", new_df.head())
        else:
            print("Nenhuma notícia nova do GNews para salvar.")

        # Atualiza o CSV
        if check_csv_exists(csv_name):
            existing_df = pd.read_csv(csv_name)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
        else:
            combined_df = new_df

        combined_df.to_csv(csv_name, index=False)
        print("Notícias do GNews atualizadas com sucesso.")
    
    except Exception as e:
        print(f"Erro ao atualizar CSV com GNews: {e}")

# Função para atualizar o arquivo CSV com notícias adicionais do NewsAPI
def update_csv_newsapi(csv_name, query):
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
        new_df = filter_removed_articles(new_df)  # Filtrar as notícias que têm "[removed]"

        if not new_df.empty:
            print("Novos dados do NewsAPI a serem salvos:", new_df.head())
        else:
            print("Nenhuma notícia nova do NewsAPI para salvar.")

        # Atualiza o CSV
        if check_csv_exists(csv_name):
            existing_df = pd.read_csv(csv_name)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
        else:
            combined_df = new_df

        combined_df.to_csv(csv_name, index=False)
        print("Notícias do NewsAPI atualizadas com sucesso.")
    
    except Exception as e:
        print(f"Erro ao atualizar CSV com NewsAPI: {e}")

# Inicializa o arquivo CSV se ainda não existir
init_csv(csv_name)

# Função para agendar a atualização das notícias
def job():
    update_csv_newsapi(csv_name, query='finance')
    update_csv_gnews(csv_name, query='finance')

# Agendamento da tarefa diária
schedule.every().hour.do(job)

# Executa a função uma vez ao iniciar para garantir que o CSV seja atualizado imediatamente
job()

# Loop para manter o script rodando e verificando o agendamento
while True:
    schedule.run_pending()
    time.sleep(1)
