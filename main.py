from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.llm_client import LLMClient
from app.api.v1.ws_monitor import router as ws_monitor_consolidated
from app.services.model_server import ModelServerConfig, ModelServerManager
from app.core.config import (
    MONITOR_MODEL_PATH,
    MONITOR_MODEL_URL,
    TARGET_MODEL_PATH,
    TARGET_MODEL_URL,
    MAIN_PORT
)
import uvicorn
import asyncio

async def wait_for_server(client: LLMClient, name: str):
    for _ in range(10):  # retry up to 10 seconds
        if await client.health_check():
            print(f"{name} ready")
            return
        await asyncio.sleep(1)
    raise RuntimeError(f"{name} failed to start")

@asynccontextmanager
async def lifespan(app: FastAPI):

    model_manager = ModelServerManager([
        ModelServerConfig(
            name="target",
            model_path=TARGET_MODEL_PATH,
            port=8001
        ),
        ModelServerConfig(
            name="monitor",
            model_path=MONITOR_MODEL_PATH,
            port=8002
        )
    ])

    model_manager.start_all()

    app.state.target = LLMClient(TARGET_MODEL_URL)
    app.state.monitor = LLMClient(MONITOR_MODEL_URL)
    app.state.model_manager = model_manager

    await wait_for_server(app.state.target, "target")
    await wait_for_server(app.state.monitor, "monitor")

    yield

    model_manager.stop_all()
    await app.state.target.close()
    await app.state.monitor.close()

app = FastAPI(lifespan=lifespan)

app.include_router(ws_monitor_consolidated, tags=["Think block analysis"])

if __name__ == "__main__":
    uvicorn.run(app=app, host="127.0.0.1", port = MAIN_PORT)