from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.tools import FunctionTool
from app.llm.prompt import SYSTEM_PROMPT


class LLMClient:
    def __init__(self, user_prompt: str, model="gemini-2.5-flash"):
        self.llm = GoogleGenAI(model=model)
        self.user_prompt = user_prompt

    def chat_completion(self):
        messages = self.set_message()
        response = self.llm.chat(messages)
        return response.message.content

    def chat_with_tools(self, tools: list):
        """Chat with the LLM while providing tools it can call."""
        messages = self.set_message()
        response = self.llm.chat_with_tools(tools, chat_history=messages)
        return response

    def get_tool_calls(self, response):
        """Extract tool calls from an LLM response."""
        return self.llm.get_tool_calls_from_response(
            response, error_on_no_tool_call=False
        )

    def set_message(self):
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            ChatMessage(role=MessageRole.USER, content=self.user_prompt),
        ]
        return messages