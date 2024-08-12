import multiprocessing
import multiprocessing_worker

if __name__ == "__main__":
    with multiprocessing.Pool(5) as p:
        print(p.map(multiprocessing_worker.worker, [1, 2, 3]))
