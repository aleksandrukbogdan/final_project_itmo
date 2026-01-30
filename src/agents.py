from abc import ABC, abstractmethod
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
import config
from llm_client import LLMClient
from knowledge_base import InterviewKnowledgeBase
from schemas import (
    FactCheckReport, PsychProfile, MentorStrategy, 
    JudgeVerdict, ConversationSummary, FinalDecisionReport
)

class BaseAgent(ABC):
    def __init__(self, name: str, client: LLMClient):
        self.name = name
        self.llm = client.get_llm()

    @abstractmethod
    def run(self, context: Dict[str, Any]) -> Any:
        """
        Запуск логики агента.
        """
        pass

class FactCheckerAgent(BaseAgent):
    def __init__(self, name: str, client: LLMClient, kb: InterviewKnowledgeBase):
        super().__init__(name, client)
        self.kb = kb
        self.parser = PydanticOutputParser(pydantic_object=FactCheckReport)

    def run(self, context: Dict[str, Any]) -> FactCheckReport:
        user_msg = context.get("user_message", "")
        facts = self.kb.verify_fact(user_msg)
        
        template = (
            config.FACT_CHECKER_PROMPT + 
            "\n\nKnown Facts (from Knowledge Base):\n{facts}" +
            "\n\nCandidate Statement:\n{user_msg}" +
            "\n\n{format_instructions}"
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        # Используем json_mode если поддерживается, или полагаемся на инструкции
        chain = prompt | self.llm | self.parser
        
        return chain.invoke({
            "facts": facts, 
            "user_msg": user_msg,
            "format_instructions": self.parser.get_format_instructions()
        })

class PsychologistAgent(BaseAgent):
    def __init__(self, name: str, client: LLMClient):
        super().__init__(name, client)
        self.parser = PydanticOutputParser(pydantic_object=PsychProfile)

    def run(self, context: Dict[str, Any]) -> PsychProfile:
        user_msg = context.get("user_message", "")
        
        template = (
            config.PSYCHOLOGIST_PROMPT + 
            "\n\nCandidate Statement:\n{user_msg}" +
            "\n\n{format_instructions}"
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | self.parser
        
        return chain.invoke({
            "user_msg": user_msg,
            "format_instructions": self.parser.get_format_instructions()
        })

class MentorAgent(BaseAgent):
    def __init__(self, name: str, client: LLMClient):
        super().__init__(name, client)
        self.parser = PydanticOutputParser(pydantic_object=MentorStrategy)

    def run(self, context: Dict[str, Any]) -> MentorStrategy:
        history = context.get("history", [])
        fact_check = context.get("fact_check", "N/A")
        psych_profile = context.get("psych_profile", "N/A")
        
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in history[-5:]])
        
        template = (
            config.MENTOR_PROMPT + 
            "\n\nConversation History:\n{formatted_history}" +
            "\n\nFact-Checker Report:\n{fact_check}" +
            "\n\nPsychologist Report:\n{psych_profile}" +
            "\n\n{format_instructions}"
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | self.parser
        
        return chain.invoke({
            "formatted_history": formatted_history,
            "fact_check": str(fact_check), # Конвертируем объект pydantic в строку, если нужно
            "psych_profile": str(psych_profile),
            "format_instructions": self.parser.get_format_instructions()
        })

class InterviewerAgent(BaseAgent):
    # Вывод обычной строки подходит для финального ответа, но можно использовать структуру для метрик.
    # Пока оставляем текст, чтобы не усложнять речь.
    def run(self, context: Dict[str, Any]) -> str:
        instruction = context.get("instruction", "")
        history = context.get("history", [])
        tone = context.get("tone", "Neutral")
        
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in history[-5:]])

        template = (
            config.INTERVIEWER_PROMPT + 
            "\n\nMentor's Instruction: {instruction}" +
            "\nMentor's Desired Tone: {tone}" +
            "\n\nConversation History:\n{formatted_history}" +
            "\n\nYour Response to Candidate:"
        )

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({
            "instruction": instruction,
            "tone": tone,
            "formatted_history": formatted_history
        })

class JudgeAgent(BaseAgent):
    def __init__(self, name: str, client: LLMClient):
        super().__init__(name, client)
        self.parser = PydanticOutputParser(pydantic_object=JudgeVerdict)

    def run(self, context: Dict[str, Any]) -> JudgeVerdict:
        history = context.get("history", [])
        instruction = context.get("instruction", "")
        generated_response = context.get("generated_response", "")
        
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in history[-3:]])
        
        template = (
            config.JUDGE_PROMPT + 
            "\n\nRecent History:\n{formatted_history}" +
            "\n\nMentor Instruction: {instruction}" +
            "\n\nInterviewer Generated Response: {generated_response}" +
            "\n\n{format_instructions}"
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | self.parser
        
        return chain.invoke({
            "formatted_history": formatted_history,
            "instruction": instruction,
            "generated_response": generated_response,
            "format_instructions": self.parser.get_format_instructions()
        })

class SummarizerAgent(BaseAgent):
    def __init__(self, name: str, client: LLMClient):
        super().__init__(name, client)
        self.parser = PydanticOutputParser(pydantic_object=ConversationSummary)

    def run(self, context: Dict[str, Any]) -> ConversationSummary:
        history = context.get("history", [])
        
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in history])
        
        template = (
            config.SUMMARIZER_PROMPT + 
            "\n\nConversation to Summarize:\n{formatted_history}" +
            "\n\n{format_instructions}"
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | self.parser
        
        return chain.invoke({
            "formatted_history": formatted_history,
            "format_instructions": self.parser.get_format_instructions()
        })

class DecisionMakerAgent(BaseAgent):
    def __init__(self, name: str, client: LLMClient):
        super().__init__(name, client)
        self.parser = PydanticOutputParser(pydantic_object=FinalDecisionReport)

    def run(self, context: Dict[str, Any]) -> FinalDecisionReport:
        full_log = context.get("full_log", "")
        
        template = (
            config.DECISION_MAKER_PROMPT + 
            "\n\nInterview Log:\n{full_log}" + 
            "\n\n{format_instructions}"
        )
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | self.parser
        return chain.invoke({
            "full_log": full_log,
            "format_instructions": self.parser.get_format_instructions()
        })

class AgentManager:
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.llm_client = LLMClient()
        self.kb = InterviewKnowledgeBase()

    def register_agent(self, name: str, agent_class: Any):
        if agent_class == FactCheckerAgent:
            self.agents[name] = agent_class(name, self.llm_client, self.kb)
        else:
            self.agents[name] = agent_class(name, self.llm_client)

    def get_agent(self, name: str) -> BaseAgent:
        return self.agents.get(name)
