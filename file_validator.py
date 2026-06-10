import os

ALLOWED_EXTENSIONS = [".csv", ".xlsx", ".xls", ".json"]

MAX_FILE_SIZE = 5 * 1024 * 1024


def validate_file_type(filename):

    extension = os.path.splitext(filename)[1]

    if extension.lower() not in ALLOWED_EXTENSIONS:
        raise Exception(
            "Invalid file type. Only CSV, Excel and JSON allowed.")
    return extension.lower()


def validate_file_size(size):

    if size > MAX_FILE_SIZE:
        raise Exception(
            "File too large. Max size is 5MB."
        )
    
def validate_file_not_empty(size):
    if size == 0:
        raise Exception("File is empty. Please upload a file with data.")