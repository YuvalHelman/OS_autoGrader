import csv
import os
import sys
import zipfile as zip
import contextlib
from pathlib import Path
from io import StringIO
import logging


def open_names_csv(full_path_dir="/home/user/work/OS_autoGrader/names.csv"):  # A full path to the csv file
    """ Open a new names.csv for writing the results.
        full_path_dir - A full path to the csv file """
    with open(full_path_dir, 'w') as csvfile:
        fieldnames = ['name', 'id', 'grade', 'comment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writerow({'name': 'FULL NAME', 'id': 'ID', 'grade': 'GRADE', 'comment': 'COMMENT'})


def write_to_grades_csv(name, id, grade, comment_string,
                        full_path_dir="/home/user/work/OS_autoGrader/names.csv"):
    """ full_path_dir - A full path to the csv file """
    with open(full_path_dir, 'a') as csvfile:
        fieldnames = ['name', 'id', 'grade', 'comment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writerow({'name': name, 'id': id, 'grade': grade, 'comment': comment_string})


def zip_out_folders():
    directory_str = "./zip_folders/"
    full_stud_name = ""
    count = 0
    try:
        for file in os.listdir(directory_str):
            splitted_filename = file.split("_")
            if splitted_filename[0] != ".gitignore":
                print(file)  # DEBUG
                # Get FirstName_LastName_ID string
                full_stud_name = splitted_filename[0].split(" ")[0] + "_" + \
                                 splitted_filename[0].split(" ")[1] + "_" + splitted_filename[4]

                # Create a new folder with the students name_ID
                directory_to_extract_to = "./assignments/" + full_stud_name
                os.mkdir(directory_to_extract_to, 0o755)  # linux - mkdir , windows - md
                # Zip the files into the student directory
                zip_ref = zip.ZipFile("./zip_folders/" + file, 'r')
                zip_ref.extractall(path=directory_to_extract_to)
                zip_ref.close()
                count += 1
        print("num of zips: {}".format(count))
    except OSError as e:
        print("Error zipping files. changes not reverted")
    except:
        print("zipping got stuck on: ", full_stud_name)


def build_comments(is_mem_leak, is_test_errors):
    student_comment = 'No Errors detected'

    if is_mem_leak is True and is_test_errors is False:
        student_comment = 'Some memory leaks detected'
    if is_mem_leak is False and is_test_errors is True:
        student_comment = 'Not all tests were successful'
    if is_mem_leak is True and is_test_errors is True:
        student_comment = 'Not all tests were successful + Some memory leaks detected'

    return student_comment


def get_student_name_id_from_file_or_dir(file_name: str, is_dir=False):
    """ returns a tuple of (name, id) given a student file_name in hw1's C file.
        Example: Yuval Helman_24284_assignsubmission_file_207890252_2961_368216201_55409_1
            if is_dir==True, then the path is: fullpath/Yuval Helman__315581819 """
    student_file_name = file_name.split("/")[-1]
    split_file_name = student_file_name.split("_")
    if is_dir is False:
        return split_file_name[0], split_file_name[4]
    else:
        return split_file_name[0], split_file_name[1]


@contextlib.contextmanager
def currentWorkingDir(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(str(path))
    try:
        yield
    finally:
        os.chdir(str(prev_cwd))


class StandardOutput:

    def __enter__(self):
        self.newstdout = StringIO()
        sys.stdout = self.newstdout
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = sys.__stdout__

    @property
    def value(self):
        return self.newstdout.getvalue()


def remove_two_last_lines_from_string(s):
    return "\n".join(s.split("\n")[:-2])


def setup_logger(name, log_file, level=logging.INFO, mode='w', print_to_stdout=True):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file, mode=mode)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    if print_to_stdout:
        logger.addHandler(logging.StreamHandler(sys.stdout))  # hide to stop printing to stdout

    return logger


if __name__ == '__main__':
    if len(sys.argv) > 1:
        argStr = sys.argv[1]
        if argStr == "zip":
            zip_out_folders()
            print("zipping completed")
