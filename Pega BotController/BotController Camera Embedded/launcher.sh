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
        python legocam_agent.py
    ) &> legocam_agent.log  
fi
