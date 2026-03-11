import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Import test class
from test_targets import TestLoadTargets

# Instantiate and run tests manually
test_instance = TestLoadTargets()
test_methods = [m for m in dir(test_instance) if m.startswith("test_")]

failed = 0
passed = 0

for test_name in test_methods:
    try:
        method = getattr(test_instance, test_name)
        method()
        print(f"PASSED: {test_name}")
        passed += 1
    except AssertionError as e:
        print(f"FAILED: {test_name} - {e}")
        failed += 1
    except Exception as e:
        print(f"ERROR: {test_name} - {e}")
        failed += 1

print(f"
{passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
