import sys
sys.path.append('../mbus')
import pytest
from mbus import *

def test_empty_init():
    foo = MBus()
