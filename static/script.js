document.addEventListener('DOMContentLoaded', () => {


    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-button');
    const typingIndicator = document.getElementById('typing-indicator');
    
    let conversationHistory = [];
    

    addMessage('Olá! Sou o **Guia Rocha**, seu assistente virtual. Como posso ajudar com os processos da empresa hoje?', 'bot');



    function typeText(targetElement, message) {
        let i = 0;
        targetElement.textContent = ''; 
        const interval = setInterval(() => {
            if (i < message.length) {
                targetElement.textContent += message.charAt(i);
                i++;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            } else {
                clearInterval(interval);
                const pElement = targetElement.closest('.message').querySelector('p');
                if (window.marked) {
                    pElement.innerHTML = marked.parse(message);
                }
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 30); 
    }


    function addMessage(message, sender, animate = false) {
        if (sender === 'user') {
            conversationHistory.push({ role: 'user', parts: [message] });
        } else if (sender === 'bot') {
        }
        
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        const pElement = document.createElement('p');
        
        messageElement.appendChild(pElement);
        chatMessages.appendChild(messageElement);
        
        if (sender === 'bot' && animate) {
            pElement.innerHTML = ''; 
            typeText(pElement, message);
            conversationHistory.push({ role: 'model', parts: [message] });
        } else if (sender === 'bot' && window.marked) {
            pElement.innerHTML = marked.parse(message);
            
        } else {
            pElement.textContent = message;
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessageToBot() {
        const question = userInput.value.trim();
        if (question === '') return;

        addMessage(question, 'user');
        userInput.value = '';
        typingIndicator.style.display = 'block';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: question,
                    history: conversationHistory.slice(0, -1) 
                })
            });

            if (!response.ok) { 
                const errorText = await response.text();
                throw new Error(`Erro do servidor (${response.status}): ${errorText.substring(0, 100)}...`);
            }

            const data = await response.json();
            addMessage(data.answer, 'bot', true); 

        } catch (error) {
            console.error('Erro ao buscar resposta:', error);
            addMessage(`Desculpe, não consegui me conectar ao meu cérebro. Detalhe: ${error.message}`, 'bot');
            conversationHistory.pop();
        } finally {
            typingIndicator.style.display = 'none';
        }
    }

    sendBtn.addEventListener('click', sendMessageToBot);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') { sendMessageToBot(); }
    });


    const searchInput = document.getElementById('article-search');
    const articleLinks = document.querySelectorAll('#topics-content .article-link');

    if (searchInput) {
        searchInput.addEventListener('keyup', (event) => {
            const searchTerm = event.target.value.toLowerCase();

            articleLinks.forEach(link => {
                const title = link.querySelector('h4').textContent.toLowerCase();
                if (title.includes(searchTerm)) {
                    link.style.display = 'block';
                } else {
                    link.style.display = 'none';
                }
            });
        });
    }

});