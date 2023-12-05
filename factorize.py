import multiprocessing
import time

def factorize_sync(numbers):
    results = []
    for number in numbers:
        factors = []
        for i in range(1, number + 1):
            if number % i == 0:
                factors.append(i)
        results.append(factors)
    return results

def factorize_parallel(numbers):
    with multiprocessing.Pool() as pool:
        results = pool.map(factorize_single, numbers)
    return results

def factorize_single(number):
    factors = []
    for i in range(1, number + 1):
        if number % i == 0:
            factors.append(i)
    return factors

if __name__ == "__main__":
    numbers = [128, 255, 99999, 10651060]

    start_time = time.time()
    result_sync = factorize_sync(numbers)
    print(f"Synchronous execution time: {time.time() - start_time} seconds")
    print("Results (synchronous):", result_sync)

    start_time = time.time()
    result_parallel = factorize_parallel(numbers)
    print(f"Parallel execution time: {time.time() - start_time} seconds")
    print("Results (parallel):", result_parallel)

    assert result_sync == result_parallel
