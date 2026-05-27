// ==========================================================================
// Antigravity AI Agent Dashboard - Lógica Frontend Premium (JS ES6)
// ==========================================================================

// Global state variables
let isChatRunning = false;
let activeApiKey = "";

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    initStarsBackground();
    initApiKeyField();
    setupChatHandler();
    checkInitialApiKey();
});

// 1. Generate Starry Sky Backdrop Dynamically
function initStarsBackground() {
    const container = document.querySelector(".stars-container");
    if (!container) return;
    
    const starCount = 80;
    for (let i = 0; i < starCount; i++) {
        const star = document.createElement("div");
        star.classList.add("star");
        
        // Random positioning and sizes
        const size = Math.random() * 2 + 1;
        star.style.width = `${size}px`;
        star.style.height = `${size}px`;
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        
        // Random opacity and blink delays
        star.style.opacity = Math.random();
        star.style.animation = `starBlink ${Math.random() * 4 + 3}s infinite ease-in-out`;
        
        container.appendChild(star);
    }
}

// Key blink animation injected via CSS
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes starBlink {
    0%, 100% { opacity: 0.2; }
    50% { opacity: 0.8; }
}
.star {
    position: absolute;
    background-color: #fff;
    border-radius: 50%;
    pointer-events: none;
}
`;
document.head.appendChild(styleSheet);

// 2. Handle Custom API Key entered in UI
function initApiKeyField() {
    const keyInput = document.getElementById("apiKeyInput");
    const storedKey = sessionStorage.getItem("GEMINI_API_KEY");
    
    if (storedKey) {
        keyInput.value = storedKey;
        activeApiKey = storedKey;
        updateKeyStatusIndicator(true, "Llave API: Guardada");
    } else {
        updateKeyStatusIndicator(false, "Llave API: Servidor");
    }

    keyInput.addEventListener("input", (e) => {
        const val = e.target.value.trim();
        if (val) {
            sessionStorage.setItem("GEMINI_API_KEY", val);
            activeApiKey = val;
            updateKeyStatusIndicator(true, "Llave API: Guardada");
        } else {
            sessionStorage.removeItem("GEMINI_API_KEY");
            activeApiKey = "";
            updateKeyStatusIndicator(false, "Llave API: Servidor");
        }
    });
}

function updateKeyStatusIndicator(hasKey, labelText) {
    const indicator = document.getElementById("keyStatus");
    const dot = indicator.querySelector(".pulse-dot");
    const label = indicator.querySelector(".status-label");
    
    label.textContent = labelText;
    if (hasKey) {
        dot.style.backgroundColor = "var(--green-active)";
        dot.style.boxShadow = "0 0 10px var(--green-active)";
    } else {
        dot.style.backgroundColor = "var(--cyan)";
        dot.style.boxShadow = "0 0 10px var(--cyan)";
    }
}

function checkInitialApiKey() {
    // Just a placeholder check. If they don't insert any key, it defaults to server environment key.
}

// 3. Tab Switching for Tools Control Room
function switchToolTab(tabId) {
    // Remove active class from all buttons and panes
    const buttons = document.querySelectorAll(".tab-btn");
    const panes = document.querySelectorAll(".tool-pane");
    
    buttons.forEach(btn => btn.classList.remove("active"));
    panes.forEach(pane => pane.classList.remove("active"));
    
    // Find clicked button based on tabId and set active
    const activeBtn = Array.from(buttons).find(btn => btn.getAttribute("onclick").includes(tabId));
    if (activeBtn) activeBtn.classList.add("active");
    
    // Show selected pane
    const targetPane = document.getElementById(tabId);
    if (targetPane) targetPane.classList.add("active");
}

// 4. Safe manual tool tester (API requests)
async function manualTestTool(event, toolName) {
    event.preventDefault();
    const resultBox = document.getElementById(`${toolName}-result`);
    
    // Setup inputs based on toolName
    let payload = {};
    let endpoint = `/api/test/${toolName}`;
    
    if (toolName === "weather") {
        const city = document.getElementById("weather-city").value;
        payload = { city };
    } else if (toolName === "github") {
        const query = document.getElementById("github-query").value;
        const language = document.getElementById("github-lang").value || null;
        payload = { query, language };
    } else if (toolName === "currency") {
        const amount = parseFloat(document.getElementById("currency-amount").value);
        const from_currency = document.getElementById("currency-from").value;
        const to_currency = document.getElementById("currency-to").value;
        payload = { amount, from_currency, to_currency };
    } else if (toolName === "math") {
        const expression = document.getElementById("math-expr").value;
        payload = { expression };
    } else if (toolName === "text") {
        const text = document.getElementById("text-content").value;
        payload = { text };
    }
    
    // Show spinner in results box
    resultBox.innerHTML = `
        <div style="display:flex; justify-content:center; align-items:center; height:100%; min-height:80px; gap: 8px;">
            <i class="fa-solid fa-spinner fa-spin" style="color: var(--purple);"></i> 
            <span>Consultando herramienta...</span>
        </div>
    `;
    
    try {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });
        
        if (response.ok) {
            const data = await response.json();
            resultBox.innerHTML = formatMarkdown(data.result);
        } else {
            resultBox.innerHTML = `<span style="color:var(--pink);">Error de API del servidor (HTTP ${response.status})</span>`;
        }
    } catch (err) {
        resultBox.innerHTML = `<span style="color:var(--pink);">Error al conectar: ${err.message}</span>`;
    }
}

// 5. Chat Turn Processing & Stream Parsing
function setupChatHandler() {
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const prompt = userInput.value.trim();
        if (!prompt || isChatRunning) return;
        
        isChatRunning = true;
        userInput.value = "";
        userInput.disabled = true;
        sendBtn.disabled = true;
        
        // Add User Bubble to history
        appendMessageBubble("user", prompt);
        
        // Create Agent Bubble and Status indicators
        const agentBubble = appendMessageBubble("agent", "");
        const agentMsgTextElement = agentBubble.querySelector(".message-text");
        
        // Reset status indicators
        const thoughtAccordion = document.getElementById("thoughtAccordion");
        const thoughtContent = document.getElementById("thoughtContent");
        const thoughtDots = thoughtAccordion.querySelector(".loading-dots");
        const toolCard = document.getElementById("toolExecutionCard");
        
        thoughtContent.textContent = "";
        thoughtAccordion.style.display = "block";
        thoughtAccordion.open = true;
        thoughtDots.style.display = "flex";
        toolCard.style.display = "none";
        
        let fullResponseText = "";
        let fullThoughtText = "";
        
        try {
            // Stream connection using standard POST fetch stream reader
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: prompt,
                    api_key: activeApiKey || null
                })
            });
            
            if (!res.ok) {
                throw new Error(`Fallo del servidor (HTTP ${res.status})`);
            }
            
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n\n");
                buffer = lines.pop(); // Keep partial line in buffer
                
                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const jsonStr = line.substring(6).trim();
                        if (!jsonStr) continue;
                        
                        try {
                            const event = JSON.parse(jsonStr);
                            
                            if (event.type === "thought") {
                                fullThoughtText += event.data;
                                thoughtContent.textContent = fullThoughtText;
                                thoughtContent.scrollTop = thoughtContent.scrollHeight;
                            } 
                            else if (event.type === "tool_start") {
                                // Show tool active neon loader
                                document.getElementById("activeToolName").textContent = `Ejecutando: ${event.data.name}`;
                                document.getElementById("activeToolArgs").textContent = JSON.stringify(event.data.args, null, 2);
                                toolCard.style.display = "flex";
                            } 
                            else if (event.type === "tool_end") {
                                // Hide loader shortly
                                toolCard.style.display = "none";
                            } 
                            else if (event.type === "text") {
                                // Turn off thought loader animation once text starts arriving
                                thoughtDots.style.display = "none";
                                fullResponseText += event.data;
                                agentMsgTextElement.innerHTML = formatMarkdown(fullResponseText);
                                scrollToBottom();
                            } 
                            else if (event.type === "error") {
                                throw new Error(event.data);
                            } 
                            else if (event.type === "done") {
                                break;
                            }
                        } catch (parseErr) {
                            console.error("Error parsing JSON line:", parseErr);
                        }
                    }
                }
            }
            
        } catch (error) {
            agentMsgTextElement.innerHTML = `<span style="color: var(--pink);"><i class="fa-solid fa-triangle-exclamation"></i> **Error:** ${error.message}</span>`;
            thoughtDots.style.display = "none";
            toolCard.style.display = "none";
        } finally {
            // Re-enable chat UI
            isChatRunning = false;
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
            
            // Clean up status dock
            thoughtDots.style.display = "none";
            toolCard.style.display = "none";
            
            // If thoughts were empty, hide thought accordion
            if (!fullThoughtText.trim()) {
                thoughtAccordion.style.display = "none";
            } else {
                // Auto-close thoughts to clean up interface after generation
                setTimeout(() => {
                    thoughtAccordion.open = false;
                }, 1000);
            }
        }
    });
}

// 6. Helpers for bubble creation & auto-scrolling
function appendMessageBubble(sender, text) {
    const chatHistory = document.getElementById("chatHistory");
    const bubble = document.createElement("div");
    bubble.classList.add("chat-bubble", `${sender}-message`);
    
    const senderIcon = sender === "user" ? "fa-solid fa-user-astronaut" : "fa-solid fa-robot";
    const senderName = sender === "user" ? "Tú" : "Antigravity Assistant";
    
    bubble.innerHTML = `
        <div class="message-sender">
            <i class="${senderIcon}"></i>
            <span>${senderName}</span>
        </div>
        <div class="message-text"></div>
    `;
    
    chatHistory.appendChild(bubble);
    bubble.querySelector(".message-text").innerHTML = formatMarkdown(text);
    scrollToBottom();
    return bubble;
}

function scrollToBottom() {
    const chatHistory = document.getElementById("chatHistory");
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// 7. Elegant & Fast Markdown Formatter
function formatMarkdown(text) {
    if (!text) return "";
    
    let html = text;
    
    // Replace escape characters
    html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    
    // Strong text: **word**
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Code blocks: ```code```
    html = html.replace(/```(.*?)\n([\s\S]*?)```/g, '<pre class="code-box"><code>$2</code></pre>');
    
    // Inline code: `code`
    html = html.replace(/`(.*?)`/g, "<code>$1</code>");
    
    // Markdown links: [text](url)
    html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color:var(--cyan);text-decoration:none;border-bottom:1px dashed var(--cyan);">$1</a>');
    
    // Headings: ### title
    html = html.replace(/###\s+(.*?)\n/g, "<h3>$1</h3>");
    
    // Bullet points: - item
    html = html.replace(/^\s*-\s+(.*?)$/gm, "<li>$1</li>");
    
    // Wrap consecutive list items in <ul>
    html = html.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
    
    // Line breaks
    html = html.replace(/\n/g, "<br>");
    
    return html;
}
