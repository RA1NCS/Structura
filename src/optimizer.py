import time
from benchmark import score_benchmark, get_top_files
from system_prompt import get_system_prompt


# Get remaining file ids after removing a subset
def remove_files_from_set(full_set, set_to_remove):
    return [file for file in full_set if file not in set_to_remove]


def forward(
    benchmarker,
    dataset_name,
    train_set,
    test_set,
    iteration,
    z_swap,
):
    start_time = time.time()
    sp_time_total = 0.0
    training_time = 0.0
    testing_time = 0.0
    print(f"\n\n{'-' * 20} ITERATION {iteration} {'-' * 20}")
    print(f"Original train set: {sorted(train_set)}")

    # training
    print("\nRunning training benchmark")
    sp_start = time.time()
    training_system_prompt = get_system_prompt(
        train_set, dataset_name, overwrite=False, use_fewshot=False
    )
    sp_time_total += time.time() - sp_start

    tr_start = time.time()
    training_benchmark = benchmarker.run(
        train_set,
        training_system_prompt,
        fewshot_enabled=False,
        iteration=iteration,
    )
    training_time += time.time() - tr_start

    print(f"> Training Score: {score_benchmark(training_benchmark)}")
    print(f"Training Time: {training_time:.2f} seconds")

    # testing
    sp_start = time.time()
    print("\nGenerating testing system prompt")
    testing_system_prompt = get_system_prompt(
        train_set, dataset_name, overwrite=True, use_fewshot=True
    )
    sp_time_total += time.time() - sp_start
    print(f"System Prompt Generation Time: {sp_time_total:.2f} seconds")

    te_start = time.time()
    print("\nRunning testing benchmark")
    testing_benchmark = benchmarker.run(
        test_set,
        testing_system_prompt,
        fewshot_enabled=True,
        iteration=iteration,
    )
    testing_time += time.time() - te_start

    print(f"> Testing Score: {score_benchmark(testing_benchmark)}")
    print(f"Testing Time: {testing_time:.2f} seconds")

    # swap heuristic
    best_training_files = get_top_files(
        training_benchmark, num_files=z_swap, mode="best"
    )
    worst_testing_files = get_top_files(
        testing_benchmark, num_files=z_swap, mode="worst"
    )

    new_train_set = (
        remove_files_from_set(train_set, best_training_files) + worst_testing_files
    )
    new_test_set = (
        remove_files_from_set(test_set, worst_testing_files) + best_training_files
    )

    print(f"Updated train set: {sorted(new_train_set)}")

    return new_train_set, new_test_set


# Iterate swaps until convergence or max iterations
def optimize_few_shot(
    benchmarker, dataset_name, train_set, test_set, z_swap, num_iterations
):
    for iteration in range((num_iterations or 999999)):
        new_train_set, new_test_set = forward(
            benchmarker,
            dataset_name,
            train_set,
            test_set,
            iteration=iteration,
            z_swap=z_swap,
        )
        if sorted(new_train_set) == sorted(train_set) and sorted(
            new_test_set
        ) == sorted(test_set):
            print(f"Iteration {iteration} reached local optimum")
            break
        train_set, test_set = new_train_set, new_test_set
    return train_set, test_set
