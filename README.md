# Network Connection Monitor

This script monitors network connection and disconnection events and logs the time and duration of each event. It also raises alerts if a disconnection lasts longer than 10 seconds.

## Features
- Monitors and logs disconnection events
- Alerts when disconnection exceeds 10 seconds
- Provides disconnection statistics by month and week

## Requirements
- Python 3.11 or higher

## How to Run
1. Clone this repository:
   ```bash
   git clone https://github.com/camposds/net_connection_monitor.git
2. Install required dependencies
3. Run the script: 
    ```bash
   sudo python3.11 monitor.py

4. Example output:
"Disconnection time: 3.1 seconds"
"ALERT: Disconnection lasted more than 10 seconds"

