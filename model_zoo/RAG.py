# import logging
# import sys
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

from llama_index.core import (
    PromptTemplate,
    Document,
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.llms.openai import OpenAI
from llama_index.llms.huggingface import HuggingFaceLLM

# from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI
from llama_index.core.output_parsers import LangchainOutputParser
from langchain.output_parsers import StructuredOutputParser, ResponseSchema
import os
import json
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer


# setting chunk size and overlap
Settings.chunk_size = 512
Settings.chunk_overlap = 64


####### setting index
# documents = SimpleDirectoryReader(
#     "logs",
# ).load_data()
# index = VectorStoreIndex.from_documents(documents, show_progress=True)

# PERSIST_DIR = "./storage"  # check if storage already exists
# if not os.path.exists(PERSIST_DIR):
#     # load the documents and create the index
#     documents = SimpleDirectoryReader(
#         "../data_collection/raw_data/factcheckrepo"
#         # "logs",
#     ).load_data()
#     index = VectorStoreIndex.from_documents(documents, show_progress=True)
#     # store it for later
#     index.storage_context.persist(persist_dir=PERSIST_DIR)
# else:
#     # load the existing index
#     storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
#     index = load_index_from_storage(storage_context)
####### setting index


####### setting output schema
# response_schemas = [
#     ResponseSchema(
#         name="Claimant",
#         description="Describes the claimant of the factual claim, including his political leanings, credibility, and background.",
#     ),
#     ResponseSchema(
#         name="Claim Entities",
#         description="Describes the entities mentioned in the factual claim",
#     ),
#     ResponseSchema(
#         name="Tweet Entities",
#         description="Describes the entities mentioned in the tweet",
#     ),
# ]
# lc_output_parser = StructuredOutputParser.from_response_schemas(response_schemas)
# output_parser = LangchainOutputParser(lc_output_parser)

####### setting LLM
# Local LLM
# Settings.embed_model = HuggingFaceEmbedding(
#     model_name="BAAI/bge-base-en-v1.5", embed_batch_size=50
# )
# Settings.llm = Ollama(
#     model="llama3.1", request_timeout=360.0, output_parser=output_parser
# )
# Online LLM
# llm = OpenAI(
#     temperature=0.1,
#     model="gpt-3.5-turbo",
#     max_tokens=4096,
#     # output_parser=output_parser
# )

query_wrapper_prompt = PromptTemplate(
    "Below is an instruction that describes a task. "
    "Write a response that appropriately completes the request.\n\n"
    "### Instruction:\n{query_str}\n\n### Response:"
)
llm = HuggingFaceLLM(
    context_window=2048,
    max_new_tokens=256,
    generate_kwargs={"temperature": 0.25, "do_sample": False},
    query_wrapper_prompt=query_wrapper_prompt,
    # tokenizer_name="HuggingFaceH4/zephyr-7b-alpha",
    # model_name="HuggingFaceH4/zephyr-7b-alpha",
    tokenizer_name="Writer/camel-5b-hf",
    model_name="Writer/camel-5b-hf",
    device_map="auto",
    tokenizer_kwargs={"max_length": 2048},
    # uncomment this if using CUDA to reduce memory usage
    # model_kwargs={"torch_dtype": torch.float16}
)
Settings.chunk_size = 512
Settings.llm = llm

####### setting LLM

with open("data_collection/processed_datasets/all_corpus_TruthSD.json", "r") as dataset:
    dataset = json.load(dataset)
    new_dataset = []
    for data in tqdm(dataset):
        corpus = json.dumps(data[-1])
        # print(corpus)
        # print(type(corpus))
        document = Document(text=corpus)
        index = VectorStoreIndex.from_documents([document])
        tweet = data[3]
        claim = data[2]
        query_engine = index.as_query_engine()
        claim_response = query_engine.query(
            f"Consider this factual claim: {claim}. Please provide the details about the claimant, enumerate entities along with their information and provide related information regarding those entities.",
        )
        # print(claim_response_text)
        tweet_response = query_engine.query(
            f"Consider this tweet: {tweet}. Please enumerate entities along with their information and provide related information regarding those entities. Please generate the context knowledge for the factual claim and tweet separately in a structured way."
        )
        context = str(claim_response) + str(tweet_response)
        # print(context, type(context))
        # print(tweet_response_text)
        rephrase_response = llm.complete(
            f"Please paraphrase the tweet {tweet} to: (1) reduce the informality of the tweet and (2) indicate whether the tweet believe the claim: {claim} is true or false based on the context: {context}."
        )
        # print(rephrase_response)
        data.append(str(claim_response))
        data.append(str(tweet_response))
        data.append(str(rephrase_response))
        new_dataset.append(data)

with open(
    "data_collection/processed_datasets/all_corpus_TruthSD_RAG_local.json", "w"
) as dataset:
    json.dump(new_dataset, dataset, indent=4)


# response = query_engine.query(
#     """
# Given a factual claim: "Special Forces arrest Deep State Dr. Anthony Fauci".
# The claimant of the factual claim is "Real raw news".
# The tweet discussing the claim: "Please let this be true. https://trusttheq.com/special-forces-arrest-deep-state-dr-anthony-fauci/".
# Please provide once sentence contextual information about the claimant.
# Please also list entities mentioned in the claim and the tweet, and provide one sentence contextual information about each entity.
# """
# )
# print(response)
