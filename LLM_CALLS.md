# LLM call map and how to point it to Ollama

This note captures where each component constructs LLM clients and which configuration knobs control the target endpoint. Use it to swap the default online providers with an OpenAI-compatible Ollama instance (e.g., `http://localhost:11434/v1`).

## API entry points
- **Archivist streaming**: `api.py` -> `/query/sse` and `/query/stream_steps/sse` -> `Archivist.process_query` / `process_query_stream`.
- **Archivist async**: `api.py` -> `/query/celery` -> Celery task `tasks.async_process_query` -> `Archivist.process_query`.
- **Researcher async**: `api.py` -> `/research/` -> Celery task `tasks.async_research` -> `Researcher.search`.
- **Interrogator async**: `api.py` -> `/interrogation/` -> Celery task `tasks.async_interrogation` -> `Interrogator.interrogation`.

## Archivist (src/Archivist)
- The agent builds a ReAct graph in `Archivist._build_agent`, then calls `get_llm` (`models/llm.py`) to obtain the chat model for LangGraph.
- `get_llm` reads `config["model"]` passed from the API request or falls back to `config.yaml -> models`.
- Provider hooks:
  - OpenAI: `models/openai.py#get_openai_llm` → `ChatOpenAI(model=model_id, openai_api_key=..., base_url=<models.endpoint_url>)`.
  - Bedrock: `models/bedrock.py#get_bedrock_llm`.
  - Local stub: `models/local.py#get_local_llm` currently returns `None`.
- **Ollama**: set `models.API: OPENAI`, `models.model_id` to your Ollama model name, `models.endpoint_url: http://localhost:11434/v1`, and provide any `OPENAI_API_KEY` (ignored by Ollama but required by the client).
- **Env overrides** (all components): set `LLM_BASE_URL` to override the base URL (e.g., Ollama) and `LLM_MODEL_ID` to override the model name without touching config files. These take precedence over `endpoint_url` and configured `model_id`.

## Interrogator (src/Interrogator)
- The StateGraph uses LLMs in three places:
  - `graph/nodes/generate_question.py` (uses `question_generator`, but switches to `write_conclusion` when emitting the final conclusion prompt).
  - `graph/nodes/refine_answer.py` (uses `report_generator`).
  - `graph/nodes/write_report.py` (uses `write_conclusion`; shares the same config block as the final-turn question above).
- Each node calls `models/llm.py#get_default_llm(node_name=...)`, which loads the model config from `config.yaml -> models.default` or the node-specific block.
- OpenAI helper: `models/openai.py#get_openai_llm` -> `ChatOpenAI(..., base_url=<endpoint_url>)`. Bedrock/Google/local adapters are also available; the local adapter is a stub.
- **Ollama**: in `config.yaml`, set the relevant `models.*` entries to `API: OPENAI`, add `endpoint_url: http://localhost:11434/v1`, and set `model_id` to the Ollama model. The Interrogator will then hit Ollama through the OpenAI-compatible path.

## Researcher (src/Researcher)
- LLM usage points:
  - `graph/nodes/query_extractor.py` binds tools and calls `get_default_llm(node_name="query_extractor")` to rewrite/route the query.
  - `graph/nodes/response_generator.py` calls `get_default_llm(node_name="response_generator")` to synthesize the final answer (and, if enabled, chunk filtering).
- `models/llm.py#get_default_llm` pulls configs from `config.yaml -> models.default/query_extractor/response_generator` and dispatches to OpenAI/Bedrock/Google.
- OpenAI helper: `models/openai.py#get_openai_llm` -> `ChatOpenAI(..., base_url=<endpoint_url>)`.
- **Ollama**: set the `models.*` blocks in `config.yaml` to `API: OPENAI`, set `endpoint_url: http://localhost:11434/v1`, choose the Ollama `model_id`, and keep `OPENAI_API_KEY` set (dummy is fine).

## Quick Ollama config snippets
Update each component’s `config.yaml` (copied from the corresponding `config.example.yaml`):

```yaml
models:
  API: "OPENAI"
  model_id: "llama3.1:8b"   # any Ollama-served model name
  args:
    temperature: 0.2
  endpoint_url: "http://localhost:11434/v1"
```

For Interrogator/Researcher node-specific blocks (e.g., `models.query_extractor`, `models.response_generator`, `models.question_generator`, `models.report_generator`), use the same fields if you want different Ollama models per node.
