# Background Task Runner

The backend now wires a lightweight background task runner that wraps
`asyncio.create_task` with retry/backoff semantics. It lives at
`core_platform.utils.background_task_runner.BackgroundTaskRunner` and is
instantiated during app startup (`platform/backend/main.py`). Services such as
the SI sync orchestrator call `configure_task_runner(...)` so they can enqueue
work without knowing which runner implementation is active.

### Switching to Phase-6 Job Orchestration

When the full job orchestration stack is ready (Celery, RQ, etc.):

1. Replace the `BackgroundTaskRunner` instance created in `initialize_services`
   with the orchestration client and pass it into
   `initialize_si_services(..., background_runner=...)`.
2. Update `SyncOrchestrator.configure_task_runner` to accept the orchestration
   client and enqueue jobs via the real queue inside `_submit_background`.
3. Remove the lightweight runner import once all services use the orchestration
   client, keeping the same payload structure so downstream code remains
   compatible.

This keeps the interim runner fully compatible with the upcoming Phase-6 queue
infrastructure.
