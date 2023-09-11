#!/bin/bash

job_v=1.0

# Directory containing the app folders
APPS_DIR='./Job Designs/'

# Generate a list of app folders, excluding "lib"
APPS=($(find "$APPS_DIR" -maxdepth 1 -type d ! -name "lib" ! -printf "%f\n" | tail -n +2))
for element in "${APPS[@]}"; do
    echo "FOUND $element"
done
echo ---------------


#Get my approval :

while true; do
    read -p "Do you want to continue? (y/n): " choice
    case "$choice" in
        [Yy])
            echo "Continuing..."
            break
            ;;
        [Nn])
            echo "Exiting."
            exit
            ;;
        *)
            echo "Invalid input. Please enter 'y' or 'n'."
            ;;
    esac
done




# Loop through app names
for app in "${APPS[@]}"; do
    lowercase_app="${app,,}"
    echo "Building container for $lowercase_app..."
    name="localhost:5000/$lowercase_app:$job_v"
    docker build -t $name . -f ./Dockerfile.template --build-arg APP_NAME="$app"
    docker push $name
done

echo "All containers built!"