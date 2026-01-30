import json
import re
import glob
import os

def clean_internal_thoughts(thoughts_str):
    """
    Parses the internal_thoughts string and reformats it to ensure 
    each agent's thought is on a new line.
    
    Expected input format resembles:
    "[Agent1]: thought1\n[Agent2]: thought2..."
    
    Output format:
    "[Agent1]: thought1\n[Agent2]: thought2\n..."
    """
    if not thoughts_str:
        return thoughts_str
        
    # Pattern to find [AgentName]: content
    # We look for [Name]: followed by content until the next [Name]: or end of string
    # The lookahead (?=\n\[|$) works if they are already separated by newlines, 
    # but to be robust against missing newlines, we can use (?=\[.*?\]:|$) 
    # provided that brackets aren't used commonly inside the thought content.
    # However, strict agent names usually verify `[Name]:`.
    
    # Let's try to split by the agent pattern
    # Pattern: start of line or newline followed by [Name]:
    
    # First, let's normalize newlines just in case
    thoughts_str = thoughts_str.replace('\r\n', '\n')
    
    # We will simply look for all occurrences of the pattern and reconstruction
    # Regex: (\[[^\]]+\]:\s.*?)
    # We need to capture the content until the next tag.
    
    pattern = re.compile(r'(\[[^\]]+\]:\s.*?)(?=(\n\[[^\]]+\]:|$))', re.DOTALL)
    
    matches = pattern.findall(thoughts_str)
    
    # matches will be a list of tuples due to the lookahead group? 
    # No, findall with groups returns tuples.
    # Group 1 is the main content. Group 2 is the lookahead (which is zero-width assertion in some engines but here it captures).
    # Wait, (?=...) is non-capturing lookahead.
    # But `(\n\[[^\]]+\]:|$)` is a capturing group inside the lookahead? No, lookaheads are atomic assertions usually non-capturing unless groups inside.
    
    # Let's refine the regex.
    # We want to match `[Agent]: <text>`
    # where <text> goes until the next `[`.
    
    # Robust approach:
    # 1. Split string by `\[(.*?)\]:`
    # 2. Reconstruct.
    
    # Using re.split to keep delimiters
    parts = re.split(r'(\[[^\]]+\]:)', thoughts_str)
    
    # parts[0] might be empty or preamble (ignore if empty/whitespace)
    # parts[1] = "[Agent1]:"
    # parts[2] = " thought content "
    # parts[3] = "[Agent2]:"
    # parts[4] = " thought content "
    
    new_thoughts = []
    
    current_agent = None
    
    for part in parts:
        if not part.strip():
            continue
            
        if re.match(r'\[[^\]]+\]:', part):
            current_agent = part.strip()
        else:
            if current_agent:
                thought = part.strip()
                new_thoughts.append(f"{current_agent} {thought}")
                current_agent = None
    
    # Join with newlines and add a trailing newline
    result = "\n".join(new_thoughts) + "\n"
    return result

def process_files():
    # Find all interview_log_*.json files
    # Only targeting the one file mentioned or all matching the pattern?
    # User said "preobrazuyut agentov v moem json", implies specific file or pattern. 
    # "my json" -> interview_log_1.json
    # But let's support all conforming to pattern.
    
    base_dir = r"c:\Users\aleks\vsproject\self-project\final_project_itmo\interview"
    files = glob.glob(os.path.join(base_dir, "interview_log_*.json"))
    
    print(f"Found {len(files)} files to process.")
    
    for file_path in files:
        print(f"Processing {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            if "turns" in data:
                for turn in data["turns"]:
                    if "internal_thoughts" in turn:
                        original = turn["internal_thoughts"]
                        formatted = clean_internal_thoughts(original)
                        if original != formatted:
                            turn["internal_thoughts"] = formatted
                            modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"Updated {file_path}")
            else:
                print(f"No changes needed for {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    process_files()
