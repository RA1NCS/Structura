import random
from clients import get_document_intelligence_client
from inference import get_docintel_result
import json
from concurrent.futures import ThreadPoolExecutor, as_completed


# Choose a random train set from the file set
def get_random_train_set(file_set, train_size, max_test_size=None, specific_files=None):
    if specific_files:
        train_set = specific_files
    else:
        train_set = random.sample(file_set, train_size)
    test_set = [file for file in file_set if file not in train_set]
    if max_test_size:
        test_set = random.sample(test_set, max_test_size)
    return train_set, test_set


# Generate new fewshot examples from the provided file set and write them to a file
def write_fewshot_examples(train_set, dataset):
    docintel_client = get_document_intelligence_client()

    ground_truths = []
    for file in train_set:
        ground_truths.append(
            json.load(open(f"datasets/{dataset}/annotations/{file}.json", "r"))
        )

    ocr_results = [None] * len(train_set)
    max_workers = 15
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_index = {}
        for index, file in enumerate(train_set):
            img_bytes = open(f"datasets/{dataset}/images/{file}.png", "rb").read()
            future = pool.submit(get_docintel_result, docintel_client, img_bytes)
            future_to_index[future] = index
        for future in as_completed(future_to_index):
            index = future_to_index[future]
            ocr_result, _ = future.result()
            ocr_results[index] = ocr_result

    fewshot_examples = ""
    for index in range(len(train_set)):
        fewshot_examples += (
            f"\n{'='*100}\nEXAMPLE {index+1}\n{'='*100}\n\n"
            f"INPUT:\n{'-'*50}\n{ocr_results[index]}\n{'-'*50}\n\n"
            f"OUTPUT:\n{'-'*50}\n{json.dumps(ground_truths[index], indent=4)}\n{'-'*50}\n\n"
            f"{'='*100}\n\n"
        )

    with open(f"prompts/{dataset}/fewshot_examples.txt", "w") as f:
        f.write(fewshot_examples)


# Get the system prompt for a dataset
def get_system_prompt(train_set, dataset, overwrite=True, use_fewshot=True):
    if overwrite:
        write_fewshot_examples(train_set, dataset)

    base_prompt = open(f"prompts/{dataset}/prompt.txt", "r").read()
    fewshot_examples = open(f"prompts/{dataset}/fewshot_examples.txt", "r").read()

    return (
        f"{base_prompt}\n\nUse the following examples to guide your response:\n{fewshot_examples}"
        if use_fewshot
        else base_prompt
    )
