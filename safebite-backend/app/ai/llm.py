from langchain_core.runnables import RunnableLambda

# This is a placeholder Runnable — NOT connected to any real LLM yet.
# Milestone 5 replaces this with an actual Ollama-backed Runnable.
echo_runnable = RunnableLambda(lambda input_text: f"[echo] {input_text}")