from transformers import pipeline

class llamaAgent:
    def __init__(self, model_id="meta-llama/Meta-Llama-3-8B-Instruct"):
        self.pipe = pipeline(
            "text-generation",
            model=model_id,
            model_kwargs={"torch_dtype": "bfloat16"},
            device_map="auto"
        )

    def chat(self, system_prompt, user_prompt,
            max_new_tokens=256, temperature=0.6, top_p=0.9):

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        prompt = self.pipe.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        outputs = self.pipe(prompt,
                            max_new_tokens=max_new_tokens,
                            do_sample=True,
                            temperature=temperature,
                            top_p=top_p)

        return outputs[0]["generated_text"]
