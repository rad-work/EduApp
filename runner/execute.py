import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _write_stderr(text: str) -> None:
    if text:
        sys.stderr.write(text)


def _compile_python(source: Path, timeout: float) -> int:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(source)],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124
    _write_stderr(result.stderr or "")
    return result.returncode


def _run_python(source: Path, input_path: Path, output_path: Path, timeout: float) -> int:
    try:
        with input_path.open("r", encoding="utf-8") as in_file:
            result = subprocess.run(
                [sys.executable, str(source)],
                stdin=in_file,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        return 124
    output_path.write_text(result.stdout, encoding="utf-8")
    _write_stderr(result.stderr or "")
    return result.returncode


def _compile_gcc_cpp(source: Path, timeout: float, compiler: str) -> int:
    workdir = source.parent
    prog = workdir / "prog"
    if prog.exists():
        prog.unlink()
    cmd = [
        compiler,
        "-std=c++20" if compiler == "g++" else "-std=c17",
        "-Wall",
        "-Wextra",
        "-O2",
        "-pipe",
        "-o",
        "prog",
        source.name,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124
    _write_stderr(result.stderr or "")
    return result.returncode


def _compile_c(source: Path, timeout: float) -> int:
    return _compile_gcc_cpp(source, timeout, "gcc")


def _compile_cpp(source: Path, timeout: float) -> int:
    return _compile_gcc_cpp(source, timeout, "g++")


def _run_prog(workdir: Path, input_path: Path, output_path: Path, timeout: float) -> int:
    binary = workdir / "prog"
    try:
        with input_path.open("r", encoding="utf-8") as in_file:
            result = subprocess.run(
                [str(binary)],
                cwd=workdir,
                stdin=in_file,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        return 124
    output_path.write_text(result.stdout, encoding="utf-8")
    _write_stderr(result.stderr or "")
    return result.returncode


def _compile_java(source: Path, timeout: float) -> int:
    workdir = source.parent
    for p in workdir.glob("*.class"):
        p.unlink(missing_ok=True)
    try:
        result = subprocess.run(
            ["javac", "-encoding", "UTF-8", source.name],
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124
    _write_stderr(result.stderr or "")
    return result.returncode


def _run_java(workdir: Path, input_path: Path, output_path: Path, timeout: float) -> int:
    try:
        with input_path.open("r", encoding="utf-8") as in_file:
            result = subprocess.run(
                ["java", "-Dfile.encoding=UTF-8", "Main"],
                cwd=workdir,
                stdin=in_file,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
    except subprocess.TimeoutExpired:
        return 124
    output_path.write_text(result.stdout, encoding="utf-8")
    _write_stderr(result.stderr or "")
    return result.returncode


def _normalize_language(raw: str) -> str:
    s = raw.strip().lower().replace(" ", "")
    if s in ("c++", "cplusplus", "cxx"):
        s = "cpp"
    return s


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["compile", "run"], required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--input", required=False)
    parser.add_argument("--output", required=False)
    parser.add_argument("--timeout", type=float, required=True)
    args = parser.parse_args()

    lang = _normalize_language(args.language)
    if lang not in {"python", "c", "cpp", "java"}:
        sys.stderr.write(f"Unsupported language: {args.language}\n")
        return 2

    source = Path(args.source)

    if args.mode == "compile":
        if lang == "python":
            return _compile_python(source, args.timeout)
        if lang == "c":
            if not shutil.which("gcc"):
                sys.stderr.write("gcc not found in runner image\n")
                return 2
            return _compile_c(source, args.timeout)
        if lang == "cpp":
            if not shutil.which("g++"):
                sys.stderr.write("g++ not found in runner image\n")
                return 2
            return _compile_cpp(source, args.timeout)
        if lang == "java":
            if not shutil.which("javac"):
                sys.stderr.write("javac not found in runner image\n")
                return 2
            return _compile_java(source, args.timeout)
        return 2

    if not args.input or not args.output:
        sys.stderr.write("Input and output paths are required in run mode\n")
        return 2

    input_path = Path(args.input)
    output_path = Path(args.output)
    workdir = source.parent

    if lang == "python":
        return _run_python(source, input_path, output_path, args.timeout)
    if lang in ("c", "cpp"):
        return _run_prog(workdir, input_path, output_path, args.timeout)
    if lang == "java":
        return _run_java(workdir, input_path, output_path, args.timeout)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
