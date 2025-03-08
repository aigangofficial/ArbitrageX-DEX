#!/usr/bin/env python3
import json
import sys
import os
from datetime import datetime, timedelta
import random

# Try to import the learning loop module
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from learning_loop import LearningLoop
    
    # Try to get an instance of the learning loop
    learning_loop = LearningLoop()
    performance = learning_loop.get_model_performance()
    print(json.dumps(performance))
except Exception as e:
    # If we can't import or use the learning loop, return mock data
    now = datetime.now()
    
    # Generate some mock performance data with improving trends
    def generate_metrics(base_value, improvement_rate, count=10):
        metrics = []
        for i in range(count):
            timestamp = (now - timedelta(hours=count-i)).isoformat()
            value = base_value * (1 + improvement_rate * i)
            metrics.append({"timestamp": timestamp, "value": value})
        return metrics
    
    mock_performance = {
        "profit_predictor": {
            "accuracy": generate_metrics(0.82, 0.01),
            "mae": generate_metrics(0.05, -0.02),  # Decreasing MAE is good
            "r2": generate_metrics(0.75, 0.02)
        },
        "gas_optimizer": {
            "accuracy": generate_metrics(0.88, 0.005),
            "mae": generate_metrics(0.03, -0.01),
            "r2": generate_metrics(0.81, 0.01)
        },
        "network_selector": {
            "accuracy": generate_metrics(0.91, 0.004),
            "mae": generate_metrics(0.02, -0.005),
            "r2": generate_metrics(0.85, 0.008)
        },
        "time_optimizer": {
            "accuracy": generate_metrics(0.79, 0.015),
            "mae": generate_metrics(0.06, -0.025),
            "r2": generate_metrics(0.72, 0.025)
        },
        "error": str(e)
    }
    print(json.dumps(mock_performance)) 