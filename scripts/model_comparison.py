"""Run real Llama vs Gemini comparison after both are configured."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.argv = [sys.argv[0], "compare"]
from scripts.run_experiment import *  # run_experiment compare writes clearly labelled results
