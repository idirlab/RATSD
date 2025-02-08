from peft import (
    LoraConfig,
    PeftConfig,
    PeftModel,
    get_peft_model,
    prepare_model_for_kbit_training,
)
import pandas as pd
from collections import defaultdict
from time import time
import argparse
from tqdm import tqdm
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader
import torch
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


SEMEVAL_CLASS_NAMES = ["Positive", "Neutral", "Negative", "Query"]
WTWT2020_CLASS_NAMES = ["Positive", "Neutral", "Negative", "Unrelated"]
TruthSD_CLASS_NAMES = ["Positive", "Neutral", "Negative"]

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
        "-pm", "--peft_model_name", help="select a fine-tuned peft LLM", default=""
    )
    parser.add_argument(
        "-bm", "--base_model_name", help="select a base LLM", default=""
    )
    args = parser.parse_args()
    if not args.base_model_name:
        raise ValueError("Please provide the base model name")

    data_source = args.datasource
    peft_model_name = args.peft_model_name
    base_model_name = args.base_model_name

    if peft_model_name:
        peft_model_name = "./model_zoo/models/{}".format(peft_model_name)
    else:
        raise ValueError("Please provide a pretrained model name.")
    print("Evaluating on {} dataset using {}".format(data_source, peft_model_name))

    _, X_test, _, y_test, target_classes = get_dataset(data_source=data_source)
    print(f"target_classes: {target_classes}")

    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    test_encodings = tokenizer(X_test, truncation=True, padding=True)

    test_dataset = torch_dataset_loader(test_encodings, y_test)

    base_model = AutoModelForSequenceClassification.from_pretrained(
        base_model_name, num_labels=len(target_classes)
    )
    model = PeftModel.from_pretrained(base_model, peft_model_name)
    model.to(device)
    model.eval()
    model = model.merge_and_unload()

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
