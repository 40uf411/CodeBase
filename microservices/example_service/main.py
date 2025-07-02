import os
import subprocess
import logging
import psutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# --- Configuration ---
SERVICE_NAME = "example_service"
LOG_DIR = "logs" # Relative to the script's location
MAX_LOG_LINES_TO_READ = 20 # Max number of log lines to return in health check

# --- Logging Setup ---
# Determine the absolute path for the log directory and file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ABS_LOG_DIR = os.path.join(SCRIPT_DIR, LOG_DIR)
ABS_LOG_FILE = os.path.join(ABS_LOG_DIR, f"{SERVICE_NAME}.log")

if not os.path.exists(ABS_LOG_DIR):
    os.makedirs(ABS_LOG_DIR)
    # Create an empty log file if it doesn't exist, so it can be read by get_recent_logs
    open(ABS_LOG_FILE, 'a').close()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(ABS_LOG_FILE),
        logging.StreamHandler() # Also log to console
    ]
)

logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(
    title=SERVICE_NAME,
    description=f"API for managing and monitoring the {SERVICE_NAME}",
    version="0.1.0",
)

# --- In-memory state (for simulation) ---
# Using a dictionary for status to allow mutability from within endpoint functions
service_status_memory = {"status": "running"}

# --- Helper Functions ---
def get_recent_logs(log_file_path: str, num_lines: int) -> List[str]:
    """Reads the last N lines from a log file."""
    if not os.path.exists(log_file_path):
        logger.warning(f"Log file {log_file_path} not found.")
        return ["Log file not found."]
    try:
        with open(log_file_path, "r") as f:
            lines = f.readlines()
        # Return last num_lines, or all lines if fewer than num_lines
        return [line.strip() for line in lines[-num_lines:]]
    except Exception as e:
        logger.error(f"Error reading log file {log_file_path}: {e}", exc_info=True)
        return [f"Error reading log file: {str(e)}"]

# --- Pydantic Models for Response Schemas ---
class RootResponse(BaseModel):
    message: str

class HealthResponse(BaseModel):
    service_name: str
    status: str
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    total_disk_space_gb: float
    used_disk_space_gb: float
    free_disk_space_gb: float
    recent_logs: List[str]

class ControlResponse(BaseModel):
    message: str
    current_status: str

# --- API Endpoints ---
@app.get("/", response_model=RootResponse, summary="Root endpoint", description="Returns a welcome message.")
async def read_root():
    logger.info("Root endpoint '/' accessed.")
    return RootResponse(message=f"Welcome to {SERVICE_NAME}. Visit /docs for API documentation.")

@app.get("/health", response_model=HealthResponse, summary="Health Check", description="Returns the current health and metrics of the service.")
async def health_check():
    logger.info("Health check endpoint '/health' accessed.")
    try:
        disk_info = psutil.disk_usage('/')
        # Read logs from the absolute path
        recent_logs = get_recent_logs(ABS_LOG_FILE, MAX_LOG_LINES_TO_READ)

        return HealthResponse(
            service_name=SERVICE_NAME,
            status=service_status_memory["status"],
            cpu_usage_percent=psutil.cpu_percent(),
            memory_usage_percent=psutil.virtual_memory().percent,
            disk_usage_percent=disk_info.percent,
            total_disk_space_gb=round(disk_info.total / (1024**3), 2),
            used_disk_space_gb=round(disk_info.used / (1024**3), 2),
            free_disk_space_gb=round(disk_info.free / (1024**3), 2),
            recent_logs=recent_logs,
        )
    except Exception as e:
        logger.error(f"Error during health check: {e}", exc_info=True)
        # Return a 500 error with detail to the client
        raise HTTPException(status_code=500, detail=f"Error collecting health data: {str(e)}")

@app.post("/stop", response_model=ControlResponse, summary="Stop Service (Simulated)", description="Simulates stopping the service.")
async def stop_service():
    global service_status_memory
    logger.info("'/stop' endpoint called. Attempting to stop service (simulated).")
    service_status_memory["status"] = "stopped"
    logger.info(f"{SERVICE_NAME} status changed to {service_status_memory['status']}.")
    return ControlResponse(message=f"{SERVICE_NAME} stop initiated (simulated).", current_status=service_status_memory['status'])

@app.post("/start", response_model=ControlResponse, summary="Start Service (Simulated)", description="Simulates starting the service.")
async def start_service():
    global service_status_memory
    logger.info("'/start' endpoint called. Attempting to start service (simulated).")
    service_status_memory["status"] = "running"
    logger.info(f"{SERVICE_NAME} status changed to {service_status_memory['status']}.")
    return ControlResponse(message=f"{SERVICE_NAME} start initiated (simulated).", current_status=service_status_memory['status'])

@app.post("/restart", response_model=ControlResponse, summary="Restart Service (Simulated)", description="Simulates restarting the service.")
async def restart_service():
    global service_status_memory
    logger.info("'/restart' endpoint called. Simulating service restart.")

    # Simulate stop
    service_status_memory["status"] = "stopped"
    logger.info(f"{SERVICE_NAME} stopping as part of restart... Current status: {service_status_memory['status']}")

    # Simulate start
    service_status_memory["status"] = "running"
    logger.info(f"{SERVICE_NAME} starting as part of restart... Current status: {service_status_memory['status']}")

    return ControlResponse(message=f"{SERVICE_NAME} restart initiated (simulated).", current_status=service_status_memory['status'])

if __name__ == "__main__":
    import uvicorn
    # Ensure logger is available if this script is run directly
    if not logger.handlers: # Basic check if handlers are already configured
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler()])
        logger = logging.getLogger(SERVICE_NAME) # Re-initialize logger for the main block if needed

    logger.info(f"Starting {SERVICE_NAME} on http://0.0.0.0:8000")
    # Uvicorn's log_level can be set to 'warning' or 'error' to reduce console noise from uvicorn itself,
    # while our application logging (to file and console) is controlled by basicConfig.
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")