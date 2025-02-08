import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
os.environ["TRANSFORMERS_CACHE"] = (
    "../.cache/huggingface/"  # set cache dir for transformers
)
os.environ["LLAMA_INDEX_CACHE_DIR"] = (
    "../.cache/llama_index/"  # set cache dir for llama_index
)
os.environ["TOKENIZERS_PARALLELISM"] = "false"
sys.path.append(path)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    GPT2ForSequenceClassification,
    Trainer,
    TrainingArguments,
    GPT2Tokenizer,
)
from transformers import EarlyStoppingCallback
from data_collection.dataset_loader.torch_dataset_loader import torch_dataset_loader
from data_pipeline import get_dataset
import evaluate
import numpy as np
import argparse
import torch


metric = evaluate.load("accuracy")


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
        "-bs", "--batch_size", help="batchsize for fine tunning", default=12, type=int
    )
    parser.add_argument(
        "-ep", "--epochs", help="epochs for fine tunning", default=8, type=int
    )
    args = parser.parse_args()

    data_source = args.datasource
    pretrain_model = args.pretrained_model
    online_model = args.online_pretrained_model
    new_model_name = args.new_model_name
    batch_size = args.batch_size
    epochs = args.epochs

    if pretrain_model:
        model_name = "./model_zoo/models/{}".format(pretrain_model)
    else:
        model_name = online_model
    print("Training on {} dataset using {}".format(data_source, model_name))

    X_train, X_val, y_train, y_val, target_class = get_dataset(data_source=data_source)

    # print available GPUs
    print("Available devices:", torch.cuda.device_count())

    # tokenize dataset
    if model_name == "gpt2":
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    train_encodings = tokenizer(X_train, truncation=True, padding=True, max_length=512)
    val_encodings = tokenizer(X_val, truncation=True, padding=True, max_length=512)
    # train_encodings = tokenizer(X_train, padding=True, return_tensors="pt")
    # val_encodings = tokenizer(X_val, padding=True, return_tensors="pt")

    train_dataset = torch_dataset_loader(train_encodings, y_train)
    val_dataset = torch_dataset_loader(val_encodings, y_val)

    training_args = TrainingArguments(
        output_dir="./model_zoo/results/{}".format(new_model_name),  # output directory
        num_train_epochs=epochs,  # total number of training epochs
        per_device_train_batch_size=batch_size,  # batch size per device during training
        per_device_eval_batch_size=batch_size,  # batch size for evaluation
        warmup_steps=500,  # number of warmup steps for learning rate scheduler
        weight_decay=0.01,  # strength of weight decay
        logging_dir="./model_zoo/logs/{}".format(
            new_model_name
        ),  # directory for storing logs
        logging_steps=100,
        report_to=None,
        # load_best_model_at_end=True,
        # evaluation_strategy="steps",
        # eval_steps=500,
        load_best_model_at_end=False,
        evaluation_strategy="no",
        do_eval=False,
    )
    if model_name == "gpt2":
        model = GPT2ForSequenceClassification.from_pretrained(
            model_name, num_labels=len(target_class), ignore_mismatched_sizes=True
        )
        model.config.pad_token_id = model.config.eos_token_id
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=len(target_class), ignore_mismatched_sizes=True
        )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        # eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    tokenizer.save_pretrained("./model_zoo/models/{}".format(new_model_name))
    model.save_pretrained("./model_zoo/models/{}".format(new_model_name))
