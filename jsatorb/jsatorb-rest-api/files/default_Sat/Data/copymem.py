# Anthony Le Batteux EAE 130723
import os
import shutil
import sys

def backup_files(source_dir):
    # Create the backup directory (overwrite if it already exists)
    backup_dir = os.path.join(source_dir, "backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        #shutil.rmtree(backup_dir)  I need to change this otherwise if backup is not empty it will throuw an error
        #shutil.rmtree(backup_dir, ignore_errors=True)
    

    # Get the list of files in the source directory
    files = os.listdir(source_dir)

    # Copy each .TXT file to the backup directory
    for file in files:
        if file.endswith(".TXT"):
            source_path = os.path.join(source_dir, file)
            backup_path = os.path.join(backup_dir, file)
            shutil.copy2(source_path, backup_path)
         #  print(f"Copied {source_path} to {backup_path}")
            print("Copied {} to {}".format(source_path, backup_path))

if __name__ == "__main__":
    # Check if the source directory is provided as a command-line argument
    if len(sys.argv) < 2:
        source_directory = os.getcwd()  # Use the current working directory
    else:
        source_directory = sys.argv[1]

    backup_files(source_directory)

