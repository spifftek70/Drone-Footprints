# runner.py
import time
import sys
import json
# while True:
#     time.sleep(1)
#     sys.stdout.flush()
#
total_steps = 100
for i in range(total_steps):
    time.sleep(0.1)  # Simulate work
    # Manually creating a progress update message as JSON
    progress_msg = json.dumps({
        "type": "progress",
        "value": (i + 1) / total_steps * 100  # Percentage completion
    })
    print(progress_msg)
    sys.stdout.flush()
