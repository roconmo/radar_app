FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit pandas

COPY streamlit_app.py .

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
