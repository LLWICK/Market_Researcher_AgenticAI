#main.py
import sys
from pathlib import Path

# Add the current directory to the path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    from Competitor_Comparison_Agent import run_compare
else:
    from .Competitor_Comparison_Agent import run_compare

def main():
    out = run_compare()
    print(f"[Agent4] Wrote: {out}")

if __name__ == "__main__":
    main()
