import os
import re
import subprocess as sp
import sys
from pathlib import Path

# import kmod
import utils

p = Path(__file__).resolve()


def compile_files(exe_files_path, output_log):
    # p = sp.Popen(args=['pwd'], #debug
    #              cwd=exe_files_path,
    #              stdout=output_log, stderr=output_log
    #              )
    try:
        p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_reader.c"
            , "-o", "message_reader"],
                     cwd=exe_files_path,
                     stdout=output_log, stderr=output_log
                     )
        p.wait()
        if p.returncode != 0:  # check if compilation works
            print("reader compile failed")  # DEBUG
            return 1
        p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_sender.c"
            , "-o", "message_sender"],
                     cwd=exe_files_path,
                     stdout=output_log, stderr=output_log
                     )
        p.wait()
        if p.returncode != 0:  # check if compilation works
            print("sender compile failed")  # DEBUG
            return 1
        p = sp.Popen(args=['make'],
                     cwd=exe_files_path,
                     stdout=output_log, stderr=output_log
                     )
        p.wait()
        if p.returncode != 0:  # check if compilation works
            print("Make failed")  # DEBUG
            return 1

        # Check if the .ko file was created
        if (os.path.exists(exe_files_path + "message_slot.ko") == False):
            print(".ko file missing")  # DEBUG
            return 1
    except OSError as e:
        print("OSError compile_files: ", e)
        return 1
    except:
        print("error on compile_files")
        return 1

    return 0


'''
@param is_user_file - a boolean that specifies if the function will use the user's message_reader code, or mine.
@param file_path_to_exe - the path to the user's directory
@param log_fd - a file descriptor to throw output, for later debugging
@param dev_name - the device name to read from
@param chID - the chanel to read from within the device
@return: 0 on success. 1 else
'''


def read_message(is_user_file, file_path_to_exe, log_fd, dev_name, chID, outputFilePath):
    device_path = "/dev/{}".format(dev_name)
    directory_src = "./src/"
    try:
        if is_user_file == True:
            # Using the user's "Message reader"
            p = sp.Popen(args=['./message_reader', device_path, str(chID), ">", outputFilePath],
                         # Not useful.. as most students print extra junk in addition to the needed text... in different ways..
                         cwd=file_path_to_exe,
                         stdout=log_fd, stderr=log_fd)
            p.wait()
        else:
            p = sp.Popen(args=['./message_reader', device_path, ">", outputFilePath],
                         cwd=directory_src,  # set to the src directory where my message_reader is at
                         stdout=log_fd, stderr=log_fd)
            p.wait()
        if (p.returncode != 0):
            print("message_reader failed", file_path_to_exe)
            return 1
    except OSError as e:
        print("OSError read_message: ", e)
        return 1

    return 0


