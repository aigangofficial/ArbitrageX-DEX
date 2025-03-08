#!/usr/bin/env python3
import json
import sys
import os
from datetime import datetime, timedelta

# Try to import the learning loop module
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from learning_loop import LearningLoop
    
    # Try to get an instance of the learning loop
    learning_loop = LearningLoop()
    stats = learning_loop.get_learning_stats()
    print(json.dumps(stats))
except Exception as e:
    # If we can't import or use the learning loop, return mock data
    mock_stats = {
        "is_running": True,
        "queue_size": 5,
        "model_update_queue_size": 12,
        "historical_results_count": 342,
        "successful_model_updates": 8,
        "failed_model_updates": 1,
        "strategy_adaptations": 3,
        "next_model_update": (datetime.now() + timedelta(minutes=15)).isoformat(),
        "next_strategy_adaptation": (datetime.now() + timedelta(hours=2)).isoformat(),
        "last_update_time": (datetime.now() - timedelta(hours=1)).isoformat(),
        "error": str(e)
    }
    print(json.dumps(mock_stats)) 