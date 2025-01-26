FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/Input

RUN ls -l /app


RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*


# Copy the repository contents to the working directory

COPY ./requirements.txt requirements.txt
COPY ./.env .env
COPY ./a2023-45.pdf a2023-45.pdf
COPY ./app_new_theme.py app_new_theme.py
COPY ./config_loader.py config_loader.py
COPY ./config.yaml config.yaml
COPY ./create_vectordb.py create_vectordb.py
COPY ./embeddings_handler.py embeddings_handler.py
COPY ./query_assistant.py query_assistant.py
COPY ./text_processor.py text_processor.py
COPY ./utils.py utils.py
COPY ./vector_store.py vector_store.py

COPY Input/ /app/Input/

RUN pip3 install -r requirements.txt

RUN rm -rf /usr/local/cuda* && \
    rm -rf /usr/lib/x86_64-linux-gnu/libcuda* && \
    rm -rf /usr/lib/x86_64-linux-gnu/libnvidia* && \
    rm -rf /usr/local/nvidia/lib64/libcuda* && \
    rm -rf /usr/local/nvidia/lib64/libnvidia*

EXPOSE 8080

RUN python create_vectordb.py

CMD ["python", "app_new_theme.py"]



