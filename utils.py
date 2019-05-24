import csv
import os
import zipfile as zip

def open_names_csv():
    # Open a new names.csv for writing the results.
    with open(r'names.csv', 'w') as csvfile:
        fieldnames = ['name', 'id', 'grade', 'comment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writerow({'name': 'FULL NAME', 'id': 'ID', 'grade': 'GRADE', 'comment': 'COMMENT'})



def write_to_csv(name, id, grade, comment_string):
    with open(r'names.csv', 'a') as csvfile:
        fieldnames = ['name', 'id', 'grade', 'comment']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writerow({'name': name, 'id': id, 'grade': grade, 'comment': comment_string})


def zip_out_folders():
    directory_str = "./zip_files/"

    for file in os.listdir(directory_str):
        splitted_filename = file.split("_")
        print(file)  # DEBUG
        # Get FirstName_LastName_ID string
        full_stud_name = splitted_filename[0].split(" ")[0] + "_" +\
                         splitted_filename[0].split(" ")[0] + "_" + splitted_filename[4]
        print(full_stud_name)  # DEBUG

        # Create a new folder with the students name_ID
        directory_to_extract_to = "./assignments/" + full_stud_name
        os.mkdir(directory_to_extract_to, 0o755)  # linux - mkdir , windows - md
        # Zip the files into the student directory
        zip_ref = zip.ZipFile("./zip_files/" + file, 'r')
        zip_ref.extractall(directory_to_extract_to)
        zip_ref.close()


def build_comments(is_mem_leak, is_test_errors):
    student_comment = 'No Errors detected'

    if (is_mem_leak is True and is_test_errors is False):
        student_comment = 'Some memory leaks detected'
    if (is_mem_leak is False and is_test_errors is True):
        student_comment = 'Not all tests were successful'
    if (is_mem_leak is True and is_test_errors is True):
        student_comment = 'Not all tests were successful + Some memory leaks detected'

    return student_comment

if __name__ == '__main__':
        zip_out_folders()
        # compile_files_and_check_tests()
        print("hi")
