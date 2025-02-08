"""
Read SemEval2019 dataset
"""

import sys
import os

path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
import pandas as pd
import numpy as np
import re

# from config import quantization_config
# from llama_index.llms import HuggingFaceLLM
# from llama_index.prompts import PromptTemplate
# from llama_index import (
#     VectorStoreIndex,
#     ServiceContext,
# )
# from llama_index.readers import BeautifulSoupWebReader
import requests
import json


class SemEval:
    def __init__(self):
        self.twitter_train_path = (
            "./data_collection/benchmarks/SemEval2019/TwitterTrainDataSrc.csv"
        )
        self.reddit_train_path = (
            "./data_collection/benchmarks/SemEval2019/RedditTrainDataSrc.csv"
        )
        self.twitter_dev_path = (
            "./data_collection/benchmarks/SemEval2019/TwitterDevDataSrc.csv"
        )
        self.reddit_dev_path = (
            "./data_collection/benchmarks/SemEval2019/RedditDevDataSrc.csv"
        )
        self.twitter_test_path = (
            "./data_collection/benchmarks/SemEval2019/TwitterTestDataSrc.csv"
        )
        self.reddit_test_path = (
            "./data_collection/benchmarks/SemEval2019/RedditTestDataSrc.csv"
        )
        print(self.twitter_train_path)

    def read_semeval(self, mode="train", mode_3cls=False):
        if mode == "train":
            twitterTrainDf = pd.read_csv(self.twitter_train_path)
            redditTrainDf = pd.read_csv(self.reddit_train_path)
            twitterDevDf = pd.read_csv(self.twitter_dev_path)
            redditDevDf = pd.read_csv(self.reddit_dev_path)
            trainDf = self.processStanceData(twitterTrainDf, redditTrainDf)
            devDf = self.processStanceData(twitterDevDf, redditDevDf)

            text_a = trainDf["pReplyText"].values.tolist()
            text_b = trainDf["pPreviousPlusSrcText"].values.tolist()
            X_train = [[b, a] for a, b in zip(text_a, text_b)]
            if mode_3cls:
                y_train = (
                    trainDf["labelValue"]
                    .apply(lambda x: 0 if x == 0 else 2 if x == 1 else 1)
                    .values.tolist()
                )
            else:
                y_train = trainDf["labelValue"].values.tolist()

            text_a = devDf["pReplyText"].values.tolist()
            text_b = devDf["pPreviousPlusSrcText"].values.tolist()
            X_val = [[b, a] for a, b in zip(text_a, text_b)]
            y_val = devDf["labelValue"].values.tolist()
            if mode_3cls:
                y_val = (
                    devDf["labelValue"]
                    .apply(lambda x: 0 if x == 0 else 2 if x == 1 else 1)
                    .values.tolist()
                )
            else:
                y_val = devDf["labelValue"].values.tolist()
            return X_train, X_val, y_train, y_val
        elif mode == "test":
            twitterTestDf = pd.read_csv(self.twitter_test_path)
            redditTestDf = pd.read_csv(self.reddit_test_path)
            testDf = self.processStanceData(twitterTestDf, redditTestDf)

            text_a = testDf["pReplyText"].values.tolist()
            text_b = testDf["pPreviousPlusSrcText"].values.tolist()
            X_test = [[b, a] for a, b in zip(text_a, text_b)]
            if mode_3cls:
                y_test = (
                    testDf["labelValue"]
                    .apply(lambda x: 0 if x == 0 else 2 if x == 1 else 1)
                    .values.tolist()
                )
            else:
                y_test = testDf["labelValue"].values.tolist()
            return X_test, y_test

    def RAG_enrichment(self):
        # LLM settings
        llm = HuggingFaceLLM(
            model_name="HuggingFaceH4/zephyr-7b-alpha",  # HuggingFaceH4/zephyr-7b-beta
            tokenizer_name="HuggingFaceH4/zephyr-7b-alpha",
            query_wrapper_prompt=PromptTemplate(
                "<|system|>\n</s>\n<|user|>\n{query_str}</s>\n<|assistant|>\n"
            ),
            context_window=3000,
            max_new_tokens=1600,
            model_kwargs={"quantization_config": quantization_config},
            # tokenizer_kwargs={},
            generate_kwargs={"temperature": 0.7, "top_k": 50, "do_sample": True},
            messages_to_prompt=self.messages_to_prompt,
            device_map="auto",
        )
        # Load data and enrich with RAG
        twitterTrainDf = pd.read_csv(self.twitter_train_path)
        redditTrainDf = pd.read_csv(self.reddit_train_path)
        twitterDevDf = pd.read_csv(self.twitter_dev_path)
        redditDevDf = pd.read_csv(self.reddit_dev_path)
        twitterTestDf = pd.read_csv(self.twitter_test_path)
        redditTestDf = pd.read_csv(self.reddit_test_path)
        dataframes = [
            twitterTrainDf,
            redditTrainDf,
            twitterDevDf,
            redditDevDf,
            twitterTestDf,
            redditTestDf,
        ]
        seen = {}
        for dataframe in dataframes:
            print("dataframe:", dataframe.columns)
            for _, row in dataframe.iterrows():
                urls = []
                # check if there is a URL in the text
                text_x_url = re.findall(
                    r"https?://(?:www\.)?[\w\.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+",
                    row["text_x"],
                )
                if text_x_url:
                    print(
                        f"URL found in text: {row['text_x']}, text_x_url: {text_x_url}"
                    )
                    urls.extend(["".join(x) for x in text_x_url])
                # skip nan values
                if not pd.isna(row["inre_x"]):
                    inre_x_url = re.findall(
                        r"https?://(?:www\.)?[\w\.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+",
                        row["inre_x"],
                    )
                    if inre_x_url:
                        print(
                            f"URL found in inre: {row['inre_x']}, inre_x_url: {inre_x_url}"
                        )
                        urls.extend(["".join(x) for x in inre_x_url])
                print("urls:", urls)
                documents = BeautifulSoupWebReader().load_data(urls)
                print("documents:", documents)
                break
            break
            # service_context = ServiceContext.from_defaults(
            #     llm=llm,
            #     embed_model="local:BAAI/bge-large-en",
            #     chunk_size=512,
            #     chunk_overlap=64,)
            # vector_index = VectorStoreIndex.from_documents(documents, service_context=service_context)
            # query_engine = vector_index.as_query_engine(response_mode="tree_summarize", similarity_top_k=4)

    def get_twitter_ids(self):
        twitterTrainDf = pd.read_csv(self.twitter_train_path)
        twitterDevDf = pd.read_csv(self.twitter_dev_path)
        twitterTestDf = pd.read_csv(self.twitter_test_path)
        twitter_map = {}
        for dataframe in [twitterTrainDf, twitterDevDf, twitterTestDf]:
            for _, row in twitterTrainDf.iterrows():
                urls = []
                # check if there is a URL in the text
                text_x_url = re.findall(
                    r"https?://(?:www\.)?[\w\.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+",
                    row["text_x"],
                )
                if text_x_url:
                    # print(f"URL found in text: {row['text_x']}, text_x_url: {text_x_url}")
                    urls.extend(["".join(x) for x in text_x_url])
                # skip nan values
                if not pd.isna(row["inre_x"]):
                    try:
                        inre_x_url = re.findall(
                            r"https?://(?:www\.)?[\w\.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+",
                            row["inre_x"],
                        )
                        if inre_x_url:
                            # print(f"URL found in inre: {row['inre_x']}, inre_x_url: {inre_x_url}")
                            urls.extend(["".join(x) for x in inre_x_url])
                    except Exception as e:
                        print(f"Error getting inre_x_url for {row['inre_x']}: {e}")
                # print('urls:', urls)
                for url in urls:
                    try:
                        response = requests.get(url, timeout=1)
                        redirected_url = response.url
                        # print('redirected url:', url)
                        tweet_id = response.url.split("/")[-1]
                        twitter_map[redirected_url] = tweet_id
                    except Exception as e:
                        print(f"Error getting tweet id for {url}: {e}")
        # store twitter_map in a json file
        with open("twitter_map.json", "w") as f:
            json.dump(twitter_map, f)
        return twitter_map

    @staticmethod
    def messages_to_prompt(messages):
        prompt = ""
        for message in messages:
            if message.role == "system":
                prompt += f"<|system|>\n{message.content}</s>\n"
            elif message.role == "user":
                prompt += f"<|user|>\n{message.content}</s>\n"
            elif message.role == "assistant":
                prompt += f"<|assistant|>\n{message.content}</s>\n"
        # ensure we start with a system prompt, insert blank if needed
        if not prompt.startswith("<|system|>\n"):
            prompt = "<|system|>\n</s>\n" + prompt
        # add final assistant prompt
        prompt = prompt + "<|assistant|>\n"
        return prompt

    def processStanceData(self, twitterDf, RedditDf):
        frames = [twitterDf, RedditDf]

        resultDf = pd.concat(frames)  # Concatenating twitter and reddit data
        result1 = resultDf.replace(np.nan, "", regex=True)  # Getting rid of NaN values

        result1["labelvalue"] = result1.label_x.apply(
            self.label_to_int
        )  # Converting labels to numbers
        result1["SrcInre"] = result1["inreText"].str.cat(result1["sourceText"], sep=" ")

        data = result1[
            ["text_x", "id", "inre_x", "source_x", "label_x", "SrcInre", "labelvalue"]
        ].copy()

        """ replyText           - the reply post (whose stance towards the target needs to be learnt)
            replyTextId         - the ID of the reply post
            previousText        - the text to which replyText was replied
            sourceText          - the source post of the conversation thread
            label               - the label value assigned to each post
            previousPlusSrctext - the concatenation of the previousText and the sourceText
            labelValue          - the numberic value assigned to each label"""

        data.columns = [
            "replyText",
            "replyTextId",
            "previousText",
            "sourceText",
            "label",
            "previousPlusSrcText",
            "labelValue",
        ]

        data["pReplyText"] = data.replyText.apply(self.processText)
        data["pPreviousPlusSrcText"] = data.previousPlusSrcText.apply(self.processText)
        return data

    def statistic(self):
        pass

    @staticmethod
    def label_to_int(label):
        if label == "support":
            return 0
        elif label == "comment":
            return 1
        elif label == "deny":
            return 2
        elif label == "query":
            return 3
        else:
            return 1

    @staticmethod
    def processText(text):
        text = re.sub(
            r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?",
            "$URL$",
            text.strip(),
        )
        text = re.sub(r"(@[A-Za-z0-9]+)", "$MENTION$", text.strip())
        return text


if __name__ == "__main__":
    semeval = SemEval()

    X_train, X_val, y_train, y_val = semeval.read_semeval(mode="train")
    X_test, y_test = semeval.read_semeval(mode="test")
    print(
        f"There are {len(X_train)} training samples and {len(X_val)} validation samples"
    )
    print(f"There are {len(X_test)} test samples")
    # semeval.RAG_enrichment()
    semeval.get_twitter_ids()
