import os
import re
import stat
import subprocess as sp
import sys
from pathlib import Path
from time import sleep
import logging

from osCheckers import utils
from osCheckers.hw3_2020a.hw3_utils import compile_static_files, uzip_and_build_test_environment, \
    compile_student_files, copy_scripts_to_user, delete_stud_dir_zips_folder


def read_message(file_path_to_exe, device_path_Name, chID, stud_logger, is_user_file=True):
    """
    @param is_user_file - a boolean that specifies if the function will use the user's message_reader code, or mine.
    @param file_path_to_exe - the path to the user's directory
    @param log_fd - a file descriptor to throw output, for later debugging
    @param dev_name - the device name to read from
    @param chID - the chanel to read from within the device
    @return: 0 on success. 1 else
    """
    try:
        with utils.currentWorkingDir(file_path_to_exe):
            if is_user_file:
                p = sp.run(args=['./message_reader', device_path_Name, str(chID)], capture_output=True, text=True)
            else:
                p = sp.run(args=['./message_reader_true', device_path_Name, str(chID)], capture_output=True, text=True)
    except sp.SubprocessError as e:
        stud_logger.info(f"read_message failed: {e}")
        raise sp.SubprocessError

    return p.stdout


def send_message(file_path_to_exe, device_path_Name, write_mode, chID, msgStr, stud_logger, is_user_file=True):
    try:
        with utils.currentWorkingDir(file_path_to_exe):
            if is_user_file:
                p = sp.run(args=['./message_sender', device_path_Name, str(chID), msgStr])
            else:
                p = sp.run(args=['./message_sender_true', device_path_Name, str(chID), msgStr])
    except sp.SubprocessError as e:
        stud_logger.info(f"send_message failed: {e}")
        raise sp.SubprocessError


TEST_POINTS_REDUCTION = 2  # change this to whatever would work with the tests
MINOR_POINT_REDUCTION = 1
POINTS_REDUCTION_BUG = 5
POINTS_SENDER_DOESNT_WORK = 10
OVERWRITE_MODE, APPEND_MODE = 0, 1  # Don't change values. these integers are the ones needed.


def message_reader_text_test(stud_logger, file_path_to_exe, dev_name):
    test_errors_str = ""
    points_to_reduct = 0
    minor_num = 250
    try:
        test_output_name = file_path_to_exe + 'outputUserReader.txt'
        with open(test_output_name, 'w') as test_log:  # ./assignments/Yuval Checker_999999999/output1.txt
            # Check If the user's message_reader is valid (Most of them aren't...) :(
            if send_message(file_path_to_exe, dev_name, OVERWRITE_MODE, minor_num, "messageToBeRead", stud_logger, is_user_file=False) == 1:
                test_errors_str += "message_sender doesn't work. "
                points_to_reduct += TEST_POINTS_REDUCTION
            # Read with user's message_reader
            if read_message(True, file_path_to_exe, dev_name, 1, stud_logger) == 1:
                test_errors_str += "message_reader output not as requested. "
                points_to_reduct += TEST_POINTS_REDUCTION
    except OSError as e:
        print("OSError First One: ", e)

    return points_to_reduct, test_errors_str


def run_tests(stud_logger, stud_dir_path, device_path_name, minor_num):
    points_to_reduct = 0
    test_errors_str = ""

    tests_arguments = [
        {'ch_id': 10, 'message': "10Hello hi", 'minor': minor_num, 'mode': OVERWRITE_MODE, 'expected': '10Hello hi'},
        # ./tests/output0.txt
        {'ch_id': 10, f'message': "10Overwritten", 'minor': minor_num, 'mode': OVERWRITE_MODE, 'expected': '10Overwritten'},
        # ./tests/output2.txt
        {'ch_id': 20, 'message': "20NiceString", 'minor': minor_num, 'mode': APPEND_MODE, 'expected': '20NiceString'},
        # ./tests/output3.txt
        {'ch_id': 20, 'message': "20OverWritten", 'minor': minor_num, 'mode': APPEND_MODE, 'expected': '20OverWritten'},
        # ./tests/output4.txt
        {'ch_id': 10, 'message': "10AgainOverwritten", 'minor': minor_num, 'mode': OVERWRITE_MODE, 'expected': '10AgainOverwritten'},
        # ./tests/output5.txt
    ]
    for test_number, test_args in enumerate(tests_arguments):
        try:
            send_message(stud_dir_path, device_path_name, test_args['mode'],test_args['ch_id'],
                         test_args['message'], stud_logger, is_user_file=True)
        except sp.SubprocessError as e:
            stud_logger.info(f"Send message failed on test {test_number} and user {stud_dir_path}: {e}")
            points_to_reduct += TEST_POINTS_REDUCTION
            test_errors_str += "message_sender failed. "
            continue

        try:
            user_output = read_message(stud_dir_path, device_path_name, test_args['ch_id'], stud_logger,
                                       is_user_file=True)
        except sp.SubprocessError as e:
            stud_logger.info(f"Read message failed on test #{test_number}, user {stud_dir_path} : {e}")
            points_to_reduct += POINTS_REDUCTION_BUG
            test_errors_str += "message_reader failed. "
            continue

        expected_output = test_args['expected']
        stud_logger.debug(f'user string: {user_output}. true string: {expected_output}')
        if user_output == expected_output:
            stud_logger.info(f"test {test_number} succeed\n")
        elif expected_output in user_output:
            points_to_reduct += MINOR_POINT_REDUCTION
            test_errors_str += f"test {test_number} failed. user_output has more characters then expected "
            stud_logger.info(f"test {test_number} failed. user_output contained in expected_output. not equal")
        else:
            points_to_reduct += TEST_POINTS_REDUCTION
            test_errors_str += f"test {test_number} failed. "
            stud_logger.info(f"test {test_number} failed\n")

    return points_to_reduct, test_errors_str


