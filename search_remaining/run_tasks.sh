#!/bin/bash

# Activate the virtual environment
source /opt/env/bin/activate

# Run the main task and capture output and error logs
python run_tasks.py > /logs/job.output 2> /logs/job.errors
ret_tasks=$?
echo "run_tasks.py return code: $ret_tasks"

# Check the return code and send email if there's an error
if [[ $ret_tasks -gt 0 ]] || [[ $ret_tasks == -1 ]]; then
    python mail.py "run_tasks.py" "Error encountered in jobs execution." /logs/job.output /logs/job.errors
fi

# Run the cleaner task and capture output and error logs
python run_cleaner_tasks.py > /logs/cleaner.output 2> /logs/cleaner.errors
ret_cleaner=$?
echo "run_cleaner_tasks.py return code: $ret_cleaner"

# Check the return code and send email if there's an error
if [[ $ret_cleaner -gt 0 ]] || [[ $ret_cleaner == -1 ]]; then
    python mail.py "run_cleaner_tasks.py" "Error encountered in cleaner task execution." /logs/cleaner.output /logs/cleaner.errors
fi
