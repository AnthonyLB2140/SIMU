import os
import sys
import subprocess
import shutil



def find_and_concat_files(directory):
    # If no directory is provided, use the current working directory
    if not directory:
        directory = os.getcwd()

    # Create the backup directory path
    backup_directory = os.path.join(directory, 'backup')

    # Check if the backup directory exists
    if not os.path.exists(backup_directory):
        # print "No 'backup' directory found in '{directory}'."
        print "No 'backup' directory found in '{directory}'.".format(directory=directory)
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
            concat_script = ["python", "concat.py", backup_file, txt_file]
            print "python concat.py {backup_file} {txt_file}".format(backup_file=backup_file, txt_file=txt_file)
            # Call the 'concat.py' script with the appropriate arguments
            subprocess.call(concat_script)
        else:
            # print "No backup file found for '{txt_file}'."
            print "No backup file found for '{txt_file}'.".format(txt_file=txt_file)
            print "backup_file: ".format(backup_file=backup_file)
            copy_file_path = backup_file + ".copy"
            shutil.copyfile(txt_file, copy_file_path)
            
    # Create the 'Manoeuver' subdirectory in the working directory
    manoeuver_directory = os.path.join(directory, 'Manoeuver')
    try:
        os.makedirs(manoeuver_directory)
    except OSError:
        pass

    # Move files ending with 'POSITION.TXT' or 'ATTITUDE.TXT' to the 'Manoeuver' directory
    position_attitude_files = [
        file for file in os.listdir(directory)
        if file.endswith(('POSITION.TXT', 'ATTITUDE.TXT')) and os.path.isfile(os.path.join(directory, file))
    ]

    for file in position_attitude_files:
        source_path = os.path.join(directory, file)
        target_path = os.path.join(manoeuver_directory, file)
        shutil.move(source_path, target_path)

    # Move files ending with '.copy' from the 'backup' directory to the working directory
    copy_files = [
        file for file in os.listdir(backup_directory)
        if file.endswith('.copy') and os.path.isfile(os.path.join(backup_directory, file))
    ]

    for file in copy_files:
        source_path = os.path.join(backup_directory, file)
        target_path = os.path.join(directory, file)
        shutil.move(source_path, target_path)

    # Call the 'rename.py' script
    rename_script = ["python", "rename.py"]
    subprocess.call(rename_script)


if __name__ == '__main__':
    # Check if a directory argument is provided
    directory_arg = sys.argv[1] if len(sys.argv) > 1 else None

    # Call the function to find and manipulate files
    find_and_concat_files(directory_arg)

