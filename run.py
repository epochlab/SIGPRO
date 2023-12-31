#!/usr/bin/env python3

from arch.llama.llm import Llama
from arch.utils import device_mapper, load_config

from typing import List, Literal, TypedDict

DEVICE = device_mapper()
print(f"Device: {str(DEVICE).upper()}")

MODEL_PATH = "/mnt/artemis/library/weights/meta/llama-2/7Bf"
TOKENIZER_PATH = "/mnt/artemis/library/weights/meta/llama-2/tokenizer.model"

class Message(TypedDict):
    role: Literal["system", "user", "assistant"]
    content: str

Dialog = List[Message]
B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>", "<</SYS>>"

def main():
    LLM = Llama.build(ckpt_dir=MODEL_PATH, tokenizer_path=TOKENIZER_PATH, max_seq_len=512, max_batch_size=8, device=DEVICE)

    dialogs: List[Dialog] = [[{"role": "system", "content": load_config('profiles.yml')['jasmine']}, 
                              {"role": "user", "content": "How fast is an F16?"}]]

    toks = []
    for dialog in dialogs:
        if dialog[0]["role"] == "system":
            dialog = [{"role": dialog[1]["role"], "content": B_SYS + dialog[0]["content"] + E_SYS + dialog[1]["content"]}] + dialog[2:]

        dialog_toks: List[int] = sum([LLM.tokenizer.encode(f"{B_INST} {(prompt['content']).strip()} {E_INST} {(answer['content']).strip()}", bos=True, eos=True,) for prompt, answer in zip(dialog[::2], dialog[1::2],)],[],)
        dialog_toks += LLM.tokenizer.encode(f"{B_INST} {(dialog[-1]['content']).strip()} {E_INST}", bos=True, eos=False)
        toks.append(dialog_toks)

        logprobs = False
        new_toks, logprobs = LLM.generate(prompt_tokens=toks, max_gen_len=None, temperature=0.6, top_p=0.9, logprobs=logprobs)

        if logprobs:
            results = [{"generation": {"role": "assistant", "content": LLM.tokenizer.decode(t)}, "tokens": [LLM.tokenizer.decode(x) for x in t], "logprobs": logprobs_i,} for t, logprobs_i in zip(new_toks, logprobs)]
        else:
            results = [{"generation": {"role": "assistant", "content": LLM.tokenizer.decode(t)}} for t in new_toks]

    for dialog, result in zip(dialogs, results):
        for msg in dialog:
            print(f"{msg['role'].capitalize()}: {msg['content']}")
        print(f">{result['generation']['content']}")

if __name__ == "__main__":
    main()