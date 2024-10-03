from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import yfinance as yf
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, Dataset
from copy import deepcopy as dc
from sklearn.metrics import mean_squared_error

app = Flask(__name__)

class TimeSeriesDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y

    def __len__(self):
        return len(self.X)

    def __getitem__(self, i):
        return self.X[i], self.y[i]

# Função para pegar os dados do Yahoo Finance
def get_stock_data(ticker):
    stock_data = yf.download(ticker, start="2017-01-01")
    return stock_data[['Close']].reset_index()

# Prepara os dados para o LSTM
def prepare_dataframe_for_lstm(df, n_steps):
    df = dc(df)
    df.set_index('Date', inplace=True)
    for i in range(1, n_steps + 1):
        df[f'Close(t-{i})'] = df['Close'].shift(i)
    df.dropna(inplace=True)
    return df

# Função para carregar os dados de uma ação e rodar o modelo
def run_model_for_ticker(ticker):
    # Pegando dados da ação
    data = get_stock_data(ticker)
    data['Date'] = pd.to_datetime(data['Date'])
    lookback = 7
    shifted_df = prepare_dataframe_for_lstm(data, lookback)

    # Convertendo os dados para numpy
    shifted_df_as_np = shifted_df.to_numpy()
    scaler = MinMaxScaler(feature_range=(-1, 1))
    shifted_df_as_np = scaler.fit_transform(shifted_df_as_np)
    X = shifted_df_as_np[:, 1:]
    y = shifted_df_as_np[:, 0]
    X = dc(np.flip(X, axis=1))

    # Separando dados de treino e teste
    split_index = int(len(X) * 0.95)
    X_train = X[:split_index]
    X_test = X[split_index:]
    y_train = y[:split_index]
    y_test = y[split_index:]

    # Formatando para o LSTM
    X_train = X_train.reshape((-1, lookback, 1))
    X_test = X_test.reshape((-1, lookback, 1))
    y_train = y_train.reshape((-1, 1))
    y_test = y_test.reshape((-1, 1))

    X_train = torch.tensor(X_train).float()
    y_train = torch.tensor(y_train).float()
    X_test = torch.tensor(X_test).float()
    y_test = torch.tensor(y_test).float()

    # Definindo o modelo LSTM
    class LSTM(nn.Module):
        def __init__(self, input_size, hidden_size, num_stacked_layers):
            super().__init__()
            self.hidden_size = hidden_size
            self.num_stacked_layers = num_stacked_layers
            self.lstm = nn.LSTM(input_size, hidden_size, num_stacked_layers, batch_first=True)
            self.fc = nn.Linear(hidden_size, 1)

        def forward(self, x):
            batch_size = x.size(0)
            h0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(device)
            c0 = torch.zeros(self.num_stacked_layers, batch_size, self.hidden_size).to(device)
            out, _ = self.lstm(x, (h0, c0))
            out = self.fc(out[:, -1, :])
            return out

    # Configurações do modelo
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    model = LSTM(1, 4, 1)
    model.to(device)
    loss_function = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # Definindo datasets e loaders
    train_dataset = TimeSeriesDataset(X_train, y_train)
    test_dataset = TimeSeriesDataset(X_test, y_test)
    batch_size = 16
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Treinando o modelo
    for epoch in range(10):
        model.train()
        for batch in train_loader:
            x_batch, y_batch = batch[0].to(device), batch[1].to(device)
            output = model(x_batch)
            loss = loss_function(output, y_batch)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    # Prevendo para o próximo ano
    with torch.no_grad():
        test_predictions = model(X_test.to(device)).detach().cpu().numpy().flatten()

    # Transformando as previsões de volta para o preço original
    dummies = np.zeros((X_test.shape[0], lookback + 1))
    dummies[:, 0] = test_predictions
    dummies = scaler.inverse_transform(dummies)
    test_predictions = dc(dummies[:, 0])

    # Obter o preço atual
    current_price = data['Close'].iloc[-1]

    # Calcular o preço alvo (previsão para o próximo ano)
    target_price = test_predictions[-1]

    # Definir a recomendação
    if target_price > current_price * 1.10:
        recommendation = "Comprar"
    elif target_price < current_price * 0.90:
        recommendation = "Vender"
    else:
        recommendation = "Manter"

    rmse = mean_squared_error(y_test.flatten(), test_predictions, squared=False)

    # Retornando os resultados
    return {
        "current_price": current_price,
        "target_price": target_price,
        "recommendation": recommendation,
        "rmse": rmse
    }

# Rota principal para exibir o formulário e resultados
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ticker = request.form["ticker"]
        results = run_model_for_ticker(ticker)
        return render_template("index.html", results=results)
    return render_template("index.html", results=None)

if __name__ == "__main__":
    app.run(debug=True)
