# Multi-Agent QA System

Este repositorio contiene la implementación de un **sistema multi-agente de preguntas y respuestas** basado en LangGraph y FastAPI. Cada agente especializado (legal, contable, médico, genérico) procesa la entrada de forma secuencial según la categoría detectada.

---

## 1. Estructura de carpetas

```
multi_agent/
├── app/
│   ├── __init__.py
│   ├── main_multi_agent.py      # FastAPI app y definición de endpoints
│   ├── multi_agent.py           # Construcción del grafo LangGraph
│   ├── prompts/                 # Prompts para cada cadena LLM
│   │   ├── classifier.txt
│   │   ├── legal.txt
│   │   ├── accounting.txt
│   │   ├── medical.txt
│   │   └── generic.txt
│   └── requirements_multi_agent.txt
├── Dockerfile.txt               # Para construir la imagen Docker
├── docker-compose.yml           # Para orquestar el contenedor
└── .env                         # Variables de entorno (no versionar)
```

---

## 2. Requisitos

- **Python 3.11+**  
- **pip**  
- **Docker & Docker Compose** (opcional, para despliegue en contenedor)  
- **Clave de OpenAI** (exportar en `.env`)

---

## 3.  Instalación y configuración

3.1 **Clona este repositorio**  
   ```bash
   git clone https://github.com/tu-usuario/tu-repo-multi-agent.git
   cd tu-repo-multi-agent/multi_agent
   ```

3.2 **Crea y activa un entorno virtual**  
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3.3 **Instala dependencias**  
   ```bash
   pip install --upgrade pip
   pip install -r app/requirements_multi_agent.txt
   ```

3.4 **Configura variables de entorno**  
   Crea un archivo `.env` en la raíz de `multi_agent/` con:
   ```ini
   OPENAI_API_KEY=sk-...
   ```
   El código de FastAPI usa `python-dotenv` para cargar esta variable.

---

## 4. Ejecución local (FastAPI + Uvicorn)

Hay varias formas de ejecutar el servidor:

- **Desde cualquier terminal**  
  ```bash
  #sitúate en el root, debes ver app
  uvicorn app.main_multi_agent:api --reload
  ```
- **En Visual Studio Code**  
  4.1 Abre el proyecto en VS Code.  
  4.2 Pulsa <kbd>Ctrl+`</kbd> (o ve a *View → Terminal*) para abrir la terminal integrada.  
  4.3 Asegúrate de estar en la carpeta `multi_agent/app`.  
  4.4 Ejecuta:
     ```bash
     uvicorn main_multi_agent:api --reload --host 0.0.0.0 --port 8000
     ```

A) **Prueba el endpoint**  
   En tu navegador o con `curl`/Postman:
   ```
   POST http://localhost:8000/qa
   Content-Type: application/json

   {
     "question": "¿Qué es un amparo indirecto?"
   }
   ```
   Recibirás una respuesta JSON con:
   ```json
   {
     "category_id": 1,
     "category_label": "Legal",
     "answer": "Respuesta generada por el agente legal…"
   }
   ```

En cualquier terminal en tu local:
   ```
   curl -X POST http://127.0.0.1:8000/qa -H "Content-Type: application/json" -d '{"question": "¿Qué es un contrato de arrendamiento?"}' 
  ```

---

## 5. Despliegue con Docker

5.1 **Construye la imagen**  
   Desde la carpeta `multi_agent/`:
   ```bash
   docker build -f Dockerfile.txt -t multi-agent-qa .
   ```

5.2 **Arranca con Docker Compose**  
   ```bash
   docker-compose up --build
   ```
   - El servicio `qa` quedará expuesto en el puerto **8000**.

5.3 **Comprueba el servicio**  
   Igual que en la sección de ejecución local, apunta a:
   ```
   http://localhost:8000/docs
   ```

   después click en **POST** y luego en **try it out**.

---

## 6. Descripción rápida del flujo multi-agente

6.1 **Clasificador**: LLMChain que etiqueta la pregunta (`category_id`).  
6.2 **Router**: Decide a qué nodo enviar (legal, contable, médico o genérico).  
6.3 **Nodo de dominio**: Cada especialista ejecuta su propio LLMChain con su prompt.  
6.4 **Respuesta**: Estado enriquecido con `category_label` y `answer`.  

El grafo se construye en `app/multi_agent.py` y se compila en un objeto `app_agent` que ofrece el método `.invoke({ "question": ... })`.

---

*¡Listo para usar tu sistema multi-agente de QA! Si tienes dudas o quieres contribuir, abre un issue o PR.*
