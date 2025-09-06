from baml_client import b

#print(b.GenerateTaskGraph("Can you please help with localizing the given file (english) hosted in s3 to French, Spanish & German and then finally after completing the localizations inform me when done."))
#print(b.GenerateConstrainedTaskGraph("how to extend credit for a borrower"))
taskGraph = b.GenerateTaskGraph("Build the service, then run unit, integration, and security tests in parallel, and finally deploy to staging")

def printTask(task, indent=0):
    print(' '*indent + task.title)
    if task.subtasks:
        for stask in task.subtasks:
            printTask(stask, indent=indent+3)
    else:
        return


     
for task in taskGraph.tasks:
    printTask(task)

