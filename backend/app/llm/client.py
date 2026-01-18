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

    def execute(self, tools: list):
        """
        Execute the agent loop: call LLM with tools, execute tool calls, return final response.
        
        Args:
            tools: List of FunctionTool objects
            
        Returns:
            The final response content from the LLM
        """
        # Build tool lookup by name
        tools_by_name = {t.metadata.name: t for t in tools}
        
        # Start conversation
        chat_history = self.set_message()
        
        # Call LLM with tools
        response = self.llm.chat_with_tools(tools, chat_history=chat_history)
        tool_calls = self.get_tool_calls(response)
        
        # If no tool calls, just return the response
        if not tool_calls:
            return response.message.content
        
        # Process tool calls in a loop
        while tool_calls:
            # Add LLM's response to history
            chat_history.append(response.message)
            
            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.tool_name
                tool_kwargs = tool_call.tool_kwargs
                
                # Get and call the tool
                tool = tools_by_name.get(tool_name)
                if tool:
                    tool_output = tool.call(**tool_kwargs)
                else:
                    tool_output = f"Error: Tool '{tool_name}' not found"
                
                # Add tool result to history
                chat_history.append(
                    ChatMessage(
                        role="tool",
                        content=str(tool_output),
                        additional_kwargs={"tool_call_id": tool_call.tool_id},
                    )
                )
            
            # Call LLM again with updated history
            response = self.llm.chat_with_tools(tools, chat_history=chat_history)
            tool_calls = self.get_tool_calls(response)
        
        return response.message.content