#!/usr/bin/env python3
"""
PokéCertify Project Management Script

This script provides an interactive CLI to:
- Run all tests (pytest)
- Initialise the environment (DB, Modal model, etc.) without running tests

Usage:
    python scripts/manage.py
"""

import subprocess
import sys

def run_tests():
    print("\nRunning all tests with pytest...\n")
    result = subprocess.run(["pytest", "tests"], check=False)
    if result.returncode == 0:
        print("\nAll tests passed!\n")
    else:
        print("\nSome tests failed. See output above.\n")
    return result.returncode

def initialise():
    print("\nInitialising PokéCertify environment...\n")
    # Example: DB init, Modal model check, etc.
    # You can expand this as needed for your stack.
    try:
        subprocess.run(["bash", "scripts/init_db.sh"], check=True)
        print("Database initialised.")
    except Exception as e:
        print(f"Database initialisation failed: {e}")
    # Modal model check (optional)
    print("Modal model weights and environment assumed ready (customise as needed).")
    print("Initialisation complete.\n")

def main():
    print("PokéCertify Project Management")
    print("=============================")
    print("Choose an option:")
    print("1. Run all tests")
    print("2. Initialise environment only")
    print("3. Exit")
    choice = input("Enter your choice [1/2/3]: ").strip()
    if choice == "1":
        run_tests()
    elif choice == "2":
        initialise()
    elif choice == "3":
        print("Exiting.")
        sys.exit(0)
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main()