import os 



def deleteFile(directory):
    print("MEMxterminator called from "+directory)
    for fileName in os.listdir(directory):
        filePath = os.path.join(directory, fileName)
        if fileName.endswith(".TXT"):
            try :
                tmpName=fileName
                os.remove(filePath)
                print(tmpName+" was deleted ...")

            except : 
                print(fileName+" Could not be deleted ...")
        elif os.path.isdir(filePath):
            try :
                deleteFile(filePath)
            except :
                print("Error could not execute deleteFile in "+filePath)


        
currentWorkingDirectory = os.getcwd()
deleteFile(currentWorkingDirectory)


