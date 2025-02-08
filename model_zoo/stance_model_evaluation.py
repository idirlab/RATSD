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

from data_pipeline import get_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    GPT2ForSequenceClassification,
    Trainer,
    TrainingArguments,
    GPT2Tokenizer,
)
from data_collection.dataset_loader.torch_dataset_loader import torch_dataset_loader
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report
from tqdm import tqdm
import argparse
from collections import defaultdict
import pandas as pd

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


if __name__ == "__main__":
    # Evaluate parameter setting
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--datasource",
        help="select datasource from semeval/wtwt/truthSD",
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
        default="",
    )
    args = parser.parse_args()
    if args.datasource not in [
        "semeval",
        "wtwt2020",
        "truthSD",
        "truthSD-3",
        "truthSD-3-rag",
        "semeval-3",
        "wtwt2020-3",
        "covidlies",
    ]:
        raise ValueError(
            "data_source should be one of 'semeval', 'wtwt2020', 'truthSD', 'truthSD-3",
            "semeval-3', 'wtwt2020-3', 'covidlies'",
        )
    if args.pretrained_model == "" and args.online_pretrained_model == "":
        raise ValueError("Please provide a pretrained model name.")

    data_source = args.datasource
    online_model = args.online_pretrained_model
    pretrain_model = args.pretrained_model
    print(pretrain_model, online_model)
    if pretrain_model:
        model_name = "./model_zoo/models/{}".format(pretrain_model)
    else:
        model_name = online_model
    print("Evaluating on {} dataset using {}".format(data_source, model_name))

    _, X_test, _, y_test, target_classes = get_dataset(data_source=data_source)
    if model_name == "gpt2":
        tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    else:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    test_encodings = tokenizer(X_test, truncation=True, padding=True, max_length=512)

    test_dataset = torch_dataset_loader(test_encodings, y_test)

    if model_name == "gpt2":
        model = GPT2ForSequenceClassification.from_pretrained(
            model_name, num_labels=len(target_classes)
        )
        model.config.pad_token_id = model.config.eos_token_id
    else:
        model = AutoModelForSequenceClassification.from_pretrained(
            model_name, num_labels=len(target_classes)
        )
    model.to(device)

    test_dataloader = DataLoader(test_dataset, batch_size=1)
    y_pred = []

    with torch.no_grad():
        for batch in tqdm(test_dataloader):
            batch = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**batch)
            logits = outputs.logits
            batch_predictions = torch.argmax(logits, dim=-1).tolist()
            y_pred.extend(batch_predictions)

    print(classification_report(y_test, y_pred, target_names=target_classes, digits=5))
    # FP, FN = []*4, []*4
    mp = defaultdict(list)
    eval_res = []
    for idx, (t, p) in enumerate(zip(y_test, y_pred)):
        eval_res.append(
            [
                X_test[idx][0],
                X_test[idx][1],
                target_classes[t],
                target_classes[p],
                t == p,
            ]
        )

    df_eval_res = pd.DataFrame(eval_res)
    df_eval_res.to_csv(
        "./model_zoo/eval_results/eval_annotation.csv",
        header=["Claim", "Tweet", "GroundTruth", "Prediction", "IsTrue"],
    )

    # Code below only for terminal testing
    # for k, v in mp.items():
    #     print('------'*5)
    #     print('------'*5)
    #     print("Ground truth: {}".format(WTWT2020_CLASS_NAMES[k[0]]))
    #     print("Prediction: {}".format(WTWT2020_CLASS_NAMES[k[1]]))
    #     for x in v:
    #         print("Claim: {}".format(x[0]))
    #         print("Tweet: {}".format(x[1]))
    #         print('------'*5)
