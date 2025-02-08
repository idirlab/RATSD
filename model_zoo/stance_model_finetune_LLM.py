from peft import (
    LoraConfig,
    PeftConfig,
    PeftModel,
    TaskType,
    get_peft_model,
    prepare_model_for_kbit_training,
)
from config import quantization_config, mac_quantization_config
import torch
import argparse
import numpy as np
import evaluate
from data_collection.dataset_loader.torch_dataset_loader import torch_dataset_loader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from sklearn.model_selection import train_test_split
from data_pipeline import get_dataset
import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
# set cache dir for transformers
os.environ["TRANSFORMERS_CACHE"] = "../.cache/huggingface/"
# set cache dir for llama_index
os.environ["LLAMA_INDEX_CACHE_DIR"] = "../.cache/llama_index/"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
sys.path.append(path)
torch.manual_seed(42)


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)


if __name__ == "__main__":
    # finetuning setting
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--datasource",
        help="select datasource from truthSD/semeval/wtwt/all",
        default="semeval",
    )
    parser.add_argument(
        "-m",
        "--pretrained_model",
        help="select local pretrained model for fine tunning",
        default="",
    )
    parser.add_argument(
        "-om",
        "--online_pretrained_model",
        help="select online pretrained model for fine tunning",
        default="bert-base-uncased",
    )
    parser.add_argument(
        "-n",
        "--new_model_name",
        help="select online pretrained model for fine tunning",
        default="new_model",
    )
    parser.add_argument(
        "-bs", "--batch_size", help="batchsize for fine tunning", default=4, type=int
    )
    parser.add_argument(
        "-ep", "--epochs", help="epochs for fine tunning", default=6, type=int
    )
    parser.add_argument(
        "-lr",
        "--learning_rate",
        help="initial learning rate for fine tunning",
        default=2e-5,
        type=float,
    )
    parser.add_argument(
        "-dm",
        "--device_map",
        help="the device allocated for fine tunning",
        default="auto",
        type=str,
    )
    parser.add_argument(
        "-mtc",
        "--user_metric",
        help="the computing metrics",
        default="accuracy",
        type=str,
    )
    args = parser.parse_args()

    data_source = args.datasource
    pretrain_model = args.pretrained_model
    online_model = args.online_pretrained_model
    new_model_name = args.new_model_name
    batch_size = args.batch_size
    epochs = args.epochs
    learning_rate = args.learning_rate
    device_map = args.device_map
    metric = evaluate.load(args.user_metric)

    if pretrain_model:
        model_name = "./model_zoo/models/{}".format(pretrain_model)
    else:
        model_name = online_model
    print("Training on {} dataset using {}".format(data_source, model_name))

    X_train, _, y_train, _, target_classes = get_dataset(data_source=data_source)

    # print available GPUs
    print("Available devices:", torch.cuda.device_count())

    # tokenize dataset
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    train_encodings = tokenizer(X_train, truncation=True, padding=True)

    train_dataset = torch_dataset_loader(train_encodings, y_train)

    quantization_config = (
        mac_quantization_config if device_map == "mps" else quantization_config
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        device_map="auto",
        trust_remote_code=True,
        num_labels=len(target_classes),
        quantization_config=quantization_config,
    )
    model.gradient_checkpointing_enable()
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_dropout=0.1,
        bias="none",
        task_type=TaskType.SEQ_CLS,
    )
    model = get_peft_model(model, lora_config)
    model.config.use_cache = False
    # model.config.pretraining_tp = 1
    # print_trainable_parameters(model)

    training_args = TrainingArguments(
        # output directory
        output_dir="./model_zoo/results/{}".format(new_model_name),
        num_train_epochs=epochs,  # total number of training epochs
        # batch size per device during training
        per_device_train_batch_size=batch_size,
        learning_rate=learning_rate,
        fp16=True,
        save_total_limit=3,
        optim="paged_adamw_8bit",
        warmup_ratio=0.05,
        report_to=None,
        lr_scheduler_type="cosine",
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    tokenizer.save_pretrained("./model_zoo/models/{}".format(new_model_name))
    model.save_pretrained("./model_zoo/models/{}".format(new_model_name))
