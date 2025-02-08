import math
from transformers import RobertaTokenizer, RobertaForMaskedLM
import argparse
import pandas as pd
import numpy as np
from datasets import load_metric
from data_collection.dataset_loader.torch_dataset_loader import torch_dataset_loader
from transformers import (
    CONFIG_MAPPING,
    MODEL_FOR_MASKED_LM_MAPPING,
    MODEL_FOR_CAUSAL_LM_MAPPING,
    PreTrainedTokenizer,
    TrainingArguments,
    AutoConfig,
    AutoTokenizer,
    AutoModelWithLMHead,
    AutoModelForCausalLM,
    AutoModelForMaskedLM,
    LineByLineTextDataset,
    TextDataset,
    DataCollatorForLanguageModeling,
    DataCollatorForWholeWordMask,
    DataCollatorForPermutationLanguageModeling,
    PretrainedConfig,
    Trainer,
    set_seed,
)
from sklearn.model_selection import train_test_split
import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

os.environ["TOKENIZERS_PARALLELISM"] = "false"
metric = load_metric("accuracy")


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return metric.compute(predictions=predictions, references=labels)


if __name__ == "__main__":
    # finetuning setting
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-om",
        "--online_pretrained_model",
        help="select online pretrained model for fine tunning",
        default="bert",
    )
    parser.add_argument(
        "-n",
        "--new_model_name",
        help="select online pretrained model for fine tunning",
        default="new_model",
    )
    args = parser.parse_args()

    model_name = args.online_pretrained_model
    new_model_name = args.new_model_name

    print("Further Pretraining using {}".format(model_name))

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, mlm=True, mlm_probability=0.15,
    )

    train_dataset = LineByLineTextDataset(
        tokenizer=tokenizer,
        file_path="./data_collection/processed_datasets/further_pretrain_corpus_TRAIN.txt",
        block_size=512,
    )
    eval_dataset = LineByLineTextDataset(
        tokenizer=tokenizer,
        file_path="./data_collection/processed_datasets/further_pretrain_corpus_EVAL.txt",
        block_size=512,
    )

    model = AutoModelForMaskedLM.from_pretrained(model_name)

    training_args = TrainingArguments(
        # output directory
        output_dir="./model_zoo/results/{}".format(new_model_name),
        do_train=True,
        do_eval=True,
        num_train_epochs=1,  # total number of training epochs
        per_device_train_batch_size=8,  # batch size per device during training
        per_device_eval_batch_size=8,  # batch size for evaluation
        # number of warmup steps for learning rate scheduler
        warmup_steps=500,
        weight_decay=0.01,  # strength of weight decay
        # directory for storing logs
        logging_dir="./model_zoo/logs/{}".format(new_model_name),
        logging_steps=100,
        prediction_loss_only=True,
        # save_steps=200,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()

    eval_output = trainer.evaluate()

    perplexity = math.exp(eval_output["eval_loss"])
    print("\nEvaluate Perplexity: {:10,.2f}".format(perplexity))
    tokenizer.save_pretrained("./model_zoo/models/{}".format(new_model_name))
    model.save_pretrained("./model_zoo/models/{}".format(new_model_name))


"""
Sen. Barack Obama of Illinois tried to make the point that enforcement against people who hire undocumented workers has to improve.
 
But statistics show the feds at least outpace lightning strikes.
 
Given current data, indictments out of employer investigations happen 4.6 times more often than people get hit by lightning, figured Deborah Rumsey, author of
 
Probability for Dummies
 
and
 
Statistics for Dummies
 
, among other books. Rumsey, a statistics education specialist at Ohio State University, helped PolitiFact.com review the stats.
 
"Neither one of these is a common occurrence, but compared to each other, there's a big difference," Rumsey said.
 
Asked to support his statement, the Obama campaign cited a
 
Washington Post
 
report that showed only three businesses were fined — a more narrow look than prosecutions — for employing illegal immigrants in 2004.
 
Being fined is indeed rarer than lightning hitting someone.
 
But based on figures from the U.S. Department of Homeland Security and the National Weather Service, we find that the change Obama demanded in Thursday's debate already has happened, at least in meteorological terms.
 
For starters, lightning hits an average of 1,000 to 1,100 people a year, according to the National Weather Service. That would make strikes on people a 1.1-in-303,000 probability, using current U.S. Census population estimates.
 
Now consider indictments in investigations of employers, which numbered 441 in 2006, according to an annual report of the Office of Immigration Statistics at the U.S. Department of Homeland Security.
 
Based only on indictments, there was a 5.1-in-303,000 chance an employer would be prosecuted to the point of indictment. That's based on a U.S. Census count of nearly 26.3-million businesses from 2004, the most recent year full data is available.
 
It should be noted that the number of employers is tough to determine; officials with the IRS and the U.S. Bureau of Labor Statistics said they had no data. The Census count is its largest available, with other surveys showing smaller numbers — and even higher chances of indictments against employers.
 
Given these findings, we rule Obama's statement False.
"""
