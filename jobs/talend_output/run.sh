#!/bin/sh

./$1_run.sh   # Execute the first command
exit_status=$?              # Capture the exit status

./push_meter.sh              # Execute the second command
./push_stats.sh              # Execute the third command

exit $exit_status           # Exit the script with the exit status of the first command
