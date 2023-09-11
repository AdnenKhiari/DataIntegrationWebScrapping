FROM python:3.8.17-slim AS builder
COPY CompanyDetails/requirements.txt requirements.txt
RUN pip install --default-timeout=300 -r requirements.txt

FROM python:3.8.17-slim
USER root
RUN apt-get update && apt-get install -y gnupg -y curl && \
    (curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -)  && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && apt-get update && apt-get install -y && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 &&  ACCEPT_EULA=Y apt-get install -y mssql-tools18  && \
    echo 'export PATH="$PATH:/opt/mssql-tools18/bin"' >> ~/.bashrc
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
WORKDIR /app
COPY CompanyDetails/app /app
CMD ["python","main.py"]