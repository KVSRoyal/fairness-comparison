import fire
import statistics

from data.objects.list import DATASETS, get_dataset_names
from data.objects.ProcessedData import ProcessedData
from algorithms.list import ALGORITHMS
from metrics.list import METRICS, FAIRNESS_METRICS

NUM_TRIALS_DEFAULT = 10
RESULT_DIR = "results/"

def run(num_trials = NUM_TRIALS_DEFAULT, dataset_names = get_dataset_names()):
    print("WARNING: be sure that you have run `python3 preprocess.py` before running this script.")

    for dataset in DATASETS:
        if not dataset.get_dataset_name() in dataset_names:
            continue
        print("\nEvaluating dataset:" + dataset.get_dataset_name())

        processed_dataset = ProcessedData(dataset)
        processed_splits, numerical_splits = processed_dataset.create_train_test_splits(num_trials)

        for algorithm in ALGORITHMS:
            print("    Algorithm:" + algorithm.get_name())
            numeric_results = {}
            alldata_results = {}
            for i in range(0, num_trials):

                if not algorithm.numerical_data_only():
                    train, test = processed_splits[i]
                    run_eval_alg(algorithm, train, test, dataset, alldata_results)

                train, test = numerical_splits[i]
                run_eval_alg(algorithm, train, test, dataset, numeric_results)
           
            for metric_name in numeric_results:
                print("        average " + metric_name + ": " + str(statistics.mean(numeric_results[metric_name])))
                print("        stdev " + metric_name + ": " + str(statistics.stdev(numeric_results[metric_name])))
                
            for metric_name in alldata_results:
                print("        average " + metric_name + ": " + str(statistics.mean(alldata_results[metric_name])))
                print("        stdev " + metric_name + ": " + str(statistics.stdev(alldata_results[metric_name])))
            ## TODO: write avg and stddev per metric to file

def run_eval_alg(algorithm, train, test, dataset, results_dict):
    actual, predicted, sensitive = run_alg(algorithm, train, test, dataset)

    for Metric in METRICS:
        m = Metric(actual, predicted)
        result = m.calc() 
        name = m.get_metric_name()
        if not name in results_dict:
            results_dict[name] = []
        results_dict[name].append(result)

    privileged_vals = dataset.get_privileged_class_names()
    positive_val = dataset.get_positive_class_val()
    for FairnessMetric in FAIRNESS_METRICS:
        m = FairnessMetric(actual, predicted, sensitive, privileged_vals, positive_val)
        result = m.calc() 
        name = m.get_metric_name()
        if not name in results_dict:
            results_dict[name] = []
        results_dict[name].append(result)
 
def run_alg(algorithm, train, test, dataset):
    class_attr = dataset.get_class_attribute()
    sensitive_attrs = dataset.get_sensitive_attributes()
    params = {}  ## TODO: algorithm specific parameters still need to be handled

    # get the actual classifications and sensitive attributes
    actual = test[class_attr]
    for attr in sensitive_attrs:
       ## TODO: actually deal with multiple protected attributes
       sensitive = test[attr].values.tolist()

    # Note: the training and test set here still include the sensitive attributes because
    # some fairness aware algorithms may need those in the dataset.  They should be removed
    # before any model training is done. 
    predictions = algorithm.run(train, test, class_attr, sensitive_attrs, params)

    return actual, predictions, sensitive

def main():
    fire.Fire(run)

if __name__ == '__main__':
    main()