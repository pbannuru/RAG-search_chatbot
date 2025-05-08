from batch_jobs.enums.ingress_enums import JobType
from batch_jobs.internal.scheduler.task_runner import TaskRunner
from batch_jobs.tasks.KZ.kz import KZLoader
from batch_jobs.tasks.KZ.kz_phase2 import kzProcessorph2
from batch_jobs.tasks.doccebo.doccebo_course_delta import DoceboCourseDeltaLoader
from batch_jobs.tasks.doccebo.docebo_phase2 import doceboProcessorph2
from batch_jobs.tasks.index_cleaner.index_cleaner import OpenSearchManager
from batch_jobs.tasks.index_cleaner.index_cleaner_ph2 import index_cleaner_ph2
from batch_jobs.tasks.kaas.kaas import KaasAPI
import argparse

from batch_jobs.tasks.kaas.kaas_phase2 import kaasProcessorph2


def main():
    print("hello")
    parser = argparse.ArgumentParser(description="Run batch jobs.")
    parser.add_argument(
        "--historical",
        nargs="+",
        choices=["kaas", "docebo", "kz"],
        help="Run historical job for specified modules (kaas, docebo)",
    )
    args = parser.parse_args()

    historical_modules = args.historical if args.historical else []

    # Initialize tasks
    kaas_job = KaasAPI(
        run_type=(
            JobType.HISTORICAL if "kaas" in historical_modules else JobType.INCREMENTAL
        )
    )
    docebo_job = DoceboCourseDeltaLoader(
        run_type=(
            JobType.HISTORICAL
            if "docebo" in historical_modules
            else JobType.INCREMENTAL
        )
    )
    kz_job = KZLoader(
        run_type=(
            JobType.HISTORICAL if "kz" in historical_modules else JobType.INCREMENTAL
        )
    )
    os_cleaner_job = OpenSearchManager()

    kaasph2job = kaasProcessorph2()
    doceboph2job = doceboProcessorph2()
    kzph2job = kzProcessorph2()
    indexcleanerph2 = index_cleaner_ph2()
    # Create TaskRunner and add tasks
    runner = TaskRunner()
    runner.add(kaas_job)
    runner.add(docebo_job)
    runner.add(kz_job)
    runner.add(kaasph2job)
    runner.add(doceboph2job)
    runner.add(kzph2job)
    runner.add(indexcleanerph2)
    # runner.add(os_cleaner_job)
    # Run tasks
    runner.run()


if __name__ == "__main__":
    main()
