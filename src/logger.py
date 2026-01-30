import json
import os
from config import BASE_DIR
from datetime import datetime
from typing import List, Dict, Any

class InterviewLogger:
    def __init__(self, filename: str = None):
        if filename is None:
            self.filename = str(BASE_DIR / "interview" / "interview_log.json")
        else:
            self.filename = filename
        self.session_data = {
            "participant_name": "Unknown",
            "turns": [],
            "final_feedback": ""
        }
        self.turn_count = 0

    def start_session(self, participant_name: str):
        self.session_data["participant_name"] = participant_name
        self.session_data["start_time"] = datetime.now().isoformat()

    def log_turn(self, user_message: str, internal_thoughts: str, agent_message: str):
        self.turn_count += 1
        turn_entry = {
            "turn_id": self.turn_count,
            "agent_visible_message": agent_message,
            "user_message": user_message,
            "internal_thoughts": internal_thoughts
        }
        self.session_data["turns"].append(turn_entry)
        self._save()

    def log_feedback(self, feedback: Any):
        if hasattr(feedback, "model_dump"):
            self.session_data["final_feedback"] = feedback.model_dump()
        elif hasattr(feedback, "dict"):
            self.session_data["final_feedback"] = feedback.dict()
        else:
            self.session_data["final_feedback"] = str(feedback)
        self._save()

    def _save(self):
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving log: {e}")
