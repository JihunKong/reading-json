FROM python:3.11-slim
WORKDIR /app
COPY cli.py /app/cli.py
COPY schemas /app/schemas
COPY prompts /app/prompts
COPY seeds /app/seeds
RUN pip install --no-cache-dir regex
ENTRYPOINT ["python","/app/cli.py"]
