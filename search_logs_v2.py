
import subprocess

def search_logs(pattern):
    try:
        # Get logs from worker
        result = subprocess.run(['docker', 'compose', 'logs', 'worker'], capture_output=True, text=True, check=True)
        logs = result.stdout
        
        # Filter lines with pattern
        matching_lines = [line for line in logs.split('\n') if pattern in line]
        
        if not matching_lines:
            print(f"No logs found for pattern: {pattern}")
        else:
            for line in matching_lines:
                print(line)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_logs("event.no_subscribers")
    # Also search for the specific idempotency key if possible, but events are enqueued by ID
