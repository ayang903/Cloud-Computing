#!/bin/bash

# Number of concurrent executions
concurrent_executions=50

cmd="python3 http-client.py -d 34.138.237.180 -p 5000 -n 100 -i 10000 -v -r 0"

for i in $(seq 1 $concurrent_executions); do
    echo "Executing instance $i..."
    ($cmd) & # Run the command in the background
done
echo "done"
wait