def remove_char_device(stud_logger, device_path_name, check_exit_code=False):
    try:
        ret = os.system(f'sudo rm -f {device_path_name}')
    except OSError as e:
        stud_logger.info("remove char device failed", e)
        return 1

    return 0


def load_module_and_read_maj_number(file_path_to_exe, log_fd):
    """ Was usefull in 2019b. in 2020A the major number is always 240 so kept here for future use """
    dmesg_file_path = file_path_to_exe + 'dmesg_file.txt'
    MajorNum_file_path = file_path_to_exe + 'dmesg_file.txt'
    majorNumber = 0

    try:
        p = sp.Popen(args=['./bash_insmod'],
                     cwd=file_path_to_exe,
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if (p.returncode == 1):
            print("insmod failed for user: ", file_path_to_exe)
            return 1, -1
    except:
        print("3:")
        return 1, -1

    sleep(1)  # DEBUG. wait for kprint to finish before reading the majorNumber

    last_line = 0  # DEBUG: erase and merge 5 and 6
    try:
        with open("/var/log/syslog", 'r') as dmesg_log:
            log_lines_list = dmesg_log.readlines()
            if (log_lines_list):
                last_line = log_lines_list[len(log_lines_list) - 1]
                # Split the message that the student wrote, then fetch the first number with regex
                studentKernLogMessage = last_line.split(']')[1]
                print(re.findall(r'\d+', studentKernLogMessage))  # debug
                majorNumber = (re.findall(r'\d+', studentKernLogMessage)[0])

    except OSError as e:
        print("Fetching MajorNumber Failed: ", e)  # DEBUG
        return 1, -1
    except:
        print("4;")  # DEBUG
        return 1, -1

    print("load module success")  # DEBUG
    return 0, majorNumber


def module_exists():
    '''
        :returns 'True' if module exists. 'False' if it doesn't exist.
    '''
    try:
        p = sp.Popen(args=['lsmod | grep message_slot'], )
        p.wait()
        if (p.returncode == 1):
            return True
        else:
            return False
    except OSError as e:
        print("OSError module_Exists: ", e)
        return True


def load_module(exe_files_path, stud_logger, super_log):
    try:
        with utils.currentWorkingDir(exe_files_path):
            s = sp.run(["sudo", "insmod", "./message_slot.ko"], check=True)
    except sp.SubprocessError as e:
        stud_logger.info("load_module failed", e)
        super_log.debug(f"load_module failed: {exe_files_path}: {e}")
        raise sp.SubprocessError

    stud_logger.info("load_module success")
    super_log.debug(f"load_module success by : {exe_files_path}")
    return 0


def remove_module(exe_files_path=None, stud_logger=None):
    try:
        s = sp.run(["sudo", "rmmod", "message_slot"], check=True)
        if s.returncode == 1:
            print("rmmod failed for user:", exe_files_path)
            return 1  # if I can't remove the Module, I shouldn't run the other directories until its off
    except sp.SubprocessError as e:
        try:
            stud_logger.info("remove_module failed", e)
        except Exception:
            pass
        return 1

    try:
        stud_logger.info("remove_module success")
    except Exception:
        pass
    return 0


def build_tests_env(exe_files_path, stud_logger, super_log):
    """ Checks the tests on 1 student
    Returns the number of points needed to reduct from the student
    @param file_path_to_exe:
    @param stud_logger:
    @return: (Points_to_deduct, test_errors_str) == (100>=int>=0, String)
    """

    remove_module()
    try:
        load_module(exe_files_path, stud_logger, super_log)
    except sp.SubprocessError as e:
        stud_logger.info("load_module failed")
        raise sp.SubprocessError

    MINOR_NUMBER = 20
    dev_name = "charDevice"
    device_path_name = f"/dev/tester/{dev_name}{exe_files_path.stem}"  # student name

    # create a character device
    remove_char_device(stud_logger, device_path_name, check_exit_code=False)
    MAJOR_NUMBER = 240
    try:
        with utils.currentWorkingDir(exe_files_path):
            s = sp.run(["sudo", "mknod", "-m", "777", device_path_name, "c", str(MAJOR_NUMBER), str(MINOR_NUMBER)],
                       check=True)
    except sp.SubprocessError as e:
        stud_logger.info("insmod failed", e)
        raise sp.SubprocessError

    return device_path_name, MINOR_NUMBER


def clean_tests_env(file_path_to_exe, device_path_name, stud_logger):
    remove_char_device(stud_logger, device_path_name)
    try:
        remove_module(file_path_to_exe, stud_logger)
    except Exception as e:
        stud_logger.info(f"error removing module on {file_path_to_exe}")


def iterate_students_directories(super_log):
    assignments_dir = Path("/home/user/work/OS_autoGrader/assignments/")

    for student_dir in assignments_dir.iterdir():
        splitted_filename = student_dir.name.split("_")
        student_name = splitted_filename[0] + " " + splitted_filename[1]
        student_id = splitted_filename[2]

        stud_dir_path = assignments_dir / student_dir  # ->  ./assignments/Yuval Checker_999999999/
        log_name_path = stud_dir_path / 'testlog.log'

        stud_logger = utils.setup_logger(name='student logger', log_file=log_name_path, mode='w')
        super_log.info(f'Tests Initialize for student {student_name}_{student_id}')

        if compile_student_files(stud_dir_path, stud_logger) != 0:
            stud_logger.info(f'Compilation phase failed for: {student_name}_{student_id}')
            super_log.info(f'Compilation phase failed for: {student_name}_{student_id}')
            ############################################################################
            utils.write_to_grades_csv(student_name, student_id, 0, 'Compilation error',
                                      "/home/user/work/OS_autoGrader/last_no_compile.csv")
            delete_stud_dir_zips_folder(stud_dir_path)
            ############################################################################

            utils.write_to_grades_csv(student_name, student_id, 0, 'Compilation error')
            continue
        stud_logger.info(f'Compilation Success')
        super_log.info(f'Compilation Success for: {student_name}_{student_id}')

        sleep(0.2)  # DEBUG
        try:
            device_path_name, minor_num = build_tests_env(stud_dir_path, stud_logger, super_log)
            super_log.info(f'build_tests_env suceed for: {student_name}_{student_id}')
        except Exception as e:
            stud_logger.info("Building Environment failed")
            utils.write_to_grades_csv(student_name, student_id, 60, "insmod \ mknod failed")
            remove_module(stud_dir_path, stud_logger)
            continue

        try:
            copy_scripts_to_user(stud_dir_path, stud_logger)
            points_to_reduct, test_errors_str = \
                run_tests(stud_logger, stud_dir_path, device_path_name, minor_num)
            student_GRADE = 100 - points_to_reduct
            stud_logger.info(f"{student_name}_{student_id} grade: {student_GRADE}")
            super_log.info(f"{student_name}_{student_id} grade: {student_GRADE}")
            utils.write_to_grades_csv(student_name, student_id, student_GRADE, test_errors_str)
            ############################################################################
            utils.write_to_grades_csv(student_name, student_id, student_GRADE, test_errors_str,
                                      "/home/user/work/OS_autoGrader/last.csv")
            delete_stud_dir_zips_folder(stud_dir_path)
            ############################################################################
            stud_logger.info(f'Tests completed for student {student_name}_{student_id}')
        except Exception as e:
            stud_logger.info(f'Exception for student {student_name}_{student_id}: {e}')
            super_log.info(f'Exception for student {student_name}_{student_id}: {e}')
        finally:
            clean_tests_env(stud_dir_path, device_path_name, stud_logger)


def main():
    # Highest level file logger
    super_logger = utils.setup_logger(name='hw3 logger', log_file='hw3.log')
    super_logger.info('Log Initialize!')

    utils.open_names_csv()

    # compile_static_files(super_logger)
    # uzip_and_build_test_environment(super_logger)
    iterate_students_directories(super_logger)

    super_logger.info("Done")


if __name__ == '__main__':
    main()
