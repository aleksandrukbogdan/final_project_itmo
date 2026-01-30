import sys
import json
from agents import AgentManager, FactCheckerAgent, PsychologistAgent, MentorAgent, InterviewerAgent, DecisionMakerAgent
from logger import InterviewLogger

def main():
    print("Initializing Multi-Agent Interview Coach (v2.0)...")
    
    logger = InterviewLogger()
    manager = AgentManager()
    
    # Регистрация агентов (версия 2)
    manager.register_agent("FactChecker", FactCheckerAgent)
    manager.register_agent("Psychologist", PsychologistAgent)
    manager.register_agent("Mentor", MentorAgent)
    manager.register_agent("Interviewer", InterviewerAgent)
    manager.register_agent("DecisionMaker", DecisionMakerAgent)
    
    fact_checker = manager.get_agent("FactChecker")
    psychologist = manager.get_agent("Psychologist")
    mentor = manager.get_agent("Mentor")
    interviewer = manager.get_agent("Interviewer")
    decision_maker = manager.get_agent("DecisionMaker")
    
    print("Welcome! The panel is ready. (Interviewer, Mentor, Fact-Checker, Psychologist, Decision-Maker)")
    print("Type 'STOP' to end the interview.\n")
    
    participant_name = input("Enter your name: ")
    logger.start_session(participant_name)
    
    history = []
    full_log_text = ""
    
    # Первое приветствие (сгенерированное или ручное)
    print("\nInterviewer: Привет! Давай начнем твое собеседование. Расскажи о себе.")
    
    while True:
        try:
            user_input = input(f"\n{participant_name}: ")
        except EOFError:
            break
            
        if user_input.strip().upper() == "STOP":
            print("\nInterview finished. The Decision-Maker is deliberating...")
            break
            
        history.append({"role": "Candidate", "content": user_input})
        full_log_text += f"\nCandidate: {user_input}"
        
        print("\n--- Analysing... ---")
        
        # 1. Параллельный анализ (Факты + Психология)
        fact_ctx = {"user_message": user_input}
        fact_report = fact_checker.run(fact_ctx)
        
        psych_ctx = {"user_message": user_input}
        psych_report = psychologist.run(psych_ctx)
        
        print(f"[Fact-Checker]: {fact_report}")
        print(f"[Psychologist]: {psych_report}")
        
        # 2. Стратегия ментора
        mentor_ctx = {
            "history": history,
            "fact_check": fact_report,
            "psych_profile": psych_report
        }
        instruction = mentor.run(mentor_ctx)
        print(f"[Mentor]: {instruction}")
        
        # 3. Ответ интервьюера
        interviewer_ctx = {
            "history": history,
            "instruction": instruction
        }
        response = interviewer.run(interviewer_ctx)
        
        # Обновление состояния
        history.append({"role": "Interviewer", "content": response})
        full_log_text += f"\nInterviewer: {response}"
        
        # Логирование
        # Очищаем отчеты от переносов строк для красивого лога
        fc_clean = str(fact_report).replace('\n', ' ').strip()
        psych_clean = str(psych_report).replace('\n', ' ').strip()
        mentor_clean = str(instruction).replace('\n', ' ').strip()
        
        combined_thoughts = f"[Fact-Checker] {fc_clean} | [Psychologist] {psych_clean} | [Mentor] {mentor_clean}"
        logger.log_turn(user_input, combined_thoughts, response)
        
        print(f"\n[Interviewer]: {response}")

        # Check for Mentor's termination signal
        if instruction.interview_status == "TERMINATE":
             print("\n--- Interview Concluded by Mentor ---")
             break

    # 4. Финальное решение
    dm_ctx = {"full_log": full_log_text}
    final_decision = decision_maker.run(dm_ctx)
    
    logger.log_feedback(final_decision)
    print("\n--- Final Decision ---")
    print(final_decision)
    print(f"\nSession saved to {logger.filename}")

if __name__ == "__main__":
    main()
