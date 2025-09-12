"""Test runner for Phase 6 tests - comprehensive test suite."""

import subprocess
import sys
from pathlib import Path


def run_phase6_tests():
    """Run all Phase 6 tests."""
    test_files = [
        "test_cli_phase6.py",
        "test_cloud_export_phase6.py", 
        "test_integration_phase6.py",
        "test_golden_files_phase6.py",
        "test_missing_cli_args_phase6.py"
    ]
    
    print("🧪 Running Phase 6 Test Suite")
    print("=" * 50)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_file in test_files:
        test_path = Path(__file__).parent / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            continue
            
        print(f"\n📁 Running {test_file}...")
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_path), "-v"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file} - PASSED")
                passed_tests += 1
            else:
                print(f"❌ {test_file} - FAILED")
                print(result.stdout)
                print(result.stderr)
                failed_tests += 1
                
        except Exception as e:
            print(f"❌ {test_file} - ERROR: {e}")
            failed_tests += 1
        
        total_tests += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Phase 6 Test Results:")
    print(f"   Total test files: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("🎉 All Phase 6 tests passed!")
        return 0
    else:
        print("💥 Some Phase 6 tests failed!")
        return 1


def run_specific_phase6_test(test_name):
    """Run a specific Phase 6 test."""
    test_file = f"test_{test_name}_phase6.py"
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    print(f"🧪 Running {test_file}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_path), "-v"],
            cwd=Path(__file__).parent.parent
        )
        return result.returncode
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return 1


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        return run_specific_phase6_test(test_name)
    else:
        return run_phase6_tests()


if __name__ == "__main__":
    sys.exit(main())
