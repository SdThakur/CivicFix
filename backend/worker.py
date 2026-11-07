"""CivicFix ARQ Worker entrypoint (Scale Kit Forwarder)."""

from app.worker import WorkerSettings, process_report_job, metrics, structured_log

if __name__ == "__main__":
    from arq import run_worker
    run_worker(WorkerSettings)
