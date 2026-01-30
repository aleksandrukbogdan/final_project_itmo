from langchain_openai import ChatOpenAI
import config

class LLMClient:
    """
    Wrapper for LangChain ChatOpenAI.
    """
    def __init__(self):
        self.llm = ChatOpenAI(
            model=config.QWEN_MODEL_NAME,
            api_key=config.QWEN_API_KEY,
            base_url=config.QWEN_BASE_URL,
            temperature=0.7
        )

    def get_llm(self):
        return self.llm
        
    def get_completion(self, messages, temperature=0.7):
        """
        Legacy/Fallback method.
        If any code still calls this, we map it to the langchain invocation.
        messages is [{"role": "user", "content": "..."}]
        """
        # Minimal adaptation for legacy calls if any exist
        # Assuming messages is just a list of dicts.
        # We can construct a prompt or just pass them if they are compatible types.
        # LangChain accepts list of (role, content) tuples or BaseMessages.
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        
        lc_messages = []
        for m in messages:
            if m["role"] == "user":
                lc_messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "system":
                lc_messages.append(SystemMessage(content=m["content"]))
            elif m["role"] == "assistant":
                lc_messages.append(AIMessage(content=m["content"]))
                
        # Override temp if needed, or use default
        response = self.llm.invoke(lc_messages)
        return response.content
