"""
MediSafe AI - Automated Test Suite Runner
Executes database, interaction engine, and ML model test suites.
"""

import unittest
import sys
import os

# Set root directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_database import TestDatabase
from tests.test_interactions import TestInteractions
from tests.test_models import TestModels

def run_all_tests():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    suite.addTests(loader.loadTestsFromTestCase(TestInteractions))
    suite.addTests(loader.loadTestsFromTestCase(TestModels))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        print("\n[SUCCESS] ALL MEDISAFE AI SYSTEM TESTS PASSED SUCCESSFULLY!")
        return 0
    else:
        print("\n[FAILED] SOME TESTS FAILED. PLEASE REVIEW LOGS.")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
