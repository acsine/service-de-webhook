
import subprocess

def search_logs(event_id):
    try:
        # Get logs from worker
        result = subprocess.run(['docker', 'compose', 'logs', 'worker'], capture_output=True, text=True, check=True)
        logs = result.stdout
        
        # Filter lines with event_id
        matching_lines = [line for line in logs.split('\n') if event_id in line]
        
        if not matching_lines:
            print(f"No logs found for event_id: {event_id}")
        else:
            for line in matching_lines:
                print(line)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    search_logs("0a7d28b8-bdad-412d-80c0-12f15d1620b7")
