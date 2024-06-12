#!/bin/bash

# Initialize a variable to store the previous output
prev_output=""

while true; do
    # Get the current output of ps aux | grep hcx
    current_output=$(ps -aux | grep hcx)

    # Compare the current output with the previous output
    if [ "$current_output" != "$prev_output" ]; then
        # If they are different, print the current output
        clear  # Clear the screen before printing
        echo "$current_output"
        # Update the previous output to the current output
        prev_output="$current_output"
    fi

    # Wait for a while before checking again
    sleep 1
done
