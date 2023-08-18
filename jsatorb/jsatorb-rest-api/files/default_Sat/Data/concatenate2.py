import os
import sys
import subprocess

def find_and_concat_files(directory):
    # If no directory is provided, use the current working directory
    if not directory:
        directory = os.getcwd()

    # Create the backup directory path
    backup_directory = os.path.join(directory, 'backup')

    # Check if the backup directory exists
    if not os.path.exists(backup_directory):
        print(f"No 'backup' directory found in '{directory}'.")
        return

    # Get a list of .txt files in the specified directory
    txt_files = [
        file for file in os.listdir(directory)
        if file.lower().endswith('.txt') and os.path.isfile(os.path.join(directory, file))
    ]

    # Iterate over each .txt file
    for txt_file in txt_files:
        # Construct the full path to the backup file
        backup_file = os.path.join(backup_directory, txt_file)

        # Check if the backup file exists
        if os.path.exists(backup_file):
            # Prepare the command to call the 'concat.py' script
            concat_script = ["python", "concat.py", txt_file, backup_file]

            # Call the 'concat.py' script with the appropriate arguments
            subprocess.run(concat_script)
        else:
            print(f"No backup file found for '{txt_file}'.")

if __name__ == '__main__':
    # Check if a directory argument is provided
    directory_arg = sys.argv[1] if len(sys.argv) > 1 else None

    # Call the function to find and concatenate files
    find_and_concat_files(directory_arg)

