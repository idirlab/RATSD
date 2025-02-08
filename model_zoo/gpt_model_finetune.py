from sklearn.model_selection import train_test_split
from data_collection.dataset_loader.TruthfulnessStance import (
    TruthfulnessStanceDetection,
)
from data_collection.dataset_loader.WTWT2020 import WTWT2020
from data_collection.dataset_loader.SemEval import SemEval
from data_collection.dataset_loader.COVIDLies import COVIDLies
import pandas as pd
import json
from openai import OpenAI
from credentials import OPENAI_API_KEY
from sklearn.metrics import classification_report
from tqdm import tqdm

client = OpenAI(api_key=OPENAI_API_KEY)


# Read datasets
def read_datasets(dataset):
    if dataset == "semeval-3":
        semeval = SemEval()
        target_classes = ["Positive", "Neutral", "Negative"]
        X_train, X_val, y_train, y_val = semeval.read_semeval(
            mode="train", mode_3cls=True
        )
        X_test, y_test = semeval.read_semeval(mode="test", mode_3cls=True)
        return X_train + X_val, X_test, y_train + y_val, y_test, target_classes
    elif dataset == "wtwt2020-3":
        wtwt2020 = WTWT2020()
        target_classes = ["Positive", "Neutral", "Negative"]
        texts_wt, labels_wt = wtwt2020.read_wtwt(mode="3cls")
        X_train, X_test, y_train, y_test = train_test_split(
            texts_wt, labels_wt, test_size=0.2, random_state=42
        )
    elif dataset == "truthSD-3":
        tsd = TruthfulnessStanceDetection()
        target_classes = ["Positive", "Neutral", "Negative"]
        text, labels = tsd.read_annotations(mode="3cls")
        X_train, X_test, y_train, y_test = train_test_split(
            text, labels, test_size=0.2, random_state=42
        )
    elif dataset == "covidlies":
        cl = COVIDLies()
        target_classes = ["Positive", "Neutral", "Negative"]
        text, labels = cl.read_annotations()
        print(len(text), len(labels))
        X_train, X_test, y_train, y_test = train_test_split(
            text, labels, test_size=0.2, random_state=42
        )
        # X_train = [[y, x] for x, y in X_train]
        # X_test = [[y, x] for x, y in X_test]
    return X_train, X_test, y_train, y_test, target_classes


def create_training_sample(X_train, y_train):
    # Function to create a fine-tuning example
    def create_example(x, y):
        system_message = "Classify the truthfulness stance of tweet toward the factual claim. Respond only with the category letter in square brackets. The categories are 0: Positive, 1: Neutral, 2: Negative"
        user_message = f"Claim: {x[0]}\n\nTweet: {x[1]}"
        assistant_message = f"[{y}]"

        return {
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_message},
            ]
        }

    fine_tuning_data = []
    for x, y in zip(X_train, y_train):
        fine_tuning_data.append(create_example(x, y))

    # Save to JSONL file
    with open("TruthSD_fine_tuning_data.jsonl", "w") as f:
        for item in fine_tuning_data:
            f.write(json.dumps(item) + "\n")


def upload_training_file():
    upload_response = client.files.create(
        file=open("TruthSD_fine_tuning_data.jsonl", "rb"), purpose="fine-tune"
    )
    file_id = upload_response.id
    print(f"File uploaded with ID: {file_id}")


def finetuning(file_id):
    # Create the fine-tuning job
    job = client.fine_tuning.jobs.create(
        training_file=file_id, model="gpt-3.5-turbo-1106"
    )
    job_id = job.id
    print(f"Fine-tuning job created with ID: {job_id}")


def check_status(job_id):
    # Check the status of the fine-tuning job
    job_status = client.fine_tuning.jobs.retrieve(job_id)
    print(f"Job status: {job_status.status}")
    return job_status


def predict(example, job_status):
    response = client.chat.completions.create(
        model=job_status.fine_tuned_model,  # Use your fine-tuned model ID here
        # model="gpt-3.5-turbo-1106",
        messages=[
            {
                "role": "system",
                # "content": "Classify the truthfulness stance of tweet toward the factual claim. Respond only with the category letter in square brackets.",
                "content": "Classify the truthfulness stance of tweet toward the factual claim. Respond only with the category letter in square brackets. The categories are 0: Positive, 1: Neutral, 2: Negative",
            },
            {"role": "user", "content": example},
        ],
    )
    return response.choices[0].message.content


def evaluate_model(X_test, y_test, job_status):
    y_pred = []

    for x_test in tqdm(X_test):
        example = f"Claim: {x_test[0]}\nTweet: {x_test[1]}"
        prediction = predict(example, job_status)
        try:
            prediction = int(prediction[1])
            y_pred.append(prediction)
        except:
            y_pred.append(1)
            print(prediction)

    print(y_test)
    print(y_pred)
    print(
        classification_report(
            y_test, y_pred, target_names=["Positive", "Neutral", "Negative"], digits=5
        )
    )


if __name__ == "__main__":
    pass