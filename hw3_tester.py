import os
import re
import stat
import subprocess as sp
import sys
from pathlib import Path
from time import sleep

# import kmod
import utils

p = Path(__file__).resolve()

def compile_static_files(gen_log):
    files_path = "./src/"
    try:
        p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_reader.c"
            , "-o", "message_reader_true"],
                     cwd=files_path,
                     stdout=gen_log, stderr=gen_log
                     )
        p.wait()
        if p.returncode != 0:  # check if compilation works
            print("reader compile failed")  # DEBUG
            return 1
        os.chmod("{}{}".format(files_path, 'message_reader_true'),
                 stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)  # DEBUG: testing this
    except OSError as e:
        print("OSError compile_files: ", e)
        return 1

    return 0

def compile_files(exe_files_path, output_log):
    try:
    #     p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_reader.c"
    #         , "-o", "message_reader"],
    #                  cwd=exe_files_path,
    #                  stdout=output_log, stderr=output_log
    #                  )
    #     p.wait()
    #     os.chmod("{}{}".format(exe_files_path, 'message_reader'),
    #              stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)  # DEBUG: testing this
    #     if p.returncode != 0:  # check if compilation works
    #         print("reader compile failed")  # DEBUG
    #         return 1 # TODO: see if reader should be even checked..
        p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_sender.c"
            , "-o", "message_sender"],
                     cwd=exe_files_path,
                     stdout=output_log, stderr=output_log
                     )
        p.wait()
        os.chmod("{}{}".format(exe_files_path, 'message_sender'),
                 stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)  # DEBUG: testing this
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


def read_message(is_user_file, file_path_to_exe, log_fd, device_path_Name, chID, output_fd):

    # print("device_path: ", relative_device_path) # DEBUG
    src_path = "./src/"
    perfect_reader_path = '/home/yuval/Downloads/OS_autoGrader/src/message_reader'

    try:
        if is_user_file == True:
            # Using the user's "Message reader"
            p = sp.Popen(args=['./message_reader', device_path_Name, str(chID)],
                         # Not useful.. as most students print extra junk in addition to the needed text... in different ways..
                         cwd=file_path_to_exe,  # needed for device_path
                         stdout=output_fd, stderr=output_fd)  # TODO: read to the outputFilePath
            p.wait()
        else:
            p = sp.Popen(args=['./message_reader_true', device_path_Name, str(chID)],
                         cwd=file_path_to_exe,  # needed for device_path
                         stdout=output_fd, stderr=output_fd)  # TODO: read to the outputFilePath
            p.wait()
        if (p.returncode != 0):
            return 1
    except OSError as e:
        print("read_message failed: ", e)
        return 1

    return 0


