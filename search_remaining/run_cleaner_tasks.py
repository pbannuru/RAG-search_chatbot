from batch_jobs.internal.scheduler.task_runner import TaskRunner
from batch_jobs.tasks.index_cleaner.taxonomy import Taxonomy
from batch_jobs.tasks.index_cleaner.index_cleaner_deletion import index_data_deletion

def main():
 
    # Initialize tasks
    os_cleaner_deletion_job = index_data_deletion()

    # taxonomy task:
    taxonomy_updation_job = Taxonomy()
    # Create TaskRunner and add tasks
    runner = TaskRunner()
    # runner.add(os_cleaner_deletion_job)
    runner.add(taxonomy_updation_job)

    # Run tasks
    runner.run()

if __name__ == "__main__":
    main()