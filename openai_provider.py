import json
import logging
import os
from collections import defaultdict
from typing import Dict, List, Union, Optional, Any, Callable, Generator
import requests

logger = logging.getLogger(__name__)

class OpenAIAPIKeyMissingError(Exception):
    """Raised when the OpenAI API key is missing."""
    pass

class OpenAIAPIError(Exception):
    """Raised when there's an error with the OpenAI API call."""
    pass

class OpenAIProvider:
    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initialize the OpenAI-compatible provider.

        Args:
            api_key (str, optional): The API key for authentication.
            base_url (str, optional): The base URL for the API endpoint.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise OpenAIAPIKeyMissingError("OpenAI API key is not provided")
        
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        self.conversation_sessions = defaultdict(list)
        self.tools = {}

    def set_api_key(self, api_key: str):
        """Update the API key."""
        self.api_key = api_key

    def set_base_url(self, base_url: str):
        """Update the base URL for the API endpoint."""
        self.base_url = base_url

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Fetch available models from the API provider."""
        url = f"{self.base_url}/models"
        headers = self._get_headers()
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])
        except requests.RequestException as e:
            logger.error(f"Failed to fetch models: {e}")
            raise OpenAIAPIError(f"Failed to fetch models: {e}")

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if self.stream else "application/json"
        }

    def register_tool(self, name: str, func: Callable):
        """Register a tool for function calling."""
        self.tools[name] = func

    def start_conversation(self, session_id: str):
        """Initialize a new conversation session."""
        if session_id in self.conversation_sessions:
            logger.warning(f"Session '{session_id}' already exists. Overwriting.")
        self.conversation_sessions[session_id] = []
        logger.info(f"Started new conversation session '{session_id}'.")

    def reset_conversation(self, session_id: str):
        """Reset a conversation session."""
        if session_id in self.conversation_sessions:
            del self.conversation_sessions[session_id]
            logger.info(f"Conversation session '{session_id}' has been reset.")
        else:
            logger.warning(f"Attempted to reset non-existent session '{session_id}'.")

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history for a session."""
        return self.conversation_sessions.get(session_id, [])

    def generate(self, prompt: str, session_id: Optional[str] = None, **kwargs) -> Union[str, Generator[str, None, None]]:
        """
        Generate a response using the language model.

        Args:
            prompt (str): The input prompt.
            session_id (Optional[str]): The session ID for conversation tracking.
            **kwargs: Additional parameters for the API call.

        Returns:
            Union[str, Generator[str, None, None]]: The generated response.
        """
        self.stream = kwargs.get('stream', False)
        if session_id:
            messages = self.conversation_sessions[session_id]
            messages.append({"role": "user", "content": prompt})
        else:
            messages = [{"role": "user", "content": prompt}]

        response = self._create_completion(messages, **kwargs)

        if session_id and not self.stream:
            self.conversation_sessions[session_id].append({
                "role": "assistant",
                "content": response
            })

        return response

    def _create_completion(self, messages: List[Dict[str, str]], **kwargs) -> Union[str, Generator[str, None, None]]:
        """Create a completion using the API."""
        completion_kwargs = {
            "model": kwargs.get("model", "gpt-3.5-turbo"),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1024),
            "top_p": kwargs.get("top_p", 1)
        }

        if self.stream:
            completion_kwargs["stream"] = self.stream

        # Add presence_penalty only if it's provided in kwargs
        if "presence_penalty" in kwargs:
            completion_kwargs["presence_penalty"] = kwargs["presence_penalty"]

        # Add frequency_penalty only if it's provided in kwargs
        if "frequency_penalty" in kwargs:
            completion_kwargs["frequency_penalty"] = kwargs["frequency_penalty"]        

        if kwargs.get("json_mode", False):
            completion_kwargs["response_format"] = {"type": "json_object"}

        if kwargs.get("tools"):
            completion_kwargs["tools"] = kwargs.get("tools")
            completion_kwargs["tool_choice"] = kwargs.get("tool_choice", "auto")

        return self._sync_create_completion(**completion_kwargs)

    def _sync_create_completion(self, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Synchronous completion creation."""
        try:
            url = f"{self.base_url}/chat/completions"
            headers = self._get_headers()
            
            response = requests.post(url, headers=headers, json=kwargs, stream=self.stream)
            response.raise_for_status()
            
            if self.stream:
                return self._process_streaming_response(response)
            else:
                return self._process_completion_response(response.json())
        except requests.RequestException as e:
            raise OpenAIAPIError(f"API request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise OpenAIAPIError(f"Failed to parse API response: {str(e)}")
        except Exception as e:
            raise OpenAIAPIError(f"Error in API call: {str(e)}")

    def _process_completion_response(self, response: Dict[str, Any]) -> str:
        """Process the completion response from the API."""
        if not response.get("choices"):
            raise OpenAIAPIError("Invalid response format: no choices found")
        
        choice = response["choices"][0]
        message = choice.get("message", {})
        
        # Handle function calling
        if message.get("toolCalls"):  # Note the camelCase key
            results = []
            messages = []
            
            # Process each tool call
            for tool_call in message["toolCalls"]:  # Note the camelCase key
                if tool_call["type"] != "function":
                    continue
                    
                function_data = tool_call["function"]
                function_name = function_data["name"]
                
                if function_name in self.tools:
                    try:
                        # Parse and execute function
                        args = json.loads(function_data["arguments"])
                        result = self.tools[function_name](**args)
                        
                        # Add tool call to messages for follow-up completion
                        messages.extend([
                            {
                                "role": "assistant",
                                "toolCalls": [  # Note the camelCase key
                                    {
                                        "id": tool_call["id"],
                                        "type": "function",
                                        "function": {
                                            "name": function_name,
                                            "arguments": function_data["arguments"]
                                        }
                                    }
                                ]
                            },
                            {
                                "role": "tool",
                                "toolCallId": tool_call["id"],  # Note the camelCase key
                                "content": json.dumps(result)
                            }
                        ])
                        
                    except Exception as e:
                        logger.error(f"Error executing function {function_name}: {e}")
                        results.append(str(e))
                else:
                    results.append(f"Function {function_name} not found")
            
            # If we have tool results, make another API call with the tool responses
            if messages:
                #TODO: The following code with hit bad request error
                final_response = self._create_completion(messages)
                return final_response
            
            # If there were only errors, return them
            return "\n".join(results) if results else ""
        
        return message.get("content", "")

    def _process_streaming_response(self, response: requests.Response) -> Generator[str, None, None]:
        """Process streaming response."""
        for line in response.iter_lines():
            if not line:
                continue
            
            try:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                if line.strip() == '[DONE]':
                    break
                    
                chunk = json.loads(line)
                if chunk.get("choices"):
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta and delta["content"] is not None:
                        yield delta["content"]
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse streaming response line: {line}, error: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing streaming response: {e}")
                raise OpenAIAPIError(f"Error processing streaming response: {e}")

if __name__ == "__main__":
    # Function calling
    def get_weather(location: str) -> str:
        return "Sunny"

    # Basic usage
    provider = OpenAIProvider(
                    api_key=os.getenv("OPENAI_API_KEY"), 
                    base_url=os.getenv("OPENAI_BASE_URL")
                )
    
    model=os.getenv("OPENAI_MODEL")
    #response = provider.generate("Hello, how are you?", model=model)
    #print(response)

    # Streaming response
    #response = provider.generate("Tell me a story", stream=True, model=model)
    #for chunk in response:
    #    print(chunk, end='', flush=True)

    provider.register_tool("get_weather", get_weather)
    response = provider.generate(
        "What's the weather in London?",
        tools=[{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }],
        model=model
    )
    print(response)

