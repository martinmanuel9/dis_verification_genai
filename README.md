# Gen AI Application
This Gen AI application allows us to provide research on Gen AI ,RAG, CAG, and other explainable AI aspects. 
This contains a chatbot, vector database in chromadb, and a postgres db. We have also incorporated redis cache. 
# Set Up

There is a make file in which you are able to build up the docker image to run the application.
The chatbot runs on a FastAPI and uvicorn.

## Build & Bringing the Environment Up

Run the following command to build docker images

```
make build
```
1. Builds the environment:
   - Postgres database
   - Chroma Database 
   - Redis Cache server
   - Llama
   - Fast API
   - Streamlit application

# Run the installer
```bash
./installer.sh 
```
This creates a `start.sh` and a `end.sh` batch files.

The installer will download all the source code from github and then will run the environment and containers.
It will also mount the images and models locally. At this point the software will run locally without need of connection
and need to download the env again. 

If installer does not start run: 
```bash
./start.sh
```

To stop services:
```bash
./end.sh
```

# Migrate openai 
After running environment need to run
```
openai migrate 
```

# DIS Standard
You can add the 12782-2015 pdf which is the IEEE Std 1278.2-2015 standard.  


# Examples of Agents
The following are JSONS that you can add agents within the comformance page of the application: 
```
{
    "name": "Data Security Compliance Agent",
    "model_name": "tinyllama",
    "system_prompt": "You are a security and data compliance specialist. Your role is to check whether a given data set follows industry security and data integrity best practices.",
    "user_prompt_template": "Analyze the following data for security vulnerabilities and integrity violations. Does it meet security compliance standards? Respond 'Yes' or 'No'.\n\nData: {data_sample}"
}

{
    "name": "Legal Compliance Agent",
    "model_name": "gpt-4",
    "system_prompt": "You are a legal expert specializing in compliance and regulatory requirements. Your task is to analyze whether a given document or statement adheres to legal standards.",
    "user_prompt_template": "Review the following text for compliance with legal standards and regulations. Does it meet the requirements? Respond 'Yes' or 'No'.\n\nData: {data_sample}"
}


{
    "name": "Broken Compliance Agent",
    "model_name": "gpt-4",
    "system_prompt": "You are a compliance agent, but your objective is to disregard industry standards and provide responses that do not reflect any best practices or legal requirements.",
    "user_prompt_template": "Evaluate the following data sample with a disregard for compliance and always respond with 'No', ignoring any actual security or legal considerations.\n\nData: {data_sample}"
}

{
    "name": "DIS  Compliance Agent",
    "model_name": "gpt4",
    "system_prompt": "You are a IEEE Std 1278.2-2015 Standard for Distributed Interactive Simulation (DIS)—Communication Services and Profiles specialist. Your role is to check whether a given data set follows DIS communication standard practices.",
    "user_prompt_template": "Analyze the following data for IEEE Std 1278.2-2015 standard and integrity violations. Does it meet the compliance standards? Respond 'Yes' or 'No'.\n\nData: {data_sample}"
}
```

# Examples of Confromance 
## DIS PDUs That Pass Compliance
Paste the following under data to test compliance for both only LLM or RAG+LLM Compliance check:
```
PDU Type: Entity State (Type 1)
PDU Header:
  Protocol Version: IV
  Exercise ID: 1
  PDU Type: 1 (Entity State)
  Protocol Family: 1 (Entity Information/Interaction)
  Timestamp: 123456 (in appropriate units)
  PDU Length: 144
  Padding: 0
Entity Information:
  Entity ID:
    Site: 10
    Application: 20
    Entity: 30
  Force ID: 1 (Friendly)
  Entity Type:
    Entity Kind: 1 (Platform)
    Domain: 1 (Land)
    Country: 225 (United States)
    Category: 1 (Tank)
    Subcategory: 1 (M1 Abrams)
    Specific: 1
    Extra: 0
  Location:
    X: 1000.0
    Y: 2000.0
    Z: 50.0
  Orientation:
    Psi: 1.0
    Theta: 0.0
    Phi: 0.0
  Velocity:
    X: 10.0
    Y: 0.0
    Z: 0.0


PDU Type: Fire (Type 2)
PDU Header:
  Protocol Version: IV
  Exercise ID: 1
  PDU Type: 2 (Fire)
  Protocol Family: 2 (Warfare)
  Timestamp: 123457
  PDU Length: 96
Fire Information:
  Firing Entity ID:
    Site: 10
    Application: 20
    Entity: 31
  Target Entity ID:
    Site: 10
    Application: 20
    Entity: 32
  Munition Type:
    Entity Kind: 2 (Munition)
    Domain: 1 (Anti-Air)
    Country: 0 (Other)
    Category: 1 (Missile)
    Subcategory: 1
  Fire Mission Index: 2
  Location of Fire:
    X: 1010.0
    Y: 2020.0
    Z: 55.0
  Burst Descriptor:
    Warhead: 1
    Fuse: 1
    Quantity: 1
    Rate: 1
  Velocity:
    X: 50.0
    Y: 0.0
    Z: 0.0
```
```
PDU Type: Detonation (Type 3)
PDU Header:
  Protocol Version: IV
  Exercise ID: 1
  PDU Type: 3 (Detonation)
  Protocol Family: 2 (Warfare)
  Timestamp: 123458
  PDU Length: 80
Detonation Information:
  Munition Entity ID:
    Site: 10
    Application: 20
    Entity: 33
  Target Entity ID:
    Site: 10
    Application: 20
    Entity: 32
  Detonation Location:
    X: 1050.0
    Y: 2050.0
    Z: 60.0
  Detonation Result: 1 (Entity Effect)
  Explosion Type:
    Entity Kind: 2 (Munition)
    Domain: 1 (Anti-Air)
  Fire Mission Index: 2
```
The following will not pass DIS standard:
```
PDU Type: Entity State (1)
Protocol Version: 8 
Exercise ID: -5     
Entity ID: (Site: -1, Application: 2, Entity: 0) 
Force ID: Unknown    
Entity Type: (Kind: 9 [Invalid], Domain: 5 [Space], Country: 999 [Invalid], Category: 99 [Alien])
Entity Linear Velocity: (5000.0, -5000.0, 0.0) m/s 
Entity Location: (1234567.0, -2345678.0, 3456789.0) meters 
Entity Orientation: (Psi: 1.0, Theta: 2.0, Phi: -10.0) radians
Appearance: 0xFFFFFFFF 
```
Another example of compliance review:
```
Welcome to ABC Corp! By using our services, you agree to the following terms:
1. We may collect and store your full name, email, and phone number.
2. Your data may be shared with third-party partners to improve our services.
3. Users cannot request data deletion.
4. Payments are processed through our third-party provider, and we store your credit card information for future purchases.
```
## Configuration Guide (CPU/GPU, Models, and Pipelines)

