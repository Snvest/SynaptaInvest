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

# Função para buscar notícias de várias fontes usando NewsAPI
def fetch_newsapi(query='finance', language='pt'):
    api_key = 'e485851e82b94d78a79bc0535d7a9226'
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
    url = f'https://newsapi.org/v2/everything?q={query}&language={language}&sortBy=publishedAt&pageSize=20&from={yesterday}&to={today}&apiKey={api_key}'
    response = requests.get(url)
    data = response.json()
    print(data)  # Verifique a resposta da API
    articles = data.get('articles', [])
    return articles

# Função para buscar notícias usando GNews API
def fetch_gnews(query='finance', language='pt', from_date=None, to_date=None):
    api_key = 'f5765bad15b4cc6b79efedf898649d52'
    url = f'https://gnews.io/api/v4/search?q={query}&lang={language}&from={from_date}&to={to_date}&max=100&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    print(data)  # Verifique a resposta da API
    articles = data.get('articles', [])
    return articles

# Função para atualizar o arquivo CSV com notícias adicionais
def update_csv_gnews(csv_name, query):
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
    additional_news = fetch_gnews(query=query, from_date=yesterday, to_date=today)
    
    if not additional_news:
        print("Nenhuma notícia adicional encontrada.")
        return

    print(additional_news)  # Verifique o conteúdo das notícias

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
    print(new_df.head())  # Verifique o conteúdo do DataFrame

    if check_csv_exists(csv_name):
        existing_df = pd.read_csv(csv_name)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
    else:
        combined_df = new_df

    combined_df.to_csv(csv_name, index=False)
    print("Notícias adicionais atualizadas com sucesso.")

# Função para atualizar o arquivo CSV com notícias adicionais
def update_csv_newsapi(csv_name, query):
    additional_news = fetch_newsapi(query)
    if not additional_news:
        print("Nenhuma notícia adicional encontrada.")
        return

    print(additional_news)  # Verifique o conteúdo das notícias

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
    print(new_df.head())  # Verifique o conteúdo do DataFrame

    if check_csv_exists(csv_name):
        existing_df = pd.read_csv(csv_name)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True).drop_duplicates(subset=['title', 'datetime'], keep='last')
    else:
        combined_df = new_df

    combined_df.to_csv(csv_name, index=False)
    print("Notícias adicionais atualizadas com sucesso.")

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
