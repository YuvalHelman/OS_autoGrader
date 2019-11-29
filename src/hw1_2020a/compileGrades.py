import utils
from pathlib import Path
import shutil
import subprocess


def compile_files():
    assignments_path = Path("/home/user/work/OS_autoGrader/assignments/")

    # Create a directory for each student.
    for student_file in assignments_path.iterdir():  # iterate on all students folders!
        student_name, student_id = utils.get_student_name_id_from_c_file(str(student_file))
        student_dir_path = assignments_path / f"{student_name}_{student_id}"
        try:
            student_dir_path.mkdir()
        except FileNotFoundError as e:
            print(e)
            print("Im here 1")  # DEBUG
            continue
        shutil.copy2('/home/user/work/OS_autoGrader/src/hw1_2020a/os.c', student_dir_path)
        shutil.copy2('/home/user/work/OS_autoGrader/src/hw1_2020a/os.h', student_dir_path)
        # Check if copying succeeded:
        if not (student_dir_path / 'os.c').exists() or not (student_dir_path / 'os.h').exists():
            print("copying files to student dir failed.")
            print("Im here 1")  # DEBUG
            continue
        # Rename files to pt.c
        pt_new_path = student_file.rename('pt.c')
        shutil.copy2(str(pt_new_path), student_dir_path)
        if not (student_dir_path / 'pt.c').exists():
            print("copying files to student dir failed.")
            print("Im here 2")  # DEBUG
            continue
        sp = subprocess.run(['gcc', '-o3', '-Wall', '-std=c11', "os.c", "pt.c", "-o", "tester"])
        if sp.returncode == 1:
            print("compilation failed for user ", student_name, "_", student_id)


if __name__ == '__main__':
    compile_files()