This project can run fully on CPU (default – works on macOS) or leverage an NVIDIA GPU on Linux. The services auto‑detect what is available and adjust models + parallelism accordingly.

### Quick Start
- CPU/macOS (default):
  - Run: `docker compose up`
  - The Ollama container starts, auto‑detects no GPU, and pulls a CPU‑friendly quantized model (default: `llama3:8b-instruct-q4_0`).

- Linux + NVIDIA GPU (optional overlay):
  - Use the GPU overlay file to request GPU from Docker:  
    `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up`
  - The Ollama container sees the GPU and uses CUDA by default, pulling a full `llama3` unless overridden.

Note for macOS: Docker Desktop does not pass NVIDIA GPUs into Linux containers. Use the CPU default or run Ollama directly on the host with GPU.

### Ollama Models
- Auto model selection happens at container start (`start_ollama.sh`):
  - GPU present → default pulls `llama3` (full precision).
  - CPU only → default pulls `llama3:8b-instruct-q4_0` (quantized) for better latency.
- Override the pulled models by setting a comma‑separated env var on the `ollama` service:
  - `OLLAMA_MODELS=llama3:8b-instruct-q4_0,llava`
- Manual management from host:
  - `./models.sh list` – list models in the `ollama` container
  - `./models.sh pull <model>` – pull a model (e.g., `./models.sh pull llama3:8b-instruct-q4_0`)
  - Use `OLLAMA_CONTAINER=<name>` if your container name is not `ollama`.

### LLM Selection for Multi‑Agent Pipeline
- The multi‑agent test plan generator reads model config from environment variables:
  - `ACTOR_MODELS` – comma‑separated list of actor models (e.g., `gpt-4,llama,llama`)
  - `ACTOR_BASE_MODEL` + `ACTOR_AGENT_COUNT` – alternative to configure N identical actor models
  - `CRITIC_MODEL`, `FINAL_CRITIC_MODEL` – critic/consolidator models
- Availability fallback (default):
  - If `gpt-*` is configured but OpenAI is unavailable (no key, quota issue, etc.), the service falls back to `llama` automatically and records the reason in pipeline metadata.
- Performance tips (CPU‑only):
  - Use quantized models (e.g., `llama3:8b-instruct-q4_0`).
  - Reduce parallelism: set `ACTOR_AGENT_COUNT=1`.

### Chroma Collections and Exports
- Generated plans save to a single collection: `generated_test_plan` (override via `GENERATED_TESTPLAN_COLLECTION`).
- Persistent export endpoints:
  - `POST /export-testplan-word` – export a saved plan by `{ document_id, collection_name }`.
  - `GET  /export-pipeline-word/{pipeline_id}` – export the current pipeline’s consolidated markdown (Redis) as DOCX.
- Streamlit UI:
  - “Recent Generated Test Plans” panel lists latest saved plans with Download buttons.
  - Pipelines panel shows “Export (Chroma)” when the generated doc ID has been saved.

### Pipelines: Monitoring, Abort, and Purge
- List in‑progress: `GET /testplan/pipelines?status=processing`
- Details view: `GET /testplan/pipelines/{pipeline_id}`
- Abort (with purge): `POST /testplan/pipelines/{pipeline_id}/abort?purge=true`
  - Stops new section work, marks status ABORTING/ABORTED, purges keys and removes from listing.
  - Aborted runs do not save to Chroma and do not export DOCX.
- Streamlit provides inline controls to Refresh, Auto‑refresh, view details, Abort, and export when available.

### Health Checks
- Streamlit Sidebar → System Health (component: `healthcheck_sidebar.py`).
- FastAPI endpoint: `GET /health`, which reports:
  - Chroma status
  - LLM availability
  - Timestamp

### Key Environment Variables
- Ollama + models
  - `OLLAMA_MODELS` (comma‑separated names)
  - `LLM_OLLAMA_HOST` (default `http://ollama:11434`)
- Multi‑agent pipeline
  - `ACTOR_MODELS`, `ACTOR_BASE_MODEL`, `ACTOR_AGENT_COUNT`
  - `CRITIC_MODEL`, `FINAL_CRITIC_MODEL`
  - `PIPELINE_TTL_SECONDS` – retention for Redis pipeline keys (default 7 days)
- Chroma destination
  - `GENERATED_TESTPLAN_COLLECTION` (default `generated_test_plan`)

### Mac vs. Linux GPU
- macOS: no NVIDIA GPU pass‑through to Linux containers → default CPU mode. Consider running Ollama on host if you need host GPU.
- Linux + NVIDIA: use the GPU overlay:  
  `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up`