def send_message(file_path_to_exe, log_fd, dev_name, write_mode, chID, msgStr):
    device_path = "/dev/{}".format(dev_name)
    try:
        # Using the user's "Message Sender"
        p = sp.Popen(args=['./message_sender', device_path, str(write_mode), str(chID), msgStr],
                     cwd=file_path_to_exe,
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if (p.returncode != 0):
            print("message_sender failed", file_path_to_exe)
            return 1
    except OSError as e:
        print("OSError send_message: ", e)
        return 1

    return 0


def create_char_device(file_path_to_exe, log_fd, majorNumber, minorNumber, dev_name):
    device_path = "/dev/{}".format(dev_name)

    p = sp.Popen(args=['sudo mknod', '-m 777', device_path, 'c', str(majorNumber), str(minorNumber)],
                 cwd=file_path_to_exe,
                 stdout=log_fd, stderr=log_fd)
    p.wait()
    if (p.returncode != 0):
        print("mknod failed", file_path_to_exe)
        return 1
    # # change the created file's permissions
    # p = sp.Popen(args=['chmod 777 /dev/{}'.format(dev_name)],
    #              cwd=file_path_to_exe,
    #              stdout=log_fd, stderr=log_fd)
    # p.wait()

    print("create char device success")  # DEBUG
    return 0


def remove_char_device(file_path_to_exe, log_fd, dev_name):
    try:
        p = sp.Popen(args=['rm -f /dev/{}'.format(dev_name)],
                     cwd=file_path_to_exe,
                     stdout=log_fd, stderr=log_fd)
        p.wait()
    except OSError as e:
        print("OSError on remove_char_device: ", e)
        return 1

    print("remove char device success")  # DEBUG
    return 0


def copyScriptsToUser(file_path_to_exe, log_fd):
    try:
        # Copy bash scripts from /src to file_path_to_exe
        p = sp.Popen(args=['cp', '-p', './src/bash_insmod', file_path_to_exe],
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if (p.returncode == 1):
            print("copy insmod failed for user: ", file_path_to_exe)
            return 1, -1
    except:
        print("1")
        return 1, -1

    try:
        p = sp.Popen(args=['cp', '-p', './src/bash_rmmod', file_path_to_exe],
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if (p.returncode == 1):
            print("copy rmmod failed for user: ", file_path_to_exe)
            return 1, -1
    except:
        print("2:")
        return 1, -1


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

    last_line = 0  # DEBUG: erase and merge 5 and 6
    try:
        with open("/var/log/syslog", 'r') as dmesg_log:
            log_lines_list = dmesg_log.readlines()
            if (log_lines_list):
                last_line = log_lines_list[len(log_lines_list) - 1]
                # Split the message that the student wrote, then fetch the first number with regex
                studentKernLogMessage = last_line.split(']')[1]
                majorNumber = (re.findall(r'\d+', studentKernLogMessage)[0])
    except OSError as e:
        print("Fetching MajorNumber Failed: ", e)  # DEBUG
        return 1, -1
    except:
        print("4;")  # DEBUG
        return 1, -1

    # Remove the files created if needed # TODO mabye?
    # os.remove("'dmesg_file.txt'")

    print("load module success")  # DEBUG
    return 0, majorNumber


def module_Exists():
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
        if (p.returncode == 1):
            print("rmmod failed for user:", file_path_to_exe)
            sys.exit()  # DEBUG: if I cant remove the Module, I shouldn't run the other directories until its off
    except OSError as e:
        print("OSError remove_module: ", e)
        sys.exit()  # DEBUG: if I cant remove the Module, I shouldn't run the other directories until its off

    print("remove module success")  # DEBUG
    return 0


'''
Checks the tests on 1 student
Returns the number of points needed to reduct from the student
@param file_path_to_exe: 
@param myParam2:
@return: (Points_to_deduct, test_errors_str) == (100>=int>=0, String)
'''
points_to_reduct_for_test = 3  # TODO: change this to whatever would work with the tests
points_to_reduct_mem_leak = 1  # TODO: change this to whatever would work with the tests
overwrite_mode, append_mode = 0, 1  # overwrite mode = 0, append_mode = 1


def run_tests(file_path_to_exe, o_log):
    points_to_reduct = 0
    test_errors_str = ""
    majorNumber = 0

    try:
        copyScriptsToUser(file_path_to_exe, o_log)
        ret, majorNumber = load_module(file_path_to_exe, o_log)
        print(majorNumber)  # DEBUG
    except OSError as e:
        print("OSError22: ", e)
    except:
        if (majorNumber <= 0):
            print("debug here majNum <0. error is: ", sys.exc_info()[0])  # DEBUG
            return 100, True

    minor_num = 34
    dev_name = "test_char"
    try:
        create_char_device(file_path_to_exe, o_log, majorNumber, minor_num, dev_name)
    except OSError as e:
        print("OSError First One: ", e)

    arguments = [  # debug: (0.dev_name, 1.chID, 2.msgSTR, 3.minor_num, 4.overwrite/append_mode)
        (dev_name, 1, "MessageString", minor_num, overwrite_mode),
    ]

    for args_test_num, test_tuple in enumerate(arguments):
        test_output_name = file_path_to_exe + 'output{}.txt'.format(args_test_num)
        test_log = open(test_output_name, 'w')  # ./assignments/Yuval_Checker_999999999/output1.txt

        # TODO: add different char_devices to this

        if send_message(file_path_to_exe, o_log, test_tuple[0], overwrite_mode, test_tuple[1], test_tuple[2]) == 1:
            test_errors_str += "message_sender doesn't work, "
            points_to_reduct += points_to_reduct_for_test
            print("write message failed on test ", args_test_num)
            continue
        # Read with my message_reader
        if read_message(False, file_path_to_exe, o_log, test_tuple[0], test_tuple[1], test_output_name) == 1:
            print("Read message failed on test ", args_test_num)

        test_log.close()
        # # Run diff with the expected test
        # path = "./input_files/"
        # try:
        #     p = sp.Popen(
        #         args=['diff', output_log_path, "./input_files/expected_{}_{}".format(env_test_num, args_test_num)],
        #         stdout=output_log, stderr=output_log)
        #     p.wait()
        # except OSError as e:
        #     print("OSError3: ", e)

    try:
        test_output_name = file_path_to_exe + 'outputUserReader.txt'
        with open(test_output_name, 'w') as test_log:  # ./assignments/Yuval Checker_999999999/output1.txt
            # Check If the user's message_reader is valid (Most of them aren't...) :(
            if send_message(file_path_to_exe, o_log, dev_name, overwrite_mode, 1, "messageToBeRead") == 1:
                test_errors_str += "message_sender doesn't work, "
            # Read with user's message_reader
            if read_message(True, file_path_to_exe, o_log, dev_name, 1, test_output_name) == 1:
                test_errors_str += "message_reader output not as requested, "
                points_to_reduct += 3

    except OSError as e:
        print("OSError First One: ", e)

    remove_char_device(file_path_to_exe, o_log, "test_char")
    remove_module(file_path_to_exe, o_log)

    print(points_to_reduct, test_errors_str)

    return points_to_reduct, test_errors_str


def iterate_students_directories():
    utils.open_names_csv()

    directory_str = "./assignments/"

    with open('compilation_log.txt', 'w') as general_log:
        general_log.write('.\n')
    general_log = open('compilation_log.txt', 'a')

    for student_dir in os.listdir(directory_str):  # iterate on all student folders!
        general_log.write("Starting on: {}\n".format(student_dir))
        splitted_filename = student_dir.split("_")
        student_name = splitted_filename[0] + " " + splitted_filename[1]
        student_id = splitted_filename[2]
        student_GRADE = 100

        stud_dir_path = directory_str + student_dir + "/"  # ->  ./assignments/Yuval Checker_999999999/
        log_name_path = stud_dir_path + 'opLog.txt'
        print("Running tests for: " + stud_dir_path)
        try:
            with open(log_name_path, 'w') as output_log:  # a file to throw logs for debugging
                compiledRet = compile_files(stud_dir_path, output_log)
                if (compiledRet != 0):
                    print("{}".format(student_name), " Compilation Failed")
                    # write_to_csv(student_name, student_id, 0, 'Compilation error')
                else:  # tests
                    print("student {} ".format(student_name), "compilation successful")
                    points_to_reduct, test_errors_str = run_tests(stud_dir_path, output_log)
                    student_GRADE -= points_to_reduct
                    print("students grade: ", student_GRADE)
                    # write_to_csv(student_name, student_id, student_GRADE, test_errors_str)
        except OSError as e:
            print("OSError1: ", e)
        except ValueError as e2:
            print("ValueError1: ", e2)

    general_log.close()


def chmod_everything():
    try:
        p = sp.Popen(args=['chmod -R 777 ./'])
        p.wait()
        if (p.returncode != 0):
            return 1
    except OSError as e:
        print("OSError: ", e)
        return 1
    return 0


if __name__ == '__main__':
    # chmod_everything()
    iterate_students_directories()
    print("hi")
