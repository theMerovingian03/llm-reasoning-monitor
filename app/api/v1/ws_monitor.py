from __future__ import annotations

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.monitor_utils.analyzer import run_monitor
from app.services.step_parser import StepParser

router = APIRouter()
step_parser = StepParser()

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
            current_step = ""
            reasoning_so_far = ""

            async for token in agent.stream(messages):

                # send token to client (live stream)
                await websocket.send_json({
                    "type": "token",
                    "content": token
                })

                # detect <think> start
                if "<think>" in token:
                    in_think = True
                    continue

                # detect </think> end
                if "</think>" in token:
                    in_think = False

                    # Flush remaining step
                    if current_step.strip():
                        step = current_step.strip()

                        analysis = await run_monitor(
                            monitor,
                            prompt,
                            reasoning_so_far,
                            step
                        )

                        await websocket.send_json({
                            "type": "analysis",
                            "step": step,
                            "data": analysis.model_dump()
                        })

                    break

                if not in_think:
                    continue

                # accumuate step
                current_step += token

                # step boundary detection
                if step_parser.detect_step_boundary(current_step):
                    raw = current_step.strip()
                    current_step = ""

                    # split into clean steps
                    steps = step_parser.split_steps(raw)

                    for step in steps:
                        reasoning_so_far += step + " "

                        analysis = await run_monitor(
                            monitor,
                            prompt,
                            reasoning_so_far,
                            step
                        )        

                        await websocket.send_json({
                            "type": "analysis",
                            "step": step,
                            "data": analysis.model_dump()
                        })

                        # interrupt early
                        if not analysis.safe:
                            await websocket.send_json({
                                "type": "interrupt",
                                "reason": analysis.reason
                            })
                            return

            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        print("Client disconnected")