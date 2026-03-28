"""Entry point for the PowerForcaster pipeline (skeleton)."""
from pathlib import Path

def main():
    project_root = Path(__file__).parent
    print(f"Project root: {project_root}")
    print("This is a scaffold. Implement data fetch, feature build, and models in src/.")

if __name__ == "__main__":
    main()
