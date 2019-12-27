import os
import re
import stat
import subprocess as sp
import sys
from pathlib import Path
from time import sleep
import logging

from osCheckers import utils
from osCheckers.hw3_2020a.hw3_utils import compile_static_files, uzip_and_build_test_environment,\
    compile_student_files, copy_scripts_to_user

p = Path(__file__).resolve()


'''
@param is_user_file - a boolean that specifies if the function will use the user's message_reader code, or mine.
@param file_path_to_exe - the path to the user's directory
@param log_fd - a file descriptor to throw output, for later debugging
@param dev_name - the device name to read from
@param chID - the chanel to read from within the device
@return: 0 on success. 1 else
'''


def read_message(is_user_file, file_path_to_exe, log_fd, device_path_Name, chID, output_fd):
    try:
        if is_user_file:  # Using the user's "Message reader"

            p = sp.Popen(args=['./message_reader', device_path_Name, str(chID)],
                         # Not useful.. as most students print extra junk in addition to the needed text... in different ways..
                         cwd=file_path_to_exe,
                         stdout=output_fd, stderr=log_fd)
            p.wait()
        else:
            p = sp.Popen(args=['./message_reader_true', device_path_Name, str(chID)],
                         cwd=file_path_to_exe,
                         stdout=output_fd, stderr=log_fd)
            p.wait()
    #  if (p.returncode != 0):
    #     return 1
    except OSError as e:
        print("read_message failed: ", e)
        return 1

    return 0


def send_message(is_user_file, file_path_to_exe, log_fd, device_path_Name, write_mode, chID, msgStr):
    try:
        if is_user_file:  # Using the user's "Message Sender"
            p = sp.Popen(args=['./message_sender', device_path_Name, str(write_mode), str(chID), msgStr],
                         cwd=file_path_to_exe,
                         stdout=log_fd, stderr=log_fd)
            p.wait()
            # if (p.returncode != 0):
            #     return 1
        else:
            p = sp.Popen(args=['./message_sender_true', device_path_Name, str(write_mode), str(chID), msgStr],
                         cwd=file_path_to_exe,
                         stdout=log_fd, stderr=log_fd)
            p.wait()
    except OSError as e:
        print("send_message failed: ", e)
        return 1

    return 0


