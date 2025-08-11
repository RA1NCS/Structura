import os
from system_prompt import get_random_train_set
from benchmark import Benchmarker
from schemas import EmptyJSON as FUNSDSchema, CORDSchema
from clients import get_document_intelligence_client, get_instructor_client
from optimizer import optimize_few_shot

dataset_name = "funsd"
schema = FUNSDSchema
model = "gpt-4o-mini"

fewshot_count = 15
fewshot_z_swap = 5
max_test_size = 100


# Load dataset from datasets folder
def load_dataset(dataset):
    base_dir = os.path.join("datasets", dataset)
    ann_dir = os.path.join(base_dir, "annotations")

    ids = []
    for file in os.listdir(ann_dir):
        if file.lower().endswith(".json"):
            ids.append(os.path.splitext(file)[0])

    return [len(ids), sorted(ids)]


def main():
    # init clients once
    doc_client = get_document_intelligence_client()
    llm_client = get_instructor_client()

    benchmarker = Benchmarker(
        dataset_name,
        schema,
        model,
        doc_client,
        llm_client,
        temperature=0.3,
    )
    # load dataset
    file_count, file_list = load_dataset(dataset_name)

    print(
        f"Loaded {file_count} files from {dataset_name} with fewshot count {fewshot_count}"
    )

    # choose random examples
    train_set, test_set = get_random_train_set(
        file_list,
        fewshot_count,
        max_test_size=max_test_size,
        # specific_files=[
        #     "0000999294",
        #     "0001239897",
        #     "0001456787",
        #     "0001463282",
        #     "0001463448",
        #     "0060000813",
        #     "0060036622",
        #     "0060080406",
        #     "0060094595",
        #     "0060262650",
        #     "71108371",
        #     "82200067_0069",
        #     "83553333_3334",
        #     "87594142_87594144",
        #     "91161344_91161347",
        # ],
        # specific_files=[
        #     "075",
        #     "147",
        #     "153",
        #     "227",
        #     "392",
        #     "490",
        #     "493",
        #     "534",
        #     "538",
        #     "552",
        #     "652",
        #     "719",
        #     "807",
        #     "826",
        #     "993",
        # ],
    )

    # optimize fewshot
    new_train_set, new_test_set = optimize_few_shot(
        benchmarker,
        dataset_name,
        train_set,
        test_set,
        fewshot_z_swap,
        num_iterations=5,
    )


if __name__ == "__main__":
    main()
