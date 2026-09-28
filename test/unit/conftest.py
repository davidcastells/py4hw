# -*- coding: utf-8 -*-
"""
Created on Mon Sep 28 18:32:33 2026

@author: dcr
"""

import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--deep_random",
        action="store_true",
        default=False,
        help="Run full / extended iteration tests"
    )
    
    
@pytest.fixture
def is_deep_random(request):
    """Fixture returning iteration count based on whether --full was passed."""
    if request.config.getoption("--deep_random"):
        return True  # High iterations for individual runs
    return False   #