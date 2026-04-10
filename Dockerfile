FROM python:3.10-slim-bookworm

RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=user artemis_env/ artemis_env/
COPY --chown=user server/ server/
COPY --chown=user README.md openenv.yaml inference.py pyproject.toml uv.lock ./
EXPOSE 7860
ENV PYTHONPATH=$HOME/app
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]