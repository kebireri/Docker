# 1. Local Docker: single-container API
### Build the Study Buddy API image from the Dockerfile in the current directory
docker build -t study-buddy:1.0 .

### Run the container locally, mapping container port 5000 to host port 5000
docker run --rm -p 5000:5000 study-buddy:1.0

### List all local Docker images
docker images

### List running containers
docker ps

### View logs for a specific running container
docker logs <container_id_or_name>

### Stop a running container gracefully
docker stop <container_id_or_name>

### Test the local health endpoint
curl http://localhost:5000/health

## 2. Local Docker Compose: API + Postgres
### Start the multi-container stack (API + Postgres), showing logs in the foreground
docker compose up

### Start the stack in the background (detached mode)
docker compose up -d

### See which services are running in this compose project
docker compose ps

### View logs for the API service
docker compose logs api

### View logs for the db (Postgres) service
docker compose logs db

### Follow API logs in real time (Ctrl+C to stop following)
docker compose logs -f api

### Restart only the API service (e.g. after a config change)
docker compose restart api

### Stop and remove containers and network (keeps volumes/data)
docker compose down

### Stop and remove containers, network, AND volumes (erases DB data)
docker compose down -v

## Create the sessions table in the local Postgres (via the db container)
### Run a one-off psql command inside the Postgres container to create the sessions table
docker exec -it study-buddy-db \
  psql -U postgres -d studybuddy \
  -c "CREATE TABLE sessions (id SERIAL PRIMARY KEY, topic TEXT NOT NULL, minutes INTEGER NOT NULL);"

# 3. Azure basics: resource group + ACR
### Log in to Azure interactively
az login

### Create a resource group for DevOps / cloud resources
az group create --name devops-rg --location switzerlandnorth

### Create an Azure Container Registry (ACR) to store Docker images
az acr create \
  --resource-group devops-rg \
  --name kevweacr \
  --sku Basic \
  --location switzerlandnorth

### (Optional) Log in to ACR for docker CLI
az acr login --name kevweacr

### Show the ACR login server (used in image tags)
az acr show \
  --name kevweacr \
  --resource-group devops-rg \
  --query loginServer \
  -o tsv

# 4. Tagging & pushing the image to ACR

Assuming you built study-buddy:1.0 locally and decided to call the repo study-buddy-api in ACR:

### Tag the local image so it points to the ACR registry/repository
docker tag study-buddy:1.0 kevweacr.azurecr.io/study-buddy-api:1.0

### Push the image to Azure Container Registry
docker push kevweacr.azurecr.io/study-buddy-api:1.0

### List repositories in ACR (to confirm the image repo exists)
az acr repository list \
  --name kevweacr \
  --output table

### List tags for the study-buddy-api repository in ACR
az acr repository show-tags \
  --name kevweacr \
  --repository study-buddy-api \
  --output table

# 5. Azure Container Apps setup (environment + logs)
### Install or upgrade the Azure Container Apps CLI extension
az extension add --name containerapp --upgrade

### Ensure required resource providers are registered
az provider register --namespace Microsoft.Web
az provider register --namespace Microsoft.App

### Create a Log Analytics workspace for container logs
az monitor log-analytics workspace create \
  --resource-group devops-rg \
  --workspace-name devops-logs \
  --location switzerlandnorth

### Get the workspace ID (customerId) – used when creating the Container Apps environment
az monitor log-analytics workspace show \
  --resource-group devops-rg \
  --workspace-name devops-logs \
  --query customerId \
  -o tsv

### Get the workspace shared keys (primarySharedKey used below)
az monitor log-analytics workspace get-shared-keys \
  --resource-group devops-rg \
  --workspace-name devops-logs


Use the customerId and primarySharedKey from above as WORKSPACE_ID and WORKSPACE_KEY:

### Create a Container Apps Environment (logical home/cluster for apps)
az containerapp env create \
  --name devops-env \
  --resource-group devops-rg \
  --location switzerlandnorth \
  --logs-workspace-id "<WORKSPACE_ID>" \
  --logs-workspace-key "<WORKSPACE_KEY>"

# 6. Create the Container App from the ACR image
### Get ACR credentials (username + passwords) for Container Apps to pull images
az acr credential show \
  --name kevweacr \
  --resource-group devops-rg

### Create the Container App using the image from ACR
az containerapp create \
  --name study-buddy-api-cloud \
  --resource-group devops-rg \
  --environment devops-env \
  --image kevweacr.azurecr.io/study-buddy-api:1.0 \
  --ingress external \
  --target-port 5000 \
  --registry-server kevweacr.azurecr.io \
  --registry-username <ACR_USERNAME> \
  --registry-password "<ACR_PASSWORD>"

### Retrieve the public FQDN (URL) of the Container App
az containerapp show \
  --name study-buddy-api-cloud \
  --resource-group devops-rg \
  --query properties.configuration.ingress.fqdn \
  -o tsv

# 7. Azure PostgreSQL (cloud DB) setup
### Create an Azure Database for PostgreSQL Flexible Server (basic learning setup)
az postgres flexible-server create \
  --resource-group devops-rg \
  --name kevwestudydb \
  --location switzerlandnorth \
  --admin-user studyadmin \
  --admin-password <YOUR_STRONG_DB_PASSWORD> \
  --database-name studybuddy \
  --public-access all

### Get the fully-qualified domain name (host) of the Postgres server
az postgres flexible-server show \
  --resource-group devops-rg \
  --name kevwestudydb \
  --query fullyQualifiedDomainName \
  -o tsv

# 8. Create the sessions table in Azure Postgres (via Docker psql)
### Use a temporary Postgres container to connect to Azure Postgres over SSL
docker run -it --rm postgres:16 psql \
  --host=kevwestudydb.postgres.database.azure.com \
  --port=5432 \
  --username=studyadmin \
  --dbname=studybuddy \
  --set=sslmode=require


Inside the psql prompt:

CREATE TABLE sessions (
  id SERIAL PRIMARY KEY,
  topic TEXT NOT NULL,
  minutes INTEGER NOT NULL
);

\q

# 9. Wire the Container App to Azure Postgres (env vars)
### Update the Container App to use Azure Postgres via environment variables
az containerapp update \
  --name study-buddy-api-cloud \
  --resource-group devops-rg \
  --set-env-vars \
    DB_HOST=kevwestudydb.postgres.database.azure.com \
    DB_NAME=studybuddy \
    DB_USER=studyadmin \
    DB_PASSWORD=<YOUR_STRONG_DB_PASSWORD>

# 10. Cloud API testing (from bash)

Replace <FQDN> with the hostname returned by az containerapp show
(e.g. study-buddy-api-cloud.ashycoast-f2a884a1.switzerlandnorth.azurecontainerapps.io).

### Health check from the internet to the cloud API
curl "https://<FQDN>/health"

### List all study sessions (reads from Azure Postgres)
curl "https://<FQDN>/sessions"

### Create a new study session (writes to Azure Postgres)
curl -X POST \
  "https://<FQDN>/sessions" \
  -H "Content-Type: application/json" \
  -d '{"topic": "Cloud DB", "minutes": 40}'

### Confirm the new session is stored
curl "https://<FQDN>/sessions"