import sys
import os
import pytest

def main():
    # Configure stdout/stderr encoding to prevent potential Unicode errors
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

    tests_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(tests_dir)
    
    # Inject project paths to sys.path
    sys.path.insert(0, project_root)
    sys.path.insert(0, tests_dir)

    print("=" * 60)
    print("Java MVC Educational Simulation E2E Test Suite - Runner")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Tests directory: {tests_dir}")
    print("-" * 60)

    # Target the new E2E test file specifically
    target_test_file = os.path.join(tests_dir, "test_mvc_flow.py")
    
    # Setup pytest arguments (verbose, show local variables on crash)
    pytest_args = [
        "-v",
        target_test_file,
    ]
    
    # Invoke pytest programmatically
    exit_code = pytest.main(pytest_args)
    
    print("=" * 60)
    print("TEST RUNNER SUMMARY")
    print("=" * 60)
    if exit_code == 0:
        print("RESULT: PASS")
        sys.exit(0)
    else:
        print("RESULT: FAIL")
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
