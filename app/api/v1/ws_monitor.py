from __future__ import annotations

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.monitor_utils.analyzer import run_monitor

router = APIRouter()

@router.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)

            prompt = payload.get("prompt", "")
            if not prompt:
                await websocket.send_json({"error": "No prompt provided"})
                continue

            agent = websocket.app.state.target
            monitor = websocket.app.state.monitor

            messages = [{"role": "user", "content": prompt}]

            # THINK PARSING STATE
            in_think = False
            think_buffer = ""

            async for token in agent.stream(messages):

                # send token to client (live stream)
                await websocket.send_json({
                    "type": "token",
                    "content": token
                })

                # detect <think> start
                if "<think>" in token:
                    in_think = True

                # accumulate reasoning
                if in_think:
                    think_buffer += token

                # detect </think> end
                if "</think>" in token:
                    in_think = False

                    # RUN MONITOR HERE
                    analysis = await run_monitor(monitor, prompt, think_buffer)

                    await websocket.send_json({
                        "type": "analysis",
                        "data": analysis.model_dump()
                    })

                    # interrupt if unsafe
                    if not analysis.safe:
                        await websocket.send_json({
                            "type": "interrupt",
                            "reason": analysis.reason
                        })
                        break

            # fallback: if no closing tag but buffer exists
            if think_buffer:
                analysis = await run_monitor(monitor, prompt, think_buffer)

                await websocket.send_json({
                    "type": "analysis",
                    "data": analysis
                })

            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("Client disconnected")