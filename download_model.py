# pip install accelerate
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME = "meta-llama/Llama-3.2-3B"
#"meta-llama/Llama-3.1-8B"
#"Qwen/Qwen2.5-3B-Instruct"
#"Qwen/Qwen2.5-3B"
#"Qwen/Qwen2.5-1.5B"
#"Qwen/Qwen2.5-0.5B"
#"allenai/Llama-3.1-Tulu-3-8B-SFT"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    device_map="auto",
)

input_text = "Briefly introduce Steve Jobs."
input_ids = tokenizer(input_text, return_tensors="pt").to("cuda")

outputs = model.generate(**input_ids, max_new_tokens=32)
print(tokenizer.decode(outputs[0]))
