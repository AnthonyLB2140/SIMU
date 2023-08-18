# Anthony Le Batteux EAE 130723
import os

directory = os.getcwd()

for filename in os.listdir(directory):
    if filename.endswith(".copy"):
        new_filename = filename[:-5]  # Remove the ".copy" extension
        new_path = os.path.join(directory, new_filename)
        old_path = os.path.join(directory, filename)
        os.rename(old_path, new_path)
       # print(f"Renamed {filename} to {new_filename}")
        print("Renamed {filename} to {new_filename}".format(filename=filename, new_filename=new_filename))

