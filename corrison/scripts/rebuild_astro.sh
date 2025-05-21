#!/bin/bash

# Log file for tracking build progress
LOG_FILE="/home/c0rrisonap1/corrison/logs/astro_rebuild.log"

# Ensure logs directory exists
mkdir -p /home/c0rrisonap1/corrison/logs

# Begin log entry
echo "---------------------------------------------" >> "$LOG_FILE"
echo "Build started at $(date)" >> "$LOG_FILE"

# Navigate to the Astro project directory
cd /home/c0rrisonap1/frontend || {
    echo "ERROR: Could not navigate to Astro project directory" >> "$LOG_FILE" 
    exit 1
}

# Run npm build
echo "Starting Astro build..." >> "$LOG_FILE"
/home/c0rrisonap1/bin/npm run build >> "$LOG_FILE" 2>&1

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Build completed successfully at $(date)" >> "$LOG_FILE"
    
    # Optional: Deploy the build (if needed)
    # Example: Copy to the web directory
    # cp -R dist/* /path/to/web/directory/
    
    exit 0
else
    echo "ERROR: Build failed at $(date)" >> "$LOG_FILE"
    
    # Send email notification only on failure
    # Uncomment and adjust the following if you want failure notifications
    # mail -s "Astro build failed" your@email.com < "$LOG_FILE"
    
    exit 1
fi