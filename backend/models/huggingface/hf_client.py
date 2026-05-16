from huggingface_hub import InferenceClient
from configs.settings import HUGGINGFACE_API_KEY

client = InferenceClient(
    provider="hf-inference",
    api_key=HUGGINGFACE_API_KEY
)
def chat_with_huggingface(model, prompt):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a powerful AI assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000
    )

    return completion.choices[0].message.content