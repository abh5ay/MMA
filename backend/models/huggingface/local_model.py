import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

loaded_models = {}
loaded_tokenizers = {}


def load_model(model_name):

    if model_name not in loaded_models:

        print(f"Loading {model_name}...")

        tokenizer = AutoTokenizer.from_pretrained(model_name)

        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )

        loaded_models[model_name] = model
        loaded_tokenizers[model_name] = tokenizer

    return (
        loaded_models[model_name],
        loaded_tokenizers[model_name]
    )


def generate_response(model_name, prompt, system_prompt):

    model, tokenizer = load_model(model_name)

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        inputs,
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.9,
        do_sample=True
    )

    response = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return response