def create_char_device(file_path_to_exe, log_fd, majorNumber, minorNumber, device_path_Name):
    # deviceUniqueIdentifer = file_path_to_exe.split("/")[-2] # Student Name
    # device_path_Name ="/dev/{}{}".format(dev_name, deviceUniqueIdentifer)
    # print(device_path_Name) # DEBUG
    try:
        p = sp.Popen(args=['./bash_mknod', device_path_Name, str(majorNumber), str(minorNumber)],
                     cwd=file_path_to_exe,  # needed for device_path DEBUG: erase later?
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if p.returncode == 1:
            print("mknod failed for user: ", file_path_to_exe)
            return 1
    except OSError as e:
        print("mknod exception: ", e)
        return 1

    print("create char device success")  # DEBUG
    return 0


def remove_char_device(file_path_to_exe, log_fd, device_path_name):
    try:
        p = sp.run(args=[f'sudo rm -f {device_path_name}'],
                   # cwd=file_path_to_exe,  # needed for device_path DEBUG: erase later?
                   stdout=log_fd, stderr=log_fd, shell=True
                   )
    except OSError as e:
        print("OSError on remove_char_device: ", e)
        return 1

    print("remove char device success")  # DEBUG
    return 0


def load_module(file_path_to_exe, log_fd):
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


def remove_module(file_path_to_exe, log_fd):
    try:
        p = sp.Popen(args=['./bash_rmmod'],
                     cwd=file_path_to_exe,
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if p.returncode == 1:
            print("rmmod failed for user:", file_path_to_exe)
            return 1  # DEBUG: if I cant remove the Module, I shouldn't run the other directories until its off
    except OSError as e:
        print("OSError remove_module: ", e)
        return 1  # DEBUG: if I cant remove the Module, I shouldn't run the other directories until its off

    print("remove module success")  # DEBUG
    return 0


points_to_reduct_for_test = 2  # TODO: change this to whatever would work with the tests
points_to_reduct_bug = 5  # TODO: change this to whatever would work with the tests
OVERWRITE_MODE, APPEND_MODE = 0, 1  # overwrite mode = 0, append_mode = 1


def run_tests(o_log, file_path_to_exe, device_path_Name, minor_num):
    points_to_reduct = 0
    test_errors_str = ""

    # Testing the device!
    arguments = [  # debug: (0.dev_name, 1.chID, 2.msgSTR, 3.minor_num, 4.overwrite/append_mode)
        (device_path_Name, 10, "Hello ", minor_num, OVERWRITE_MODE),  # ./tests/output0.txt
        (device_path_Name, 10, "World", minor_num, APPEND_MODE),  # ./tests/output1.txt
        (device_path_Name, 10, "Overwritten", minor_num, OVERWRITE_MODE),  # ./tests/output2.txt
        (device_path_Name, 20, "##new123", minor_num, APPEND_MODE),  # ./tests/output3.txt
        (device_path_Name, 20, "##appended##", minor_num, APPEND_MODE),  # ./tests/output4.txt
        (device_path_Name, 10, "123ow#", minor_num, OVERWRITE_MODE),  # ./tests/output5.txt
    ]
    for args_test_num, test_tuple in enumerate(arguments):
        test_output_name = file_path_to_exe + 'output{}.txt'.format(args_test_num)
        true_test_name = './tests/output{}.txt'.format(args_test_num)
        if send_message(True, file_path_to_exe, o_log,
                        test_tuple[0], test_tuple[4], test_tuple[1], test_tuple[2]) == 1:
            print("Send message failed on test {} and user {}".format(args_test_num, file_path_to_exe))
            points_to_reduct += points_to_reduct_for_test
            test_errors_str += "message_sender failed. "
            continue
        # Read with my message_reader and write to: testOutputFd
        with open(test_output_name, 'w+') as testOutputFd:
            if read_message(True, file_path_to_exe, o_log, test_tuple[0], test_tuple[1], testOutputFd) == 1:
                # DEBUG : change True\False for users\mine message_reader exe
                print("Read message failed on test {} and user {}".format(args_test_num, file_path_to_exe))
                points_to_reduct += points_to_reduct_bug
                test_errors_str += "message_reader failed. "
                continue
        # Test output file
        true_fd = open(true_test_name, 'r')
        testOutputFd = open(test_output_name, 'r')
        true_string = true_fd.readline()
        output_string = testOutputFd.readlines()  # This is a list!

        if true_string:
            if (output_string):
                print('user string: {}\ntrue string: {}'.format(output_string, true_string))  # DEBUG
                OKflag = False
                for line_str in output_string:
                    # print("{} ## {}".format(line_str, true_string))  # Debug
                    if (true_string in line_str):
                        OKflag = True
                if OKflag is False:
                    points_to_reduct += points_to_reduct_for_test
                    test_errors_str += "test {} failed. ".format(args_test_num)
                    o_log.write("test {} failed\n".format(args_test_num))
                else:
                    o_log.write("test {} succeeded\n".format(args_test_num))
            else:
                points_to_reduct += points_to_reduct_for_test
                test_errors_str += "test {} failed. ".format(args_test_num)

        true_fd.close()
        testOutputFd.close()

    return points_to_reduct, test_errors_str


def message_reader_text_test(o_log, file_path_to_exe, dev_name):
    test_errors_str = ""
    points_to_reduct = 0
    minor_num = 250
    try:
        test_output_name = file_path_to_exe + 'outputUserReader.txt'
        with open(test_output_name, 'w') as test_log:  # ./assignments/Yuval Checker_999999999/output1.txt
            # Check If the user's message_reader is valid (Most of them aren't...) :(
            if send_message(file_path_to_exe, o_log, dev_name, OVERWRITE_MODE, minor_num, "messageToBeRead") == 1:
                test_errors_str += "message_sender doesn't work. "
                points_to_reduct += points_to_reduct_for_test
            # Read with user's message_reader
            if read_message(True, file_path_to_exe, o_log, dev_name, 1, test_log) == 1:
                test_errors_str += "message_reader output not as requested. "
                points_to_reduct += points_to_reduct_for_test
    except OSError as e:
        print("OSError First One: ", e)

    return points_to_reduct, test_errors_str


def build_tests(file_path_to_exe, o_log):
    '''
    Checks the tests on 1 student
    Returns the number of points needed to reduct from the student
    @param file_path_to_exe:
    @param myParam2:
    @return: (Points_to_deduct, test_errors_str) == (100>=int>=0, String)
    '''
    majorNumber = 0

    ret, majorNumber = load_module(file_path_to_exe, o_log)
    print("Major number: ", majorNumber)  # DEBUG
    if majorNumber <= 0:
        print("debug here majNum <0. error is: ", sys.exc_info()[0])  # DEBUG
        remove_module(file_path_to_exe, o_log)
        return 40, "Major Number Parsing from Syslog failed. "

    minor_num = 20
    dev_name = "charDevice"
    deviceUniqueIdentifer = file_path_to_exe.split("/")[-2]  # Student Name
    device_path_Name = "/dev/{}{}".format(dev_name, deviceUniqueIdentifer)

    create_char_device(file_path_to_exe, o_log, majorNumber, minor_num, device_path_Name)

    points_to_reduct, test_errors_str = \
        run_tests(o_log, file_path_to_exe, device_path_Name, minor_num)

    remove_char_device(file_path_to_exe, o_log, device_path_Name)
    remove_module(file_path_to_exe, o_log)

    print(points_to_reduct, test_errors_str)

    return points_to_reduct, test_errors_str


def iterate_students_directories(super_log):
    assignments_dir = Path("/home/user/work/OS_autoGrader/assignments/")

    for student_dir in assignments_dir.iterdir():
        splitted_filename = student_dir.name.split("_")
        student_name = splitted_filename[0] + " " + splitted_filename[1]
        student_id = splitted_filename[2]
        student_GRADE = 100

        stud_dir_path = assignments_dir / student_dir / "/"  # ->  ./assignments/Yuval Checker_999999999/
        log_name_path = stud_dir_path + 'hw3.log'

        stud_logger = utils.setup_logger(name='student logger', log_file=log_name_path, mode='w')
        stud_logger.info(f'Tests Initialize for student {student_name}_{student_id}')
        super_log.info(f'Tests Initialize for student {student_name}_{student_id}')

        try:
            compiledRet = compile_student_files(stud_dir_path, stud_logger)
            if compiledRet != 0:
                stud_logger.info(f'Compilation phase failed for: {student_name}_{student_id}')
                utils.write_to_grades_csv(student_name, student_id, 0, 'Compilation error')
                continue

            stud_logger.info(f'Compilation Success')

            copy_scripts_to_user(stud_dir_path, stud_logger)

            points_to_reduct, test_errors_str = build_tests(stud_dir_path, stud_logger)

            student_GRADE -= points_to_reduct
            stud_logger.info(f"{student_name}_{student_id} grade: {student_GRADE}")
            utils.write_to_grades_csv(student_name, student_id, student_GRADE, test_errors_str)
        except Exception as e:
            stud_logger.info(f'Tests threw exception for student {student_name}_{student_id}: {e}')
            super_log.info(f'Tests threw exception for student {student_name}_{student_id}: {e}')


def main():
    # Highest level file logger
    super_logger = utils.setup_logger(name='hw3 logger', log_file='hw3.log')
    super_logger.info('Log Initialize!')
    utils.open_names_csv()
    compile_static_files(super_logger)
    uzip_and_build_test_environment(super_logger)

    # chmod_everything()
    iterate_students_directories(super_logger)  # TODO: test this

    print("Done")


if __name__ == '__main__':
    main()
