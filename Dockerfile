FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY prompt_mirror.py .
COPY fonts/ ./fonts/
COPY .streamlit/ ./.streamlit/

EXPOSE 8501

CMD ["streamlit", "run", "prompt_mirror.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
