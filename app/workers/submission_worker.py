import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
import shutil

import docker
from docker.errors import DockerException, ImageNotFound
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Submission, SubmissionResult, SubmissionStatus, TestCase, Verdict


def _ensure_runner_image(client: docker.DockerClient) -> None:
    try:
        client.images.get(settings.runner_image)
    except ImageNotFound:
        client.images.build(path="runner", tag=settings.runner_image)


def _run_runner(
    client: docker.DockerClient,
    workdir: Path,
    command: list[str],
    timeout_sec: int,
) -> tuple[int, str, float]:
    container = client.containers.run(
        settings.runner_image,
        command=command,
        network_disabled=True,
        detach=True,
        mem_limit=f"{settings.runner_memory_limit_mb}m",
        nano_cpus=int(settings.runner_cpu_limit * 1_000_000_000),
        volumes={str(workdir): {"bind": "/work", "mode": "rw"}},
        working_dir="/work",
        user="10001:10001",
    )
    started = time.monotonic()
    try:
        result = container.wait(timeout=timeout_sec + 1)
        exit_code = int(result.get("StatusCode", 1))
    except Exception:
        container.kill()
        exit_code = 124
    elapsed_ms = (time.monotonic() - started) * 1000
    stderr = container.logs(stderr=True, stdout=False).decode("utf-8", errors="replace")
    container.remove(force=True)
    return exit_code, stderr, elapsed_ms


def _verdict_from_exit(exit_code: int) -> Verdict:
    if exit_code == 124:
        return Verdict.TIME_LIMIT_EXCEEDED
    if exit_code == 137:
        return Verdict.MEMORY_LIMIT_EXCEEDED
    if exit_code != 0:
        return Verdict.RUNTIME_ERROR
    return Verdict.ACCEPTED


def process_submission_job(submission_id: int) -> None:
    db = SessionLocal()
    try:
        submission = db.get(Submission, submission_id)
        if not submission:
            return

        submission.status = SubmissionStatus.RUNNING
        db.commit()

        client = docker.from_env()
        _ensure_runner_image(client)

        tests = db.scalars(
            select(TestCase).where(TestCase.problem_id == submission.problem_id).order_by(TestCase.order_index, TestCase.id)
        ).all()
        if not tests:
            db.add(
                SubmissionResult(
                    submission_id=submission.id,
                    test_case_id=None,
                    verdict=Verdict.RUNTIME_ERROR,
                    message="No test cases configured for problem",
                )
            )
            submission.status = SubmissionStatus.COMPLETED
            submission.finished_at = datetime.now(UTC)
            db.commit()
            return

        jobs_dir = Path(settings.project_root) / ".runner_jobs"
        jobs_dir.mkdir(parents=True, exist_ok=True)
        tmp = tempfile.mkdtemp(prefix=f"submission_{submission.id}_", dir=jobs_dir)
        workdir = Path(tmp)
        workdir.chmod(0o777)
        try:
            source_path = workdir / "main.py"
            source_path.write_text(submission.source_code, encoding="utf-8")
            source_path.chmod(0o666)

            compile_code, compile_stderr, _ = _run_runner(
                client,
                workdir,
                [
                    "--mode",
                    "compile",
                    "--language",
                    submission.language,
                    "--source",
                    "/work/main.py",
                    "--timeout",
                    str(settings.runner_timeout_sec),
                ],
                settings.runner_timeout_sec,
            )
            if compile_code != 0:
                db.add(
                    SubmissionResult(
                        submission_id=submission.id,
                        test_case_id=None,
                        verdict=Verdict.COMPILATION_ERROR,
                        message=compile_stderr or "Compilation failed",
                    )
                )
                submission.status = SubmissionStatus.COMPLETED
                submission.finished_at = datetime.now(UTC)
                db.commit()
                return

            final_verdict = Verdict.ACCEPTED
            for test in tests:
                input_path = workdir / "input.txt"
                output_path = workdir / "output.txt"
                input_path.write_text(test.input_data, encoding="utf-8")
                input_path.chmod(0o666)
                if output_path.exists():
                    output_path.unlink()

                exit_code, stderr, elapsed_ms = _run_runner(
                    client,
                    workdir,
                    [
                        "--mode",
                        "run",
                        "--language",
                        submission.language,
                        "--source",
                        "/work/main.py",
                        "--input",
                        "/work/input.txt",
                        "--output",
                        "/work/output.txt",
                        "--timeout",
                        str(settings.runner_timeout_sec),
                    ],
                    settings.runner_timeout_sec,
                )
                verdict = _verdict_from_exit(exit_code)
                message = stderr.strip() if stderr else None

                actual_output = ""
                if output_path.exists():
                    actual_output = output_path.read_text(encoding="utf-8")
                expected = test.expected_output.strip()
                actual = actual_output.strip()
                if verdict == Verdict.ACCEPTED and actual != expected:
                    verdict = Verdict.WRONG_ANSWER
                    message = "Output mismatch"

                db.add(
                    SubmissionResult(
                        submission_id=submission.id,
                        test_case_id=test.id,
                        verdict=verdict,
                        execution_time_ms=int(elapsed_ms),
                        message=message,
                    )
                )
                if verdict != Verdict.ACCEPTED and final_verdict == Verdict.ACCEPTED:
                    final_verdict = verdict

            if final_verdict == Verdict.ACCEPTED:
                db.add(
                    SubmissionResult(
                        submission_id=submission.id,
                        test_case_id=None,
                        verdict=Verdict.ACCEPTED,
                        message="All tests passed",
                    )
                )
            submission.status = SubmissionStatus.COMPLETED
            submission.finished_at = datetime.now(UTC)
            db.commit()
        finally:
            shutil.rmtree(workdir, ignore_errors=True)
    except DockerException:
        submission = db.get(Submission, submission_id)
        if submission:
            submission.status = SubmissionStatus.FAILED
            submission.finished_at = datetime.now(UTC)
            db.add(
                SubmissionResult(
                    submission_id=submission.id,
                    test_case_id=None,
                    verdict=Verdict.SYSTEM_ERROR,
                    message="Docker runner unavailable",
                )
            )
            db.commit()
    except Exception:
        submission = db.get(Submission, submission_id)
        if submission:
            submission.status = SubmissionStatus.FAILED
            submission.finished_at = datetime.now(UTC)
            db.commit()
        raise
    finally:
        db.close()
