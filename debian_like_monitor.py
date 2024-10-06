import subprocess
import re
from datetime import datetime
import locale
import time
from collections import defaultdict

# Set the locale to Portuguese for date formatting
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8') #set your locale!!!

# Limit for disconnection duration in seconds
DISCONNECTION_LIMIT = 10

# Function to execute the journalctl command
def run_journalctl():
    try:
        # Run journalctl without grep
        result = subprocess.run(
            ['journalctl', '-u', 'NetworkManager', '--no-pager'],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Error executing journalctl: {e}")
        return []

# Function to analyze logs and capture events
def parse_log_entry(entry):
    # Modified to capture UNIX timestamp between brackets
    log_pattern = r'(?P<date>\w{3} \d{2} \d{2}:\d{2}:\d{2}) your_username NetworkManager.*\[([0-9.]+)\] .*NetworkManager state is now (?P<state>\w+)'
    match = re.search(log_pattern, entry)
    if match:
        try:
            # Capture the UNIX timestamp in seconds and milliseconds
            unix_timestamp = float(match.group(2))
            # Convert the timestamp to a full datetime, including the year
            log_time = datetime.fromtimestamp(unix_timestamp)
            print(f"Converted full date: {log_time}")  # For debugging
        except ValueError as e:
            print(f"Error interpreting date: {e}")
            return None, None
        state = match.group('state')
        return log_time, state
    else:
        print(f"Regex did not match the line: {entry}")  # Debugging if regex fails
    return None, None

# Function to calculate the average
def calculate_average(values):
    if values:
        return sum(values) / len(values)
    return 0

# Function to process disconnection and reconnection events
def monitor_connections():
    disconnections = []
    reconnections = []
    events = run_journalctl()

    # Filter only lines with state changes
    filtered_events = [event for event in events if 'NetworkManager state is now' in event]

    for event in filtered_events:
        log_time, state = parse_log_entry(event)
        if log_time and state:
            if state == 'DISCONNECTED':
                disconnections.append(log_time)
            elif state == 'CONNECTED_GLOBAL':
                reconnections.append(log_time)

    # Sort disconnections and reconnections chronologically
    disconnections.sort()
    reconnections.sort()

    # Process disconnections and calculate time
    disconnection_durations = []
    i = 0
    j = 0
    while i < len(disconnections) and j < len(reconnections):
        if reconnections[j] > disconnections[i]:
            diff = (reconnections[j] - disconnections[i]).total_seconds()
            disconnection_durations.append((diff, disconnections[i]))
            print(f"Disconnection time: {diff} seconds")
            if diff > DISCONNECTION_LIMIT:
                print(f"ALERT: Disconnection lasted more than {DISCONNECTION_LIMIT} seconds")
            i += 1
        j += 1

    # Summarize by month
    disconnections_by_month = summarize_by_period(disconnection_durations, lambda x: x.strftime('%Y-%m'))
    # Summarize by week
    disconnections_by_week = summarize_by_period(disconnection_durations, lambda x: x.strftime('%Y-%U'))

    # Display summary by month
    print("\n--- Disconnections by Month ---")
    for month, durations in disconnections_by_month.items():
        avg = calculate_average(durations)
        print(f"Month: {month} - Total disconnections: {len(durations)} - Average duration: {avg:.2f} seconds")

    # Display summary by week
    print("\n--- Disconnections by Week ---")
    for week, durations in disconnections_by_week.items():
        avg = calculate_average(durations)
        print(f"Week: {week} - Total disconnections: {len(durations)} - Average duration: {avg:.2f} seconds")

    print(f"\nDisconnections captured: {len(disconnection_durations)} events")
    print(f"Reconnections captured: {len(reconnections)} events")

# Function to summarize disconnections by a given period
def summarize_by_period(data, period_func):
    summarized = defaultdict(list)
    for disconnection_time, disconnection_date in data:
        period = period_func(disconnection_date)
        summarized[period].append(disconnection_time)
    return summarized

if __name__ == '__main__':
    monitor_connections()
