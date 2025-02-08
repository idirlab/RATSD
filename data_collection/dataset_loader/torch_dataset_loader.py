import torch


class torch_dataset_loader(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


class StanceDataset(torch.utils.data.Dataset):
    def __init__(
        self, firstSeq, secondSeq, TextSrcInre, labelValue, tokenizer, max_len
    ):
        self.firstSeq = (
            firstSeq  # First input sequence that will be supplied to RoBERTa
        )
        self.secondSeq = (
            secondSeq  # Second input sequence that will be supplied to RoBERTa
        )
        self.TextSrcInre = TextSrcInre  # Concatenation of reply+ previous+ src text to get features from 1 training example
        self.labelValue = (
            labelValue  # label value for each training example in the dataset
        )
        self.tokenizer = tokenizer  # tokenizer that will be used to tokenize input sequences (Uses BERT-tokenizer here)
        self.max_len = max_len  # Maximum length of the tokens from the input sequence that BERT needs to attend to

    def __getitem__(self, item):
        firstSeq = str(self.firstSeq[item])
        secondSeq = str(self.secondSeq[item])
        TextSrcInre = str(self.TextSrcInre[item])

        # Encoding the first and the second sequence to a form accepted by RoBERTa
        # RoBERTa does not use token_type_ids to distinguish the first sequence from the second sequnece.
        encoding = tokenizer.encode_plus(
            firstSeq,
            secondSeq,
            max_length=self.max_len,
            add_special_tokens=True,
            truncation=True,
            pad_to_max_length=True,
            return_attention_mask=True,
            return_tensors="pt",
        )
        return {
            "firstSeq": firstSeq,
            "secondSeq": secondSeq,
            "TextSrcInre": TextSrcInre,
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
            "labelValue": torch.tensor(self.labelValue[item], dtype=torch.long),
        }

    def __len__(self):
        return len(self.labelValue)
