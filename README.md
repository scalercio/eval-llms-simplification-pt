# evaluation-llms-portuguese-simplification API Application
Evaluation of Large Language Models for Portuguese Sentence Simplification

This application makes requests to an endpoint with a prompt to generate jokes.

## Requirements

- Python 3.7+
- Install dependencies via `pip install -r requirements.txt`
- A valid OpenAI API key if running OpenAI LLMs.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/scalercio/evaluation-llms-portuguese-simplification
   cd evaluation-llms-portuguese-simplification

## Execute

1. Run python script:
   ```python
   python src/evaluate_llm.py "http://127.0.0.1:1234/v1/" data/public_simple_language/test.complex data/public_simple_language/test.simple public_simple_language