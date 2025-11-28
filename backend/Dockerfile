FROM python:3.12
EXPOSE 4000
WORKDIR /python-docker

ENV POSTGRES_HOST="db-postgres"
ENV POSTGRES_USER="postgres"
ENV POSTGRES_PASSWORD="password"
ENV REDIS_HOST="db-redis"
ENV MONGO_HOST="db-mongo"

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "app.py"]

