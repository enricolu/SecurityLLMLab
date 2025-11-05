"""Fine-tuning utilities using Hugging Face Transformers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from ..config import TrainingConfig
from ..logging_utils import configure_logging


@dataclass(slots=True)
class FineTuningResult:
    output_dir: Path
    total_steps: int


class FineTuner:
    def __init__(self, config: TrainingConfig) -> None:
        self.config = config
        self.logger = configure_logging(name=self.__class__.__name__)

    def run(self, dataset_path: str) -> FineTuningResult:
        from datasets import load_from_disk
        from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments

        dataset = load_from_disk(dataset_path)
        tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        def tokenize_function(batch):
            return tokenizer(batch["instruction"], batch.get("response", ""), truncation=True)

        tokenized = dataset.map(tokenize_function, batched=True)

        model = AutoModelForCausalLM.from_pretrained(self.config.model_name)
        training_args = TrainingArguments(
            output_dir=str(self.config.output_dir),
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            num_train_epochs=1 if self.config.max_steps is None else None,
            max_steps=self.config.max_steps,
            warmup_steps=self.config.warmup_steps,
            save_steps=self.config.save_steps,
            logging_steps=self.config.logging_steps,
            report_to=[]
        )

        trainer = Trainer(model=model, args=training_args, train_dataset=tokenized["train"])
        trainer.train()
        trainer.save_model()
        tokenizer.save_pretrained(self.config.output_dir)

        total_steps = trainer.state.global_step
        self.logger.info("Fine-tuning completed at step %s", total_steps)
        return FineTuningResult(output_dir=self.config.output_dir, total_steps=total_steps)


__all__ = ["FineTuner", "FineTuningResult"]
