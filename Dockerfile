FROM python:3.13-slim
WORKDIR /app
COPY requirements/api.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
RUN pip install --no-cache-dir --no-deps \
    https://github.com/explosion/spacy-models/releases/download/fr_core_news_md-3.8.0/fr_core_news_md-3.8.0-py3-none-any.whl \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --no-deps .
RUN useradd --uid 10001 --create-home poc
USER poc
EXPOSE 8000
CMD ["uvicorn", "triage_poc.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
