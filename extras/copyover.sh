#!/bin/bash

# Check if at least two arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <file_pattern>... <destination_directory>"
    exit 1
fi

# The last argument is the destination directory
dest_dir="${!#}"

# Create the destination directory if it doesn't exist
mkdir -p "$dest_dir"

# Loop through each file pattern
for pattern in "$@"; do
    # Skip the last argument (the destination directory)
    if [ "$pattern" == "$dest_dir" ]; then
        continue
    fi

    # Loop through each file that matches the pattern
    for src_file in $pattern; do
        # Check if the file exists (in case the pattern doesn't match any file)
        if [ -f "$src_file" ]; then
            filename=$(basename "$src_file")
            dest_file="$dest_dir/$filename"
            
            # Check if the destination file exists
            if [ -f "$dest_file" ]; then
                # Get the sizes of the source and destination files
                src_size=$(stat -c%s "$src_file")
                dest_size=$(stat -c%s "$dest_file")
                
                # Compare the file sizes and copy if the source file is larger
                if [ "$src_size" -gt "$dest_size" ]; then
                    cp "$src_file" "$dest_dir"
                    echo "Copied $src_file to $dest_dir (source is larger)"
                else
                    echo "Skipped $src_file (destination is larger or equal in size)"
                fi
            else
                # If the destination file does not exist, copy the file
                cp "$src_file" "$dest_dir"
                echo "Copied $src_file to $dest_dir (destination file does not exist)"
            fi
        fi
    done
done
