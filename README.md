Agente IA con 5 herramientas

--Backend (tools.py, app.py, requirements.txt): Contiene las 5 herramientas (Clima, GitHub, Conversión de divisas, Calculadora matemática segura y Analizador de texto) integradas con el Google Antigravity SDK y transmitidas en tiempo real por FastAPI mediante eventos SSE.

--Frontend (index.html, style.css, app.js): Una consola interactiva ultramoderna con diseño de Glassmorfismo, gradientes neón HSL, animaciones fluidas y formularios interactivos para probar cada herramienta manualmente.


Para comenzar rápidamente:

1-Activa tu entorno virtual (source .venv/bin/activate).

2-Configura tu GEMINI_API_KEY o pégala directamente en la ranura de seguridad superior de la interfaz web.

3-Inicia el servidor con python3 -m uvicorn app:app --reload.

4-Abre http://localhost:8000 en tu navegador.


------5 Herramientas------

El agente de IA esta equipado con las siguientes 5 herramientas implementadas en Python de manera segura y eficiente:

1.get_weather(city: str) -> str: Consulta el clima actual y el pronóstico de cualquier ciudad del mundo en tiempo real utilizando la API pública y sin llave de wttr.in.
2.search_github_repos(query: str, language: str = None) -> str: Realiza búsquedas de repositorios populares en GitHub mediante la API oficial de GitHub, devolviendo una lista formateada en Markdown con las estrellas, descripción y enlaces.
3.convert_currency(amount: float, from_currency: str, to_currency: str) -> str: Realiza conversiones de divisas en tiempo real basadas en tasas de cambio actuales usando la API libre de exchangerate-api (con respaldo interno estático).
4.calculate_expression(expression: str) -> str: Evalúa expresiones matemáticas avanzadas de manera 100% segura usando un subconjunto seguro de funciones de Python (sin recurrir a eval inseguros).
5.analyze_text(text: str) -> str: Analiza cualquier fragmento de texto proporcionado para calcular métricas como recuento de palabras y caracteres, tiempo estimado de lectura, densidad de palabras clave y estimación de legibilidad Flesch-Kincaid.
