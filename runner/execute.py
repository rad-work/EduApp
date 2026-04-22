import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["compile", "run"], required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--input", required=False)
    parser.add_argument("--output", required=False)
    parser.add_argument("--timeout", type=float, required=True)
    args = parser.parse_args()

    source = Path(args.source)
    if args.language != "python":
        sys.stderr.write(f"Unsupported language: {args.language}\n")
        return 2

    if args.mode == "compile":
        try:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(source)],
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )
            if result.stderr:
                sys.stderr.write(result.stderr)
            return result.returncode
        except subprocess.TimeoutExpired:
            return 124

    if not args.input or not args.output:
        sys.stderr.write("Input and output paths are required in run mode\n")
        return 2

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        with input_path.open("r", encoding="utf-8") as in_file:
            result = subprocess.run(
                [sys.executable, str(source)],
                stdin=in_file,
                capture_output=True,
                text=True,
                timeout=args.timeout,
            )
    except subprocess.TimeoutExpired:
        return 124

    output_path.write_text(result.stdout, encoding="utf-8")
    if result.stderr:
        sys.stderr.write(result.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
