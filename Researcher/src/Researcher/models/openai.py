"""
Description:
OpenAI language model integration for the Researcher agent. Provides factory function
to create and configure ChatOpenAI instances with custom parameters and endpoint support.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date: 2025/03/10
"""
import os
from langchain_openai import ChatOpenAI
from Researcher.utils import config  

def get_openai_llm(model_id: str, endpoint_url=None, **kwargs):
    """
    Returns an instance of OpenAI's LLM with additional parameters.

    Requires the environment variable `OPENAI_API_KEY` to be set.

    Args:
        model_id (str): The OpenAI model name or ID to use.
        endpoint_url (str, optional): Custom endpoint URL for API requests.
        **kwargs: Additional arguments (e.g., max_tokens, temperature, top_p).

    Returns:
        ChatOpenAI: Configured instance of OpenAI's model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    env_base_url = os.getenv("LLM_BASE_URL")
    env_model_id = os.getenv("LLM_MODEL_ID")

    final_base_url = env_base_url or endpoint_url
    if final_base_url:
        kwargs["base_url"] = final_base_url
    
    model_to_use = env_model_id or model_id
    return ChatOpenAI(model_name=model_to_use, openai_api_key=api_key, **kwargs)
