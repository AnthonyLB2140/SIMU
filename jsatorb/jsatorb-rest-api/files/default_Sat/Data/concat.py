# Anthony Le Batteux EAE 130723
import argparse
import shutil

def find_previous_time(lines, target_time):
    # Find the index of the line with time just before the target time
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i]
        line_elements = line.split()
        if len(line_elements) >= 2:     # Skip empty lines
            try:
                # Time = float(line_elements[1])
                time = float(line_elements[1])+(86400*float(line_elements[0]))
                if time < target_time and abs(target_time-time)<=3600:     ## Warning here 10 is the time step ##
                    return i
            except ValueError:
                continue
    return -1


def merge_files(file1_path, file2_path):
    # Create a copy of file1
    copy_file_path = file1_path + ".copy"
    shutil.copyfile(file1_path, copy_file_path)

    with open(copy_file_path, 'r') as file1, open(file2_path, 'r') as file2:
        lines1 = file1.readlines()  # Read all lines from the copy file
        metadata1 = []
        data1 = []

        # Separate metadata and data lines from file1
        for line in lines1:
            if line.strip() and line[0].isdigit():
                data1.append(line)
            else:
                metadata1.append(line)

        lines2 = file2.readlines()  # Read all lines from file2
        metadata2 = []
        data2 = []
        for line in lines2:
            if line.strip() and line[0].isdigit():
                data2.append(line)
            else:
                metadata2.append(line)

    if not data2:
        print("No data found in file2.")
        return

    # Find the previous time index in data1 based on the target time from data2
    # Previous_time_index = find_previous_time(data1, float(data2[0].split()[1]))
    previous_time_index = find_previous_time(data1, (float(data2[0].split()[1]) + ( 86400 * float(data2[0].split()[0]))) )# 18/07/23 Correction we sum the date and time to avoid error if simulation is over two days
    if previous_time_index != -1:
        # Merge metadata1, data1, and data2 into a single list
        merged_lines = metadata1 + data1[:previous_time_index+1] + data2

        with open(copy_file_path, 'w') as copy_file:
            copy_file.writelines(merged_lines)

        print("Files merged successfully!")
    else:
        print("Previous time not found in the first file.")
        merged_lines = metadata2 + data2
        with open(copy_file_path, 'w') as copy_file:
            copy_file.writelines(merged_lines)
        print("New file returned..")
# Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("file1", help="path to the first file (OEM1.TXT)")
parser.add_argument("file2", help="path to the second file (OEM2.TXT)")
args = parser.parse_args()

# Usage example:
file1_path = args.file1
file2_path = args.file2
#if file1_path == file2_path:
    
merge_files(file1_path, file2_path)

