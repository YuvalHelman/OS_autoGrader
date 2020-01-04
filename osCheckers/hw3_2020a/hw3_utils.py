import subprocess as sp
import os
import stat
import logging
from pathlib import Path
import zipfile as zip
from osCheckers import utils


def compile_static_files(gen_log):
    try:
        s = sp.run(['gcc', '-o3', '-w', '-Wall', '-std=c11', "message_reader_true.c", '-o', "message_reader_true"],
                   check=True)
        os.chmod(f"./message_reader_true",
                 stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)  # DEBUG: testing this
    except sp.SubprocessError as e:
        print("Reader compile failed", e)
        return 1

    try:
        s = sp.run(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_sender_true.c", "-o", "message_sender_true"],
                   check=True)
        os.chmod(f"./message_sender_true",
                 stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)  # DEBUG: testing this
    except sp.SubprocessError as e:
        print("Sender compile failed", e)
        return 1

    return 0


def uzip_and_build_test_environment(super_log, path_from=Path("/home/user/work/OS_autoGrader/zip_files/"),
                                    path_to=Path("/home/user/work/OS_autoGrader/assignments/")):
    assignments_dir = path_to

    for student_zipped in path_from.iterdir():
        splitted_filename = student_zipped.name.split("_")
        student_first_name = splitted_filename[0].split(" ")[0]
        student_last_name = (splitted_filename[0].split(" "))[1]
        student_id = splitted_filename[4]

        student_dir_path = assignments_dir / f"{student_first_name}_{student_last_name}_{student_id}"
        try:
            student_dir_path.mkdir()
        except FileNotFoundError as e:
            print(f"directory creation failed for student: {student_first_name}_{student_last_name}_{student_id}", e)
            super_log.info(
                f"directory creation failed for student: {student_first_name}_{student_last_name}_{student_id}", e)
            continue

        logger_path = student_dir_path / 'testlog.log'
        stud_logger = utils.setup_logger(name='test log', log_file=logger_path, mode='w')

        with zip.ZipFile(student_zipped, 'r') as ref:
            ref.extractall(path=student_dir_path)
        # student_zipped.unlink()


def compile_student_files(exe_files_path, stud_logger):
    try:
        with utils.currentWorkingDir(exe_files_path):
            s = sp.run(["gcc", "-O3", "-Wall", "-std=c11", "message_reader.c", "-o", "message_reader"],
                       check=True)
            os.chmod(f"./message_reader",
                     stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
    except Exception as e:
        stud_logger.info("message_reader compile failed", e)
        return 1

    try:
        with utils.currentWorkingDir(exe_files_path):
            s = sp.run(["gcc", "-O3", "-Wall", "-std=c11", "message_sender.c", "-o", "message_sender"],
                       check=True)
            os.chmod(f"./message_sender",
                     stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)
    except Exception as e:
        stud_logger.info("message_reader compile failed", e)
        return 1

    try:
        s = sp.run(["make"],
                   cwd=exe_files_path, check=True)
        if s.returncode != 0:  # check if compilation works
            print("Make failed")  # DEBUG
            return 1
    except Exception as e:
        print("make compile failed", e)
        return 1

    try:  # Check if the .ko file was created
        if not os.path.exists(exe_files_path / "message_slot.ko"):
            print(".ko file missing")  # DEBUG
            return 1
    except Exception as e:
        print("OSError compile_files: ", e)
        return 1

    return 0


def copy_scripts_to_user(student_dir, logger,
                         from_path='/home/user/work/OS_autoGrader/osCheckers/hw3_2020a'):
    """ Copy bash scripts from /src to file_path_to_exe """
    try:
        ret = os.system(f'sudo cp -p {from_path}/message_reader_true {student_dir}')
    except OSError as e:
        logger.info(f"copy message_reader_true failed: {e}")

    try:
        ret = os.system(f'sudo cp -p {from_path}/message_sender_true {student_dir}')
    except OSError as e:
        logger.info(f"copy message_reader_true failed: {e}")
