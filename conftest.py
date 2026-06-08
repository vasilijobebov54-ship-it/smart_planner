"""Делает корень проекта импортируемым для тестов."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
