Agente IA con 5 herramientas

--Backend (tools.py, app.py, requirements.txt): Contiene las 5 herramientas (Clima, GitHub, Conversión de divisas, Calculadora matemática segura y Analizador de texto) integradas con el Google Antigravity SDK y transmitidas en tiempo real por FastAPI mediante eventos SSE.

--Frontend (index.html, style.css, app.js): Una consola interactiva ultramoderna con diseño de Glassmorfismo, gradientes neón HSL, animaciones fluidas y formularios interactivos para probar cada herramienta manualmente.


Para comenzar rápidamente:

-Activa tu entorno virtual (source .venv/bin/activate).

-Configura tu GEMINI_API_KEY o pégala directamente en la ranura de seguridad superior de la interfaz web.

-Inicia el servidor con python3 -m uvicorn app:app --reload.

-Abre http://localhost:8000 en tu navegador.
