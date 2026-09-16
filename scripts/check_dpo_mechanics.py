import json
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM, set_seed
from trl import DPOConfig, DPOTrainer

from triage_poc.dpo import adapter_fingerprint, verify_dpo_weight_changes

set_seed(42)
torch.set_num_threads(2)
tokenizer = AutoTokenizer.from_pretrained(
    "artifacts/kaggle/continuation-v22-reports/source-sft-v2-continuation-500/trainer/checkpoint-500",
    local_files_only=True,
)
model = Qwen3ForCausalLM(
    Qwen3Config(
        vocab_size=len(tokenizer),
        hidden_size=32,
        intermediate_size=64,
        num_hidden_layers=1,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=16,
    )
)
model = get_peft_model(
    model,
    LoraConfig(r=2, lora_alpha=2, target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM"),
    adapter_name="policy",
)
model.save_pretrained("artifacts/dpo-cpu-mechanics/initial", selected_adapters=["policy"])
model.load_adapter(
    "artifacts/dpo-cpu-mechanics/initial/policy", adapter_name="reference", is_trainable=False
)
model.set_adapter("policy")
rows = Dataset.from_list(
    [
        {
            "prompt": "Synthetic question: choose the stated colour blue.",
            "chosen": "Blue.",
            "rejected": "Red.",
        },
        {
            "prompt": "Synthetic question: repeat the word test.",
            "chosen": "Test.",
            "rejected": "Other.",
        },
    ]
)
config = DPOConfig(
    output_dir="artifacts/dpo-cpu-mechanics/trainer",
    max_steps=2,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=1,
    max_length=64,
    max_prompt_length=32,
    model_adapter_name="policy",
    ref_adapter_name="reference",
    use_cpu=True,
    fp16=False,
    bf16=False,
    report_to="none",
    save_strategy="no",
    learning_rate=5e-4,
    disable_tqdm=True,
)
trainer = DPOTrainer(model=model, args=config, processing_class=tokenizer, train_dataset=rows)
before = {n: adapter_fingerprint(model, n) for n in ["policy", "reference"]}
trainer.train()
after = {n: adapter_fingerprint(model, n) for n in ["policy", "reference"]}
result = verify_dpo_weight_changes(before, after)
Path("artifacts/dpo-cpu-mechanics/result.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result))
