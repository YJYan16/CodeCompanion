"""使用 Docker OpenJDK 镜像安全执行 Java 代码。"""
import os
import shutil
import subprocess
import tempfile
import time
from typing import Optional


def _docker_volume_path(path: str) -> str:
    """将本地路径转换为 Docker 可挂载的路径（兼容 Windows Docker Desktop）。"""
    resolved = os.path.abspath(path)
    if os.name == "nt":
        drive, rest = os.path.splitdrive(resolved)
        return f"/{drive[0].lower()}{rest.replace(os.sep, '/')}"
    return resolved


class DockerJavaExecutor:
    def __init__(
        self,
        image: str = "eclipse-temurin:17-jdk",
        timeout: int = 10,
        memory_limit: str = "128m",
        cpus: str = "0.5",
    ):
        self.image = image
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpus = cpus

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def ensure_image(self) -> Optional[str]:
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", self.image],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return None
            pull = subprocess.run(
                ["docker", "pull", self.image],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if pull.returncode != 0:
                return pull.stderr or "拉取 Docker 镜像失败"
            return None
        except FileNotFoundError:
            return "未找到 Docker，请先安装并启动 Docker Desktop"
        except subprocess.TimeoutExpired:
            return "Docker 镜像拉取超时"

    def execute(self, code: str) -> dict:
        if not self.is_available():
            return {
                "success": False,
                "error": "Docker 不可用，请安装并启动 Docker Desktop",
                "output": "",
            }

        image_error = self.ensure_image()
        if image_error:
            return {"success": False, "error": image_error, "output": ""}

        tmpdir = tempfile.mkdtemp(prefix="cc_java_")
        start = time.time()
        try:
            filepath = os.path.join(tmpdir, "Main.java")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)

            volume = _docker_volume_path(tmpdir)
            cmd = [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--memory",
                self.memory_limit,
                "--cpus",
                self.cpus,
                "-v",
                f"{volume}:/workspace",
                "-w",
                "/workspace",
                self.image,
                "sh",
                "-c",
                "javac -encoding UTF-8 Main.java && java Main",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                encoding="utf-8",
                errors="replace",
            )
            elapsed_ms = int((time.time() - start) * 1000)

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": result.stderr.strip() or "Java 执行失败",
                    "output": result.stdout,
                    "elapsed_ms": elapsed_ms,
                }

            return {
                "success": True,
                "output": result.stdout,
                "error": "",
                "elapsed_ms": elapsed_ms,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"执行超时（{self.timeout}秒）",
                "output": "",
                "elapsed_ms": int((time.time() - start) * 1000),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "output": ""}
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
