import os
import requests
import json
from time import sleep

class LlamaClient:
    def __init__(self):
        # Initialize the Llama client with environment variables
        self.api_url = os.getenv('LLAMA_API_URL')  # Llama API URL from environment variable
        self.api_key = os.getenv('LLAMA_API_KEY')  # OpenRouter API key from environment variable
        self.retry_count = int(os.getenv('LLAMA_RETRY_COUNT', 3))  # Number of retries in case of failure
        self.timeout = int(os.getenv('LLAMA_TIMEOUT', 10))  # Timeout for each request

    def analyze_mood_with_system_prompt(self, system_prompt, text):
        """
        Sends a request to Llama to analyze the mood, with a predefined system prompt.
        This method ensures that the conversation is focused on movie recommendations.
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',  # Authentication header with API key
            'Content-Type': 'application/json',  # Setting the content type to JSON
        }
        
        # Construct the conversation messages with roles
        messages = [
            {'role': 'system', 'content': system_prompt},  # The system prompt to guide Llama
            {'role': 'user', 'content': text}  # The user input (mood description)
        ]

        # Add the assistant's role to reinforce the rule
        messages.append({'role': 'assistant', 'content': 'Only provide movie recommendations based on the mood described by the user.'})

        # Prepare the data for the API request, including system prompt and user input
        data = {
            'model': 'meta-llama/llama-3.1-8b-instruct',  # The model to use (Llama 3.1 8b Instruct)
            'messages': messages  # Add system prompt and user input to the conversation
        }

        # Retry logic in case the API call fails
        for attempt in range(self.retry_count):
            try:
                # Make the API call to the Llama model
                response = requests.post(self.api_url, headers=headers, json=data, timeout=self.timeout)
                response.raise_for_status()  # Raise an exception for HTTP errors (4xx, 5xx)
                return response.json()  # Return the successful response from Llama
            except requests.exceptions.RequestException as e:
                if attempt < self.retry_count - 1:
                    sleep(2)  # Wait before retrying
                    continue
                raise e  # Raise the error if all retry attempts fail
