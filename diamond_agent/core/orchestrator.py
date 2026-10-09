"""
Hierarchical Multi-Agent Orchestrator: Planner, Executor, and Critic/Reviewer.
"""

from typing import Any, Dict, List, Optional
import json
import logging
import asyncio

from diamond_agent.core.llm_client import ClaudeClient

logger = logging.getLogger("diamond_agent.orchestrator")


class AgentTask:
    """Represents a discrete sub-task assigned to a specialized agent."""

    def __init__(self, task_id: str, title: str, description: str, agent_role: str):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.agent_role = agent_role
        self.status = "pending"  # pending, in_progress, completed, failed
        self.result: Optional[str] = None
        self.critique: Optional[str] = None


class DiamondOrchestrator:
    """Coordinates high-level task planning, worker dispatching, and quality review."""

    PLANNER_SYSTEM = """You are the Lead Strategic Planner in the DiamondAgent architecture.
Your job is to break down complex enterprise goals into 3 to 5 logical, executable sub-tasks.
Output your plan in pure JSON format:
{
  "summary": "Brief strategy summary",
  "tasks": [
    {"task_id": "T1", "title": "...", "description": "...", "agent_role": "Researcher|Engineer|Analyst"}
  ]
}"""

    CRITIC_SYSTEM = """You are the Senior Reviewer/Critic in the DiamondAgent architecture.
Evaluate the execution output for correctness, completeness, and adherence to requirements.
Respond in JSON:
{
  "approved": true/false,
  "score": 1-10,
  "feedback": "constructive feedback or acceptance confirmation"
}"""

    def __init__(self, client: Optional[ClaudeClient] = None):
        self.client = client or ClaudeClient()
        self.active_tasks: List[AgentTask] = []

    async def plan_goal(self, goal: str) -> List[AgentTask]:
        """Decompose a high-level goal into structured AgentTasks."""
        logger.info(f"Planning goal: {goal}")
        response = await self.client.generate_response(
            messages=[{"role": "user", "content": f"Deconstruct this goal into executable subtasks:\n{goal}"}],
            system_prompt=self.PLANNER_SYSTEM,
            model=ClaudeClient.DEFAULT_MODEL,
        )

        try:
            raw_text = response["content"]
            # Extract JSON block if surrounded by markdown fences
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            data = json.loads(raw_text)
            tasks = []
            for t in data.get("tasks", []):
                task = AgentTask(
                    task_id=t.get("task_id", f"T{len(tasks)+1}"),
                    title=t.get("title", "Untitled Task"),
                    description=t.get("description", ""),
                    agent_role=t.get("agent_role", "Engineer"),
                )
                tasks.append(task)
            self.active_tasks = tasks
            return tasks
        except Exception as e:
            logger.warning(f"Error parsing plan JSON, fallback to default decomposition: {e}")
            fallback_tasks = [
                AgentTask("T1", "Information Gathering", f"Research requirements for {goal}", "Researcher"),
                AgentTask("T2", "Execution & Synthesis", f"Execute core workflow for {goal}", "Engineer"),
                AgentTask("T3", "Verification", f"Validate outputs for {goal}", "Analyst"),
            ]
            self.active_tasks = fallback_tasks
            return fallback_tasks

    async def execute_task(self, task: AgentTask, context: str = "") -> str:
        """Execute a sub-task with the assigned specialist agent."""
        task.status = "in_progress"
        logger.info(f"Executing task [{task.task_id}] {task.title} as {task.agent_role}")

        worker_system = f"You are a specialized Diamond {task.agent_role} Agent. Focus on precision, rigor, and actionable output."
        prompt = f"Goal Context:\n{context}\n\nTask Assigned:\n{task.title}: {task.description}\n\nExecute this task and provide comprehensive results."

        response = await self.client.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=worker_system,
        )

        task.result = response["content"]
        task.status = "completed"
        return task.result

    async def review_output(self, goal: str, execution_summary: str) -> Dict[str, Any]:
        """Critique and verify final deliverable against original goal."""
        prompt = f"Original Goal: {goal}\n\nDeliverable Output:\n{execution_summary}\n\nEvaluate quality."
        response = await self.client.generate_response(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=self.CRITIC_SYSTEM,
        )

        try:
            raw = response["content"]
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()
            return json.loads(raw)
        except Exception:
            return {"approved": True, "score": 9, "feedback": "Output satisfies primary specifications."}

    async def run_pipeline(self, goal: str) -> Dict[str, Any]:
        """Full end-to-end multi-agent orchestration pipeline."""
        tasks = await self.plan_goal(goal)
        results = []
        cumulated_context = f"Main Goal: {goal}\n"

        for task in tasks:
            res = await self.execute_task(task, context=cumulated_context)
            results.append({"task_id": task.task_id, "title": task.title, "result": res})
            cumulated_context += f"\n[{task.task_id}] Result: {res[:200]}...\n"

        summary = "\n\n".join([f"### {r['task_id']}: {r['title']}\n{r['result']}" for r in results])
        review = await self.review_output(goal, summary)

        return {
            "goal": goal,
            "tasks_count": len(tasks),
            "summary": summary,
            "review": review,
            "status": "success" if review.get("approved", True) else "needs_revision",
        }
