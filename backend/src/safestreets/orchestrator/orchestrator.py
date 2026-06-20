"""Fetch.ai uAgent wrapper.

For the demo, the HTTP API drives the pipeline directly via `dispatch.run_pipeline`.
This uAgent is the Fetch.ai-track surface: it receives AnalyzeRequest messages and
coordinates the same pipeline through the agent protocol. Keep both paths thin so they
share `dispatch` and `coordinator` logic.
"""
from __future__ import annotations

from uagents import Agent, Context

from safestreets.config import get_settings
from safestreets.orchestrator.messages import AnalyzeAck, AnalyzeRequest

settings = get_settings()

orchestrator = Agent(name="safestreets-orchestrator", seed=settings.orchestrator_seed)


@orchestrator.on_message(model=AnalyzeRequest, replies=AnalyzeAck)
async def handle_analyze(ctx: Context, sender: str, msg: AnalyzeRequest) -> None:
    ctx.logger.info(f"analyze request for {msg.address}")
    # TODO: kick off the pipeline (reuse coordinator.analyze) and reply with a job id.
    await ctx.send(sender, AnalyzeAck(job_id=f"{msg.lat},{msg.lng}"))


if __name__ == "__main__":
    orchestrator.run()
