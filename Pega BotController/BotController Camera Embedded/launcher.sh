#!/bin/sh
# launcher.sh

#!/bin/bash
SERVICE="python"
if pgrep -x "$SERVICE" >/dev/null
then
    echo "$SERVICE is running"
    pgrep -x "$SERVICE"
else
    echo "$SERVICE stopped"
    (
        echo Starting $(date)
        python camera_agent.py
    ) &> camera_agent.log  
fi
