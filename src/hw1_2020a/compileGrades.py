import utils
from pathlib import Path
import shutil
import subprocess

PROCESS_SUCCESS = 0


def build_students_directories():
    assignments_path = Path("/home/user/work/OS_autoGrader/assignments/")

    # Create a directory for each student.
    for student_file in assignments_path.iterdir():  # iterate on all students folders!
        student_name, student_id = utils.get_student_name_id_from_file_or_dir(str(student_file))
        student_dir_path = assignments_path / f"{student_name}_{student_id}"
        try:
            student_dir_path.mkdir()
        except FileNotFoundError as e:
            print(e)
            continue
        shutil.copy2('/home/user/work/OS_autoGrader/src/hw1_2020a/os.c', student_dir_path)
        shutil.copy2('/home/user/work/OS_autoGrader/src/hw1_2020a/os.h', student_dir_path)
        # Check if copying succeeded:
        if not (student_dir_path / 'os.c').exists() or not (student_dir_path / 'os.h').exists():
            print("copying files to student dir failed.")
            continue
        # Rename files to pt.c
        pt_new_path = student_file.rename('pt.c')
        shutil.copy2(str(pt_new_path), student_dir_path)
        if not (student_dir_path / 'pt.c').exists():
            print("copying files to student dir failed.")
            continue


def compile_students_files():
    assignments_path = Path("/home/user/work/OS_autoGrader/assignments/")
    utils.open_names_csv("/home/user/work/OS_autoGrader/names.csv")  # Create the grades Excel

    # Create a directory for each student.
    for student_dir in assignments_path.iterdir():  # Example: Yuval Helman_315581819
        student_name, student_id = utils.get_student_name_id_from_file_or_dir(str(student_dir), is_dir=True)
        student_dir_path = assignments_path / f"{student_name}_{student_id}"

        with utils.working_directory(str(student_dir_path)):
            sp = subprocess.run(['gcc', '-o3', '-w', '-Wall', '-std=c11', 'os.c', 'pt.c', "-o", "tester"])
            if sp.returncode != PROCESS_SUCCESS:
                print("compilation failed for user ", student_name, "_", student_id)
                utils.write_to_grades_csv("/home/user/work/OS_autoGrader/names.csv",
                                          student_name, student_id, 0, "compilation error")
            else:
                run_test_for_user(student_dir_path, student_name, student_id)


def run_test_for_user(student_dir_path: str, student_name, student_id):
    with utils.working_directory(str(student_dir_path)):
        # with utils.StandardOutput() as stdout:
        sp = subprocess.run(['./tester'], capture_output=True, shell=True)
        if not isinstance(sp, subprocess.CompletedProcess) or sp.returncode != PROCESS_SUCCESS:
            utils.write_to_grades_csv("/home/user/work/OS_autoGrader/names.csv",
                                      student_name, student_id, 60, f"program failed while tested. returned code {sp.returncode}")
            # TODO: instead of auto 60, try to run only the "sanity-check" thingy. should be like 75 if it works.
            #       Can do that with an argument on the ./tester --full_tests/--sanity
        else:  # Tester succeed for this dude
            tester_output = sp.stdout.decode("utf-8")
            student_comments = utils.remove_two_last_lines_from_string(tester_output)
            student_grade = tester_output.split('\n')[-2]
            utils.write_to_grades_csv("/home/user/work/OS_autoGrader/names.csv",
                                      student_name, student_id, student_grade, student_comments)


if __name__ == '__main__':
    ''' Run build_Students_directories() on a directory where all the student's c-files are present.
        THen run compile_students_files() to compile and generate results csv. '''
    # build_students_directories()
    compile_students_files()
