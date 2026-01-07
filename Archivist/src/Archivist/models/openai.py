"""
Description:
OpenAI LLM implementation. Provides a factory function for creating ChatOpenAI instances
with API key authentication and optional custom endpoint support.

Author: Raptopoulos Petros [petrosrapto@gmail.com]
Date : 2025/03/10
"""
import os
from langchain_openai import ChatOpenAI
from Archivist.utils import config  

def get_openai_llm(model_id: str, **kwargs):
    """
    Returns an instance of OpenAI's LLM with additional parameters.

    Requires the environment variable `OPENAI_API_KEY` to be set.

    Args:
        model_id (str): The OpenAI model name or ID to use.
        **kwargs: Additional arguments (e.g., max_tokens, temperature, top_p).

    Returns:
        ChatOpenAI: Configured instance of OpenAI's model.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")
    
    # Environment overrides
    env_base_url = os.getenv("LLM_BASE_URL")
    env_model_id = os.getenv("LLM_MODEL_ID")

    endpoint_url = env_base_url or config.get("models.endpoint_url", None)
    if endpoint_url:
        kwargs["base_url"] = endpoint_url

    model_to_use = env_model_id or model_id
    return ChatOpenAI(model_name=model_to_use, openai_api_key=api_key, **kwargs)
