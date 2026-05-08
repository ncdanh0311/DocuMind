# 🚀 Modern Docker Setup Guide (Recommended)

Docker is the preferred way to run DocuMind. It automates the complex setup of AI models, specialized databases, and networking with a single command.

---

## 1. Why Docker?
- **Zero Configuration**: No need to install PostgreSQL or Python on your host machine.
- **AI-Ready**: Includes a specialized `pgvector` image for semantic search.
- **Consistency**: Ensures the app runs exactly the same way on every machine.

---

## 2. Quick Start
1. Ensure **Docker Desktop** is installed and running.
2. Open your terminal at the project root.
3. Run the magic command:
   ```bash
   docker-compose up --build
   ```

---

## 3. Managing Services
- **Stop services**: Press `Ctrl + C` or run `docker-compose down`.
- **Run in Background**: `docker-compose up -d` (useful if you don't want to see logs constantly).
- **View Logs**: `docker logs -f documind-backend`.
- **Rebuild**: If you change dependencies in `pyproject.toml`, run `docker-compose up --build`.

---

## 4. Accessing the System
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Database Access**: You can connect to the database from your host using:
  - **Host**: `localhost`
  - **Port**: `5432`
  - **User**: `postgres`
  - **Password**: `password`
  - **Database**: `documind`

---

## 5. Development Workflow (Hot-Reload)
The `backend/` folder on your computer is linked to the container. 
**When you save a file in your IDE, the server inside Docker will automatically restart.** You do NOT need to rebuild the container for every code change.

---

## 💡 Troubleshooting
- **ModuleNotFoundError**: This usually happens if you're not mounting the volume correctly. Check your `docker-compose.yml` for the correct paths.
- **Port 5432 or 8000 already in use**: Stop any local PostgreSQL or FastAPI instances running on your machine before starting Docker.
- **Empty Database**: If you just switched to Docker, your local accounts will NOT be here. **You must register a new account on the mobile app.**
- **Vector Type Error**: Our `docker-compose` is configured to automatically enable this extension. If it fails, check the logs of the `documind-db` container.
