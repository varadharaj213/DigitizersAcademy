  // Chat Script - Updated for direct file access
const chatbotIcon = document.getElementById('chatbot-icon');
const chatbotWindow = document.getElementById('chatbot-window');
const chatInput = document.getElementById('chat-input');
const chatContent = document.getElementById('chat-content');
const sendBtn = document.querySelector('.send-btn');
const closeBtn = document.querySelector('.close-btn');
const notificationBadge = document.querySelector('.notification-badge');

// Define the server URL - change this if your Flask server runs on a different port
const serverUrl = "http://127.0.0.1:3000";

// Initial greeting
setTimeout(() => {
  addBotMessage("Hi there! 👋 I'm DigitizerBot, your personal assistant. How can I help you today?");
}, 500);

function toggleChatWindow() {
  if (chatbotWindow.style.display === 'none' || chatbotWindow.style.display === '') {
    chatbotWindow.style.display = 'flex';
    chatInput.focus();
    notificationBadge.style.display = 'none';
    
    // Scroll to bottom
    chatContent.scrollTop = chatContent.scrollHeight;
  } else {
    chatbotWindow.style.display = 'none';
  }
}

chatbotIcon.onclick = toggleChatWindow;
closeBtn.onclick = toggleChatWindow;

function getCurrentTime() {
  const now = new Date();
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
}

function addUserMessage(message) {
  const time = getCurrentTime();
  const messageElement = document.createElement('div');
  messageElement.classList.add('message', 'user-message');
  messageElement.innerHTML = `
    ${message}
    <div class="message-time">${time}</div>
  `;
  chatContent.appendChild(messageElement);
  chatContent.scrollTop = chatContent.scrollHeight;
}

function addBotMessage(message) {
  const time = getCurrentTime();
  const messageElement = document.createElement('div');
  messageElement.classList.add('message', 'bot-message');
  messageElement.innerHTML = `
    ${message}
    <div class="message-time">${time}</div>
  `;
  chatContent.appendChild(messageElement);
  chatContent.scrollTop = chatContent.scrollHeight;
}

function showTypingIndicator() {
  const typingElement = document.createElement('div');
  typingElement.classList.add('bot-typing');
  typingElement.innerHTML = `
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
    <div class="typing-dot"></div>
  `;
  typingElement.id = "typing-indicator";
  chatContent.appendChild(typingElement);
  chatContent.scrollTop = chatContent.scrollHeight;
}

function removeTypingIndicator() {
  const typingElement = document.getElementById("typing-indicator");
  if (typingElement) {
    typingElement.remove();
  }
}

function sendMessage() {
  const message = chatInput.value.trim();
  if (message) {
    addUserMessage(message);
    showTypingIndicator();
    
    // Send to server with explicit URL (works when opened from file:///)
    fetch(`${serverUrl}/chat`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ message })
    })
    .then(res => res.json())
    .then(data => {
      setTimeout(() => {
        removeTypingIndicator();
        addBotMessage(data.reply);
      }, 700); // Simulate typing delay
    })
    .catch(error => {
      removeTypingIndicator();
      addBotMessage("Sorry, I encountered an error. Please check if the Flask server is running at " + serverUrl);
      console.error("Error:", error);
    });
    
    chatInput.value = '';
  }
}

sendBtn.addEventListener('click', sendMessage);

chatInput.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') {
    sendMessage();
  }
});

// When user clicks outside the chat window, but not on the chat icon
document.addEventListener('click', function(e) {
  if (!chatbotWindow.contains(e.target) && 
      !chatbotIcon.contains(e.target) && 
      chatbotWindow.style.display === 'flex') {
    chatbotWindow.style.display = 'none';
  }
});

// Prevent clicks inside the chat window from closing it
chatbotWindow.addEventListener('click', function(e) {
  e.stopPropagation();
});

// Optional: Check if server is running when the page loads
function checkServerStatus() {
  fetch(`${serverUrl}/docs_info`)
    .then(response => response.json())
    .then(data => {
      console.log("Server connected! Loaded documents:", data.loaded_docs);
    })
    .catch(error => {
      console.error("Server not available. Please start Flask server at:", serverUrl);
    });
}

// Uncomment to enable server status check on page load
// checkServerStatus();