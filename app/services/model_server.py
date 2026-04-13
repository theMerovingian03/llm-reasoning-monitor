import sys
import subprocess
import time
import logging
from app.schemas.model_server_schema import ModelServerConfig

logger = logging.getLogger(__name__)

class ModelServerManager:
    """Manages multiple LLM model servers using subprocess."""

    def __init__(self, configs: list[ModelServerConfig]) -> None:
        """Initialize with a list of model server configurations."""
        self.configs = configs
        self.processes: dict[str, subprocess.Popen] = {}

    # Start all models
    def start_all(self):
        """Start all configured model servers."""
        try:
            for config in self.configs:
                self._start_model(config)
            # Buffer time for server
            time.sleep(3)

        except Exception as e:
            logger.error(f"Failed to start model servers: {e}")
            # cleanup already started processes
            self.stop_all()
            raise

    def _start_model(self, config: ModelServerConfig):
        """Start a single model server if not already running."""
        if config.name in self.processes:
            logger.warning(f"{config.name} already running")
            return
        
        logger.info(f"Starting model: {config.name}")

        cmd = [
            sys.executable,
            "-m",
            "llama_cpp.server",
            "--model", config.model_path,
            "--port", str(config.port),
            "--n_ctx", str(config.n_ctx),
            "--n_threads", str(config.n_threads),
            "--n_gpu_layers", str(config.n_gpu_layers)
        ]

        process = subprocess.Popen(
            cmd,
            stdout=None,
            stderr=None
        )

        # check immediate failure
        time.sleep(1)
        if process.poll() is not None:
            raise RuntimeError(f"Model {config.name} failed to start")

        self.processes[config.name] = process

    def stop_all(self):
        """Stop all running model servers."""
        for name, process in self.processes.items():
            logger.info(f"Stopping model: {name}")
            process.terminate()
            process.wait(timeout=5)

        self.processes.clear()

    # health check
    def is_running(self, name: str) -> bool:
        """Check if a specific model server is running."""
        process = self.processes.get(name)
        if not process:
            return False
        return process.poll() is None