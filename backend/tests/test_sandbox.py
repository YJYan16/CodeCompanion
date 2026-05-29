from unittest.mock import MagicMock, patch

from app.core.sandbox.secure_executor import SecureExecutor


def test_execute_valid_python():
    executor = SecureExecutor()
    result = executor.execute_python("print('hello')")
    assert result["success"] is True
    assert "hello" in result["output"]


def test_execute_syntax_error():
    executor = SecureExecutor()
    result = executor.execute_python("def broken(")
    assert result["success"] is False
    assert "语法错误" in result["error"] or "编译错误" in result["error"]


@patch("app.core.sandbox.docker_java_executor.subprocess.run")
@patch("app.core.sandbox.docker_java_executor.DockerJavaExecutor.is_available", return_value=True)
@patch("app.core.sandbox.docker_java_executor.DockerJavaExecutor.ensure_image", return_value=None)
def test_docker_java_execute_success(mock_image, mock_available, mock_run):
    from app.core.sandbox.docker_java_executor import DockerJavaExecutor

    mock_run.return_value = MagicMock(returncode=0, stdout="42\n", stderr="")
    executor = DockerJavaExecutor()
    result = executor.execute('public class Main { public static void main(String[] args) { System.out.println(42); } }')
    assert result["success"] is True
    assert "42" in result["output"]


@patch("app.core.sandbox.docker_java_executor.DockerJavaExecutor.is_available", return_value=False)
def test_docker_java_unavailable(mock_available):
    from app.core.sandbox.docker_java_executor import DockerJavaExecutor

    executor = DockerJavaExecutor()
    result = executor.execute("public class Main {}")
    assert result["success"] is False
    assert "Docker" in result["error"]


def test_sandbox_python_via_api(client):
    response = client.post(
        "/api/sandbox/execute",
        json={"code": "print(1+1)", "language": "python", "timeout": 5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "2" in data["output"]
