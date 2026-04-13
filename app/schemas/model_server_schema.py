from dataclasses import dataclass

@dataclass
class ModelServerConfig:
    name: str
    model_path: str
    port: int
    n_ctx: int = 2048
    n_threads: int = 8
    n_gpu_layers: int = 5