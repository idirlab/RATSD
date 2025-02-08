import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
os.environ[
    "TRANSFORMERS_CACHE"
] = "../.cache/huggingface/"  # set cache dir for transformers
os.environ[
    "LLAMA_INDEX_CACHE_DIR"
] = "../.cache/llama_index/"  # set cache dir for llama_index
os.environ["TOKENIZERS_PARALLELISM"] = "false"
sys.path.append(path)

from data_collection.dataset_loader.SemEval import SemEval
from data_collection.dataset_loader.WTWT2020 import WTWT2020
from data_collection.dataset_loader.TruthfulnessStance import (
    TruthfulnessStanceDetection,
)
from sklearn.model_selection import train_test_split
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
)
from transformers import EarlyStoppingCallback
from data_collection.dataset_loader.torch_dataset_loader import torch_dataset_loader
import evaluate
import numpy as np
import argparse


def get_dataset(data_source="semeval"):
    if data_source not in ["semeval", "wtwt2020", "truthSD"]:
        raise ValueError(
            "data_source should be one of 'semeval', 'wtwt2020', 'truthSD'"
        )

    if data_source == "semeval":
        semeval = SemEval()
        X_train, X_val, y_train, y_val = semeval.read_semeval(mode="train")
    elif data_source == "wtwt2020":
        wtwt2020 = WTWT2020()
        texts_wt, labels_wt = wtwt2020.read_wtwt()
        X_train, _, y_train, _ = train_test_split(
            texts_wt, labels_wt, test_size=0.2, random_state=42
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.1, random_state=42
        )  # 0.25 x 0.8 = 0.2
    elif data_source == "truthSD":
        tsd = TruthfulnessStanceDetection()
        text, labels = tsd.read_annotations()
        X_train, X_val, y_train, y_val = train_test_split(
            text, labels, test_size=0.01, random_state=42
        )
        X_train, _, y_train, _ = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
        )
    return X_train, X_val, y_train, y_val


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
        "-ep", "--epochs", help="batchsize for fine tunning", default=42, type=int
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

    X_train, X_val, y_train, y_val = get_dataset(data_source=data_source)

    # tokenize dataset
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    train_encodings = tokenizer(X_train, truncation=True, padding=True)
    val_encodings = tokenizer(X_val, truncation=True, padding=True)

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
        load_best_model_at_end=True,
        evaluation_strategy="steps",
        eval_steps=500,
        # save_steps=200,
    )

    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=4)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    trainer.train()
    trainer.evaluate()

    tokenizer.save_pretrained("./model_zoo/models/{}".format(new_model_name))
    model.save_pretrained("./model_zoo/models/{}".format(new_model_name))


"""
What is the truthfulness stance of the tweet towards the factual claim?

The tweet believes the factual claim is true.
The tweet expresses a neutral or no stance towards the factual claim's truthfulness.
The tweet believes the factual claim is false.
The tweet and the claim discuss different topics.
"""
