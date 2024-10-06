import subprocess
from datetime import datetime
import re
from collections import defaultdict

# Limit for disconnections in seconds
DISCONNECT_LIMIT = 10

# Function to run PowerShell and fetch WLAN AutoConfig events
def run_powershell():
    try:
        ps_command = (
            "Get-WinEvent -LogName 'Microsoft-Windows-WLAN-AutoConfig/Operational' | "
            "Where-Object { $_.Id -in 8000, 8001, 8003, 11001, 11005 } | "
            "Format-Table TimeCreated, Id, Message -AutoSize"
        )
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error executing PowerShell: {e}")
        return []

# Function to parse the log entries and capture connection/disconnection events
def parse_log_entry(entry):
    log_pattern = r'(?P<date>\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})\s+(?P<id>\d+)\s+(?P<message>.+)'
    match = re.search(log_pattern, entry)
    if match:
        try:
            log_time = datetime.strptime(match.group('date'), '%d/%m/%Y %H:%M:%S')
            event_id = int(match.group('id'))
            message = match.group('message')
            return log_time, event_id, message
        except ValueError as e:
            print(f"Error parsing log entry: {e}")
            return None, None, None
    else:
        return None, None, None

# Function to calculate the average of a list of values
def calculate_average(values):
    if values:
        return sum(values) / len(values)
    return 0

# Function to summarize disconnections by a given period (month or week)
def summarize_by_period(data, period_func):
    summarized = defaultdict(list)
    for duration, disconnect_time in data:
        period = period_func(disconnect_time)
        summarized[period].append(duration)
    return summarized

# Function to process disconnections and reconnections
def monitor_connections():
    disconnect_times = []
    reconnect_times = []
    events = run_powershell()

    # Filter disconnection (8003) and reconnection (8001) events
    for event in events:
        log_time, event_id, message = parse_log_entry(event)
        if log_time and event_id:
            if event_id == 8003:  # Disconnection event
                disconnect_times.append(log_time)
            elif event_id == 8001:  # Reconnection event
                reconnect_times.append(log_time)

    # Sort disconnections and reconnections chronologically
    disconnect_times.sort()
    reconnect_times.sort()

    # Process disconnections and calculate time duration
    disconnect_durations = []
    i = 0
    j = 0
    while i < len(disconnect_times) and j < len(reconnect_times):
        if reconnect_times[j] > disconnect_times[i]:
            duration = (reconnect_times[j] - disconnect_times[i]).total_seconds()
            disconnect_durations.append((duration, disconnect_times[i]))
            print(f"Disconnect duration: {duration} seconds")
            if duration > DISCONNECT_LIMIT:
                print(f"ALERT: Disconnect lasted more than {DISCONNECT_LIMIT} seconds")
            i += 1
        j += 1

    # Summarize by month
    disconnects_by_month = summarize_by_period(disconnect_durations, lambda x: x.strftime('%Y-%m'))
    # Summarize by week
    disconnects_by_week = summarize_by_period(disconnect_durations, lambda x: x.strftime('%Y-%U'))

    # Display summary by month
    print("\n--- Disconnects by Month ---")
    for month, durations in disconnects_by_month.items():
        average_duration = calculate_average(durations)
        print(f"Month: {month} - Total disconnects: {len(durations)} - Average duration: {average_duration:.2f} seconds")

    # Display summary by week
    print("\n--- Disconnects by Week ---")
    for week, durations in disconnects_by_week.items():
        average_duration = calculate_average(durations)
        print(f"Week: {week} - Total disconnects: {len(durations)} - Average duration: {average_duration:.2f} seconds")

    print(f"\nTotal disconnects captured: {len(disconnect_durations)} events")
    print(f"Total reconnects captured: {len(reconnect_times)} events")

if __name__ == "__main__":
    monitor_connections()
