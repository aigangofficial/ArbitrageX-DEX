#!/usr/bin/env python3
import json
import sys
import os

# Try to import the learning loop module
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from learning_loop import LearningLoop
    
    # Try to get an instance of the learning loop
    learning_loop = LearningLoop()
    result = learning_loop.force_strategy_adaptation()
    print(str(result).lower())
except Exception as e:
    # If we can't import or use the learning loop, return failure
    print("false") 