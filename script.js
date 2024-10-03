document.addEventListener('DOMContentLoaded', function() {
    console.log('Página carregada!');

    // Exemplo de interatividade para o botão "Integrar com a B3"
    const integrarButton = document.querySelector('.cta-button:first-child');
    integrarButton.addEventListener('click', function() {
        alert('Funcionalidade de integração com a B3 em desenvolvimento.');
    });

    // Exemplo de interatividade para o botão "Adicionar Ativo"
    const adicionarAtivoButton = document.querySelector('.cta-button:last-child');
    adicionarAtivoButton.addEventListener('click', function() {
        alert('Funcionalidade de adicionar ativo em desenvolvimento.');
    });
});
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página carregada!');
    fetchNews();
});

function fetchNews() {
    const apiKey = 'YOUR_API_KEY'; // Substitua com sua chave da API
    const apiUrl = `https://newsapi.org/v2/everything?q=ações&apiKey=${apiKey}`;
    
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const articles = data.articles;
            const newsContainer = document.getElementById('news-container');
            newsContainer.innerHTML = '';

            articles.forEach(article => {
                const newsItem = document.createElement('div');
                newsItem.className = 'news-item';
                
                const newsLink = document.createElement('a');
                newsLink.href = article.url;
                newsLink.target = '_blank';
                newsLink.textContent = article.title;
                
                newsItem.appendChild(newsLink);
                newsContainer.appendChild(newsItem);
            });
        })
        .catch(error => console.error('Erro ao buscar notícias:', error));