# Log Analyzer

Backend with fastapi+uvicorn for log analysis with LLMs.

- [Log Analyzer](#log-analyzer)
  - [API Architecture Setup](#api-architecture-setup)
  - [Setup](#setup)
    - [1. Create .env file](#1-create-env-file)
    - [2. Create shared volumes directory](#2-create-shared-volumes-directory)
  - [Running the log analysis service](#running-the-log-analysis-service)
    - [Option A) Docker Compose](#option-a-docker-compose)
      - [Note:](#note)
    - [Option B) Docker and local virtual env](#option-b-docker-and-local-virtual-env)
      - [Option Bi) Uvicorn server with fastapi with Docker](#option-bi-uvicorn-server-with-fastapi-with-docker)
      - [Option Bii) Uvicorn server with fastapi with venv](#option-bii-uvicorn-server-with-fastapi-with-venv)
    - [Optional: frontend with streamlit](#optional-frontend-with-streamlit)
    - [Optional: expose app through ngrok docker for sharing localhost on the internet](#optional-expose-app-through-ngrok-docker-for-sharing-localhost-on-the-internet)
  - [Testing](#testing)
  - [For Developers](#for-developers)
    - [To change schema of tables](#to-change-schema-of-tables)

## API Architecture Setup

[<img src="app/static/images/log analyzer.drawio.png">](https://link-to-your-URL/)

## Setup

### 1. Create .env file

Create a `.env` file with the following keys with updated values for unames and pass:

```yaml
# set to ERROR for deployment
DEBUG_LEVEL=DEBUG
# http api server
API_SERVER_PORT=8080
# openai api key
OPENAI_API_KEY=<OPENAI_API_KEY>
# langchain langsmith keys
USER_AGENT=log_analyzer
LANGCHAIN_PROJECT=log_analyzer
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=<LANGCHAIN_API_KEY>
# mysql mariadb
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=user
MYSQL_PASSWORD=pass
MYSQL_DATABASE=default
MYSQL_ROOT_PASSWORD=admin
# phpmyadmin mariadb
PMA_GUI_PORT=8001
PMA_HOST=${MYSQL_HOST}
PMA_PORT=${MYSQL_PORT}
PMA_USER=${MYSQL_USER}
PMA_PASSWORD=${MYSQL_PASSWORD}
```

### 2. Create shared volumes directory

```shell
mkdir -p volumes/log_analyzer
mkdir -p volumes/store
```

## Running the log analysis service

There are two options for running the analysis service. Both require `docker compose` (Available from the [official docker site](https://docs.docker.com/compose/install/)). `$docker-compose ...` style commands have been depreciated.

### Option A) Docker Compose

Note: some services are set to bind to all addresses which should be changed in a production environment.

```shell
# build all required containers
docker compose build
# start all services
docker compose up -d
```

The server will be available at <http://localhost:8080> if using the default port.

#### Note:

When changing settings in `docker-compose.yaml` for the mongodb service, the existing docker and shared volumes might have to be purged i.e. when changing replicaset name.

<p style="color:red;">WARNING: This will delete all existing user, document, and vector records.</p> 

```shell
docker-compose down
docker volume rm $(docker volume ls -q)
rm -rf volumes/store
```

### Option B) Docker and local virtual env

```shell
# build all required containers
docker compose build
# start mysql server & phpmyadmin server
docker compose up -d mysql mysql-admin
```

#### Option Bi) Uvicorn server with fastapi with Docker

Build server container and start server at HTTP port EXPOSED_HTTP_PORT

```shell
bash scripts/build_docker.sh
bash scripts/run_docker.sh -p EXPOSED_HTTP_PORT
```

The server will be available at <http://localhost:8080> if using the default port.

#### Option Bii) Uvicorn server with fastapi with venv

Install requirements inside venv or conda environment

```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Start server at HTTP port EXPOSED_HTTP_PORT. Note the host names must contain addresses when using docker microservices and the fastapi+uvicorn server outside the docker compose environment.

```shell
python app/server.py -p EXPOSED_HTTP_PORT
```

The server will be available at <http://localhost:8080> if using the default port.

### Optional: frontend with streamlit

```shell
pip install streamlit==1.38.0
streamlit run app/streamlit_frontend.py
```

### Optional: expose app through ngrok docker for sharing localhost on the internet

WARNING: Never use for production

```bash
# start log analyzer with python
# sign up for ngrok account at https://ngrok.com/
# https://ngrok.com/docs/using-ngrok-with/docker/
docker pull ngrok/ngrok
# for linux systems
docker run --net=host -it -e NGROK_AUTHTOKEN=<NGROK_AUTHTOKEN> ngrok/ngrok:latest http <EXPOSED_HTTP_PORT>
# for MacOS and windows
docker run -it -e NGROK_AUTHTOKEN=<NGROK_AUTHTOKEN> ngrok/ngrok:latest http host.docker.internal:<EXPOSED_HTTP_PORT>
```

## Testing

Note: all the microservices must already be running with docker compose.

Install requirements:

```shell
pip install -r tests/requirements.txt
```

Run tests:

```shell
pytest tests/
```

Generating coverage reports

```shell
coverage run -m pytest tests/
coverage report -m -i
```

## For Developers

### To change schema of tables

The following files must be edited.

-   Edit/add to `init.sql` for changing/adding log table schema
-   Edit/add to `app/api/log_format/log_parser.py` for parsing logs
-   Edit/add to `app/core.setup.py` for adding table schema and data sample info
-   Edit/add to `tests/conftests.py` for setting the correct values for the test database
-   Edit/add to `tests/api/test_mysql_api.py` for setting the correct values for the test database
