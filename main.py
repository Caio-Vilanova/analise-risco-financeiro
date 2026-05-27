from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from finanalise.cli import FinanaliseCLI


if __name__ == "__main__":
    FinanaliseCLI().run()
