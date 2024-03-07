import os
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


class DockerUnavailable(RuntimeError):
    pass


@dataclass
class CommandEvidence:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    container_name: str
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    def to_dict(self):
        return asdict(self)


class DockerRunner:
    def __init__(
        self,
        image: str = "swe-repair-pytest:3.12",
        timeout_seconds: float = 60,
        docker_binary: str = "docker",
    ):
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.docker_binary = docker_binary

    def ensure_image(self) -> None:
        inspect = subprocess.run(
            [self.docker_binary, "image", "inspect", self.image], capture_output=True, text=True
        )
        if inspect.returncode == 0:
            return
        dockerfile = Path(__file__).resolve().parents[2] / "docker" / "Dockerfile"
        build = subprocess.run(
            [
                self.docker_binary,
                "build",
                "--tag",
                self.image,
                "--file",
                str(dockerfile),
                str(dockerfile.parent),
            ],
            capture_output=True,
            text=True,
        )
        if build.returncode != 0:
            raise DockerUnavailable(f"Cannot build {self.image}: {build.stderr}{build.stdout}")

    def run_pytest(self, repo: Path) -> CommandEvidence:
        return self._run(repo, ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"])

    def run_probe(self, repo: Path, probe: str) -> CommandEvidence:
        return self._run(repo, ["python", "-c", probe])

    def _run(self, repo: Path, command: list[str]) -> CommandEvidence:
        self.ensure_image()
        name = f"swe-repair-{uuid.uuid4().hex}"
        docker_command = [
            self.docker_binary,
            "run",
            "--rm",
            "--name",
            name,
            "--network",
            "none",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--tmpfs",
            "/tmp:rw,nosuid,size=64m",
            "--volume",
            f"{repo.resolve()}:/workspace",
            "--workdir",
            "/workspace",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            self.image,
            *command,
        ]
        started = time.perf_counter()
        timed_out = False
        try:
            completed = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            returncode, stdout, stderr = (
                completed.returncode,
                completed.stdout,
                completed.stderr,
            )
        except subprocess.TimeoutExpired as error:
            timed_out = True
            returncode = 124
            stdout = error.stdout or ""
            stderr = (error.stderr or "") + f"\nTimed out after {self.timeout_seconds}s"
            if isinstance(stdout, bytes):
                stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes):
                stderr = stderr.decode(errors="replace")
            subprocess.run(
                [self.docker_binary, "rm", "--force", name], capture_output=True, text=True
            )
        duration = time.perf_counter() - started
        evidence = CommandEvidence(
            docker_command, returncode, stdout, stderr, duration, name, timed_out
        )
        if returncode in {125, 126, 127}:
            raise DockerUnavailable(f"Docker could not execute the workload: {stderr}{stdout}")
        return evidence