def send_message(file_path_to_exe, log_fd, device_path_Name, write_mode, chID, msgStr):
    try:
        # Using the user's "Message Sender"
        p = sp.Popen(args=['./message_sender', device_path_Name, str(write_mode), str(chID), msgStr],
                     cwd=file_path_to_exe,  # needed for device_path
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if (p.returncode != 0):
            return 1
    except OSError as e:
        print("send_message failed: ", e)
        return 1

    return 0

# TODO: this doesn't work well. device doesn't open after creation
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
        if (p.returncode == 1):
            print("mknod failed for user: ", file_path_to_exe)
            return 1
    except OSError as e:
        print("mknod exception: ", e)
        return 1

    print("create char device success")  # DEBUG
    return 0


def remove_char_device(file_path_to_exe, log_fd, device_path_Name):
    # deviceUniqueIdentifer = file_path_to_exe.split("/")[-2]  # Student Name
    # device_path_Name = "/dev/{}{}".format(dev_name, deviceUniqueIdentifer)
    #print(device_path_Name) # DEBUG
    # try:
    #     p = sp.Popen(args=['./src/removefile', device_path_Name],
    #                  #cwd=file_path_to_exe,  # needed for device_path DEBUG: erase later?
    #                  stdout=log_fd, stderr=log_fd
    #                  )
    #     p.wait()
    # except OSError as e:
    #     print("OSError on remove_char_device: ", e)
    #     return 1

    try:
        p = sp.Popen(args=['sudo rm -f {}'.format(device_path_Name)],
                     #cwd=file_path_to_exe,  # needed for device_path DEBUG: erase later?
                     stdout=log_fd, stderr=log_fd, shell=True
                     )
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
        print("copy bash_insmod failed")
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
        print("copy bash_rmmod failed")
        return 1, -1

    try:
        p = sp.Popen(args=['cp', '-p', './src/bash_mknod', file_path_to_exe],
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if (p.returncode == 1):
            print("copy mknod failed for user: ", file_path_to_exe)
            return 1, -1
    except:
        print("copy bash_mknod failed")
        return 1, -1
    try:
        p = sp.Popen(args=['cp', '-p', './src/message_reader_true', file_path_to_exe],
                     stdout=log_fd, stderr=log_fd
                     )
        p.wait()
        if (p.returncode == 1):
            print("copy mknod failed for user: ", file_path_to_exe)
            return 1, -1
    except:
        print("copy bash_mknod failed")
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


points_to_reduct_for_test = 3  # TODO: change this to whatever would work with the tests
points_to_reduct_bug = 5  # TODO: change this to whatever would work with the tests
overwrite_mode, append_mode = 0, 1  # overwrite mode = 0, append_mode = 1


def run_tests(o_log, file_path_to_exe, device_path_Name, minor_num):
    points_to_reduct = 0
    test_errors_str = ""

    # Testing the device!
    arguments = [  # debug: (0.dev_name, 1.chID, 2.msgSTR, 3.minor_num, 4.overwrite/append_mode)
        (device_path_Name, 10, "Hello ", minor_num, overwrite_mode),  # ./tests/output0.txt
        (device_path_Name, 10, "World", minor_num, append_mode),  # ./tests/output1.txt
        (device_path_Name, 10, "Overwritten", minor_num, overwrite_mode),  # ./tests/output2.txt
    ]
    for args_test_num, test_tuple in enumerate(arguments):
        test_output_name = file_path_to_exe + 'output{}.txt'.format(args_test_num)
        true_test_name = './tests/output{}.txt'.format(args_test_num)
        with open(test_output_name, 'w+') as testOutputFd:  # ./assignments/Yuval_Checker_999999999/output1.txt
            if send_message(file_path_to_exe, o_log,
                            test_tuple[0], test_tuple[4], test_tuple[1], test_tuple[2]) == 1:
                print("Send message failed on test {} and user {}".format(args_test_num, file_path_to_exe))
                points_to_reduct += points_to_reduct_for_test
                test_errors_str += "message_sender failed. "
                continue
            # Read with my message_reader
        with open(test_output_name, 'r') as testOutputFd:
            if read_message(False, file_path_to_exe, o_log, test_tuple[0], test_tuple[1], testOutputFd) == 1:
                # DEBUG : change True\False for users\mine message_reader exe
                print("Read message failed on test {} and user {}".format(args_test_num, file_path_to_exe))
                points_to_reduct += points_to_reduct_bug
                test_errors_str += "message_reader failed. "
                continue
        # Test output file
        true_log = open(true_test_name, 'r')
        testOutputFd = open(test_output_name, 'r')
        true_string = true_log.readline()
        output_string = testOutputFd.readline()

        if (output_string and true_string):
            print('user string: {}.'.format(output_string))
            print('true string: {}.'.format(true_string))
            if (true_string != output_string):
                points_to_reduct += points_to_reduct_for_test
                test_errors_str += "test {} failed. ".format(args_test_num)
                o_log.write("test {} failed".format(args_test_num))
            else:
                o_log.write("test {} succeeded".format(args_test_num))

        true_log.close()
        testOutputFd.close()

    return points_to_reduct, test_errors_str

def test_messageReader_text(o_log, file_path_to_exe, dev_name):
    test_errors_str = ""
    points_to_reduct = 0
    minor_num = 250
    try:
        test_output_name = file_path_to_exe + 'outputUserReader.txt'
        with open(test_output_name, 'w') as test_log:  # ./assignments/Yuval Checker_999999999/output1.txt
            # Check If the user's message_reader is valid (Most of them aren't...) :(
            if send_message(file_path_to_exe, o_log, dev_name, overwrite_mode, minor_num , "messageToBeRead") == 1:
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

    copyScriptsToUser(file_path_to_exe, o_log)
    ret, majorNumber = load_module(file_path_to_exe, o_log)
    print("Major number: ", majorNumber)  # DEBUG
    if (majorNumber <= 0):
        print("debug here majNum <0. error is: ", sys.exc_info()[0])  # DEBUG
        return 50, "Major Number Parsing from Syslog failed. "

    minor_num = 134
    dev_name = "charDevice"
    deviceUniqueIdentifer = file_path_to_exe.split("/")[-2]  # Student Name
    device_path_Name = "/dev/{}{}".format(dev_name, deviceUniqueIdentifer)

    create_char_device(file_path_to_exe, o_log, majorNumber, minor_num, device_path_Name)

    points_to_reduct, test_errors_str = run_tests(o_log, file_path_to_exe, device_path_Name, minor_num)

    #remove_char_device(file_path_to_exe, o_log, device_path_Name) # DEBUG: get it back online

    # Run message_reader with the user's file. see if text is similar
    # points_to_reduct_text, test_errors_str_text = test_messageReader_text(o_log, file_path_to_exe, dev_name)
    #  debug: forgot why i did this lel
    # points_to_reduct += points_to_reduct_text
    # test_errors_str +=test_errors_str_text

    #remove_module(file_path_to_exe, o_log) # DEBUG: get it back online

    print(points_to_reduct, test_errors_str)

    return points_to_reduct, test_errors_str


def iterate_students_directories():
    utils.open_names_csv()

    directory_str = "./assignments/"

    with open('compilation_log.txt', 'w') as general_log:
        general_log.write('.\n')
    general_log = open('compilation_log.txt', 'a')

    compile_static_files(general_log)

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
            with open(log_name_path, 'a+') as output_log:  # a file to throw logs for debugging
                compiledRet = compile_files(stud_dir_path, output_log)
                if (compiledRet != 0):
                    print("{}".format(student_name), " Compilation Failed")
                    # write_to_csv(student_name, student_id, 0, 'Compilation error')
                else:  # tests
                    print("student {} ".format(student_name), "compilation successful")
                    points_to_reduct, test_errors_str = build_tests(stud_dir_path, output_log)
                    student_GRADE -= points_to_reduct
                    print("students grade: ", student_GRADE)
                    # write_to_csv(student_name, student_id, student_GRADE, test_errors_str)
        except OSError as e:
            print("OSError1: ", e)
        except ValueError as e2:
            print("ValueError1: ", e2)

    general_log.close()


if __name__ == '__main__':
    # chmod_everything()
    iterate_students_directories()
    print("hi")
