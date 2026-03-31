import subprocess

# Run docker compose logs for worker
try:
    result = subprocess.run(['docker', 'compose', 'logs', 'worker'], capture_output=True, text=True)
    logs = result.stdout
    
    # Search for the event ID fragment
    event_id_fragment = "d179"
    matches = [line for line in logs.split('\n') if event_id_fragment in line]
    
    if matches:
        print("Matches found in logs:")
        for m in matches:
            print(m)
    else:
        print(f"No logs found for event ID fragment: {event_id_fragment}")
except Exception as e:
    print(f"Error reading logs: {e}")
