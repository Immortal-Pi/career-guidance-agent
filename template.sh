#!/bin/bash

# creating directory structure
mkdir -p infra
mkdir -p infra/sam
mkdir -p infra/terraform
mkdir -p services
mkdir -p services/scraper_lambda
mkdir -p services/scraper_lambda/src
mkdir -p services/ingest_lambda
mkdir -p services/ingest_lambda/src
mkdir -p services/agent_lambda
mkdir -p services/agent_lambda/src
mkdir -p shared
mkdir -p shared/agent_core
mkdir -p web
mkdir -p scripts
mkdir -p docs

# creating files 
touch services/scraper_lambda/requirements.txt
touch services/ingest_lambda/requirements.txt
touch services/agent_lambda/requirements.txt
touch shared/agent_core/chunking.py
touch shared/agent_core/embedding_client.py
touch web/index.html
touch web/styles.css
touch touch web/app.js
touch scripts/db_init.sql
touch scripts/local_smoke_test.py
touch config.py
touch .env 
touch setup.py 
touch app.py 
touch research/trails.ipynb 
touch requirements.txt 

echo "Directory and files created successfully"
