# Optional container build. Render uses the native Python runtime by default
# (see render.yaml); this is here for Docker-based hosts and local parity.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app.py start.sh ./
COPY .streamlit/ .streamlit/

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
  CMD python -c "import urllib.request,os;urllib.request.urlopen(f\"http://localhost:{os.getenv('PORT','8501')}/_stcore/health\")"

CMD ["bash", "start.sh"]
