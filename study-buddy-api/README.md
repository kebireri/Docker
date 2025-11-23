# **Study Buddy API**

The Study Buddy API is a lightweight Python/Flask service designed to track study sessions.<br>
It was developed as an end-to-end DevOps and cloud engineering project, covering the full lifecycle from local development to cloud deployment.

## **Overview**
The API provides three endpoints:

- **GET /health** — service status  
- **GET /sessions** — list all study sessions  
- **POST /sessions** — create a session (topic + minutes)

Data is stored in a PostgreSQL database.

The project started as a local Docker application, expanded to a multi-container setup using Docker Compose, and was deployed to Microsoft Azure using **Azure Container Registry**, **Azure Container Apps**, and **Azure PostgreSQL Flexible Server**.

## **Architecture**
- **Local:**  
  - Dockerized Flask API  
  - Postgres container via Docker Compose  
  - Internal container networking  

- **Cloud:**  
  - Image stored in Azure Container Registry (ACR)  
  - API hosted on Azure Container Apps  
  - Managed database on Azure PostgreSQL  
  - Environment variables used for configuration  

## **Skills Demonstrated**
- Containerizing applications with Docker  
- Multi-container orchestration using Docker Compose  
- Pushing and pulling images from ACR  
- Deploying to Azure Container Apps  
- Connecting services to a managed cloud database  
- Using environment variables for configuration  
- Testing REST APIs with curl  

### **Check if the app is running**
`GET /health`  
Returns:
```json
{"service": "study-buddy", "status": "ok"}
