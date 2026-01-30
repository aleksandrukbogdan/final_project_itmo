from agents import (
    AgentManager, FactCheckerAgent, PsychologistAgent, MentorAgent, 
    InterviewerAgent, DecisionMakerAgent, JudgeAgent, SummarizerAgent
)
from logger import InterviewLogger
from config import BASE_DIR
import json

def run_scenario(scenario_name: str, candidate_name: str, inputs: list):
    print(f"\n=== Running Scenario (v3 - Structured): {scenario_name} ===")
    
    logger = InterviewLogger(filename=str(BASE_DIR / "interview" / f"scenario_v3_{scenario_name}.json"))
    manager = AgentManager()
    
    # Register V2/V3 Agents
    manager.register_agent("FactChecker", FactCheckerAgent)
    manager.register_agent("Psychologist", PsychologistAgent)
    manager.register_agent("Mentor", MentorAgent)
    manager.register_agent("Interviewer", InterviewerAgent)
    manager.register_agent("DecisionMaker", DecisionMakerAgent)
    manager.register_agent("Judge", JudgeAgent)
    manager.register_agent("Summarizer", SummarizerAgent)
    
    fact_checker = manager.get_agent("FactChecker")
    psychologist = manager.get_agent("Psychologist")
    mentor = manager.get_agent("Mentor")
    interviewer = manager.get_agent("Interviewer")
    decision_maker = manager.get_agent("DecisionMaker")
    judge = manager.get_agent("Judge")
    summarizer = manager.get_agent("Summarizer")
    
    logger.start_session(candidate_name)
    history = []
    # We maintain a separate full text log for the Decision Maker, 
    # as it might need the full context even if we summarize for other agents.
    # However, for huge contexts, Decision Maker might also need a summarized version.
    # For now, we keep full log text, assuming it fits in context (or DM uses RAG).
    full_log_text = ""
    summary_so_far = ""
    
    print("System started.")
    
    for user_input in inputs:
        print(f"\n{candidate_name}: {user_input}")
        
        # Memory Management: Summarize if history gets too long (e.g., > 6 turns)
        # 6 turns = 3 user + 3 system.
        MEMORY_THRESHOLD = 6
        if len(history) > MEMORY_THRESHOLD:
            print("\n[System]: Consolidating Memory...")
            summary_obj = summarizer.run({"history": history})
            summary_so_far = summary_obj.summary
            # Be careful: we want to keep RECENT history for flow, but summarize OLD history.
            # Strategy: Keep last 2 turns (4 messages), summarize the rest.
            # For simplicity here: We just store the summary in a separate variable 
            # and maybe prepend it to the history sent to agents?
            # Or we physically truncate self.history.
            # Let's truncate: Keep last 2 turns, replace older with a system message "Summary: ..."
            
            recent_history = history[-2:]
            history = [{"role": "System", "content": f"Previous conversation summary: {summary_so_far}"}] + recent_history
            print(f"[Summarizer]: {summary_so_far}")

        history.append({"role": "Candidate", "content": user_input})
        full_log_text += f"\nCandidate: {user_input}"
        
        # 1. Parallel Analysis
        fact_report = fact_checker.run({"user_message": user_input})
        psych_report = psychologist.run({"user_message": user_input})
        
        # fact_report and psych_report are Pydantic models.
        print(f"[Fact-Checker]: {fact_report.verdict} | {fact_report.evidence}")
        print(f"[Psychologist]: {psych_report.emotional_state} | {psych_report.communication_style}")
        
        # 2. Mentor Strategy
        mentor_strategy = mentor.run({
            "history": history,
            "fact_check": fact_report.model_dump_json(),
            "psych_profile": psych_report.model_dump_json()
        })
        print(f"[Mentor]: {mentor_strategy.strategy} -> {mentor_strategy.instruction} (Tone: {mentor_strategy.tone})")
        
        # 3. Interviewer Response Generation & Judge Loop
        approved = False
        attempts = 0
        MAX_RETRIES = 2
        response_text = ""
        
        current_instruction = mentor_strategy.instruction
        current_tone = mentor_strategy.tone
        
        while not approved and attempts < MAX_RETRIES:
            attempts += 1
            response_text = interviewer.run({
                "history": history,
                "instruction": current_instruction,
                "tone": current_tone
            })
            
            # Judge Check
            verdict = judge.run({
                "history": history,
                "instruction": current_instruction,
                "generated_response": response_text
            })
            
            if verdict.approved:
                approved = True
                print(f"[Judge]: Approved (Score: {verdict.score})")
            else:
                print(f"[Judge]: Rejected. Feedback: {verdict.feedback}")
                # Refine instruction for retry
                current_instruction = f"{mentor_strategy.instruction} (CRITICAL FEEDBACK: {verdict.feedback})"
        
        if not approved:
            print("[System]: Max retries reached. Using last response.")
        
        history.append({"role": "Interviewer", "content": response_text})
        full_log_text += f"\nInterviewer: {response_text}"
        
        # Logging
        combined_thoughts = (
            f"[Fact-Checker] {fact_report.model_dump_json()} | "
            f"[Psychologist] {psych_report.model_dump_json()} | "
            f"[Mentor] {mentor_strategy.model_dump_json()}"
        )
        logger.log_turn(user_input, combined_thoughts, response_text)
        print(f"[Interviewer]: {response_text}")

    # 4. Final Decision
    final_decision = decision_maker.run({"full_log": full_log_text})
    
    # Save formatted feedback
    logger.log_feedback(final_decision.model_dump_json(indent=2))
    
    print(f"\nFinal Decision:\n{final_decision.model_dump_json(indent=2)}")
    print(f"Scenario {scenario_name} completed. Log saved.")

if __name__ == "__main__":
    # 1. Middle Developer Scenario
    inputs_middle = [
        "Привет. Меня зовут Алекс, я Middle Python разработчик. Работал 2 года с Django и Postgres.",
        "Generators save memory because they yield items one by one instead of storing the list.",
        "GIL prevents multiple threads from executing python bytecode at once, so CPU-bound tasks are single-threaded.",
        "Для оптимизации SQL запросов я использую индексы и стараюсь избегать N+1 через select_related.",
        "Стоп игра."
    ]
    
    # 2. Senior Developer Scenario
    inputs_senior = [
        "Привет. Я Алекс, Senior Backend. 5 лет опыта, строил микросервисы на FastAPI, Highload системы.",
        "Python's asyncio uses an event loop to handle I/O bound tasks concurrently without OS threads.",
        "For database sharding, I prefer key-based sharding for even distribution, but it makes resharding hard.",
        "Metaclasses allow intercepting class creation. Useful for frameworks, but I avoid them in business logic to keep code readable.",
        "Стоп игра."
    ]
    
    run_scenario("alex_middle", "Alex Middle", inputs_middle)
    # run_scenario("alex_senior", "Alex Senior", inputs_senior)
