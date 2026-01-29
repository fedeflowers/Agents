from langchain_core.tools import tool

@tool
def submit_extraction(**kwargs):
    """
    Submit the final extracted engineering data. 
    You must call this tool to finish the task.
    """
    # This function doesn't need to do anything real, it's just a signal.
    # The arguments will be captured.
    return "Extraction submitted."
