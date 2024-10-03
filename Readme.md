Aqui está o arquivo `README.md` formatado:

# Guia de Execução do Projeto

## Passos para Executar o Projeto

1. **Inicie o Frontend**

   Abra um terminal, navegue até o diretório do frontend e execute os comandos necessários para iniciá-lo.
   No terminal, execute o seguinte comando para ativar o frontend:

   ```bash
   python3 -m http.server 8000
   ```

2. **Configure o Backend**

   Em outra aba do terminal, exporte a variável de ambiente `FLASK_APP`:

   ```bash
   export FLASK_APP=app.py
   ```

3. **Inicie o Backend**

   Ainda no terminal, execute o comando abaixo para iniciar o backend:

   ```bash
   flask run
   ```

4. **Acesse o Frontend**

   No navegador, acesse o seguinte endereço para visualizar o frontend:

   ```bash
   http://127.0.0.1:8000
   ```