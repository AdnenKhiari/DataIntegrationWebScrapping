FROM python:3.8.17-slim AS builder
RUN apt-get update -y
COPY HelloWork/requirements.txt /app/HelloWork/requirements.txt
RUN pip3 install -r /app/HelloWork/requirements.txt

FROM python:3.8.17-slim
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
WORKDIR /app
COPY HelloWork /app/HelloWork
COPY BufferWriter /app/BufferWriter
ENV PYTHONPATH="./"
CMD ["python","HelloWork/main.py"]