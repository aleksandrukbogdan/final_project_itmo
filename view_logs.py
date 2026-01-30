import json
import glob
import os

def view_logs():
    base_dir = r"c:\Users\aleks\vsproject\self-project\final_project_itmo\interview"
    files = glob.glob(os.path.join(base_dir, "interview_log_*.json"))
    
    if not files:
        print("No log files found.")
        return

    for file_path in files:
        print(f"\n{'='*50}")
        print(f"VIEWING: {os.path.basename(file_path)}")
        print(f"{'='*50}\n")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            participant = data.get("participant_name", "Unknown")
            print(f"Participant: {participant}")
            
            for turn in data.get("turns", []):
                tid = turn.get("turn_id")
                thoughts = turn.get("internal_thoughts", "")
                
                print(f"\n--- Turn {tid} ---")
                print(f"[Internal Thoughts]:")
                # When printing the string, \n comes out as an actual newline
                print(thoughts) 
                print("-" * 20)
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

if __name__ == "__main__":
    view_logs()
