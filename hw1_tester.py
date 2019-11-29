import os
import subprocess as sp
import csv
import utils
from utils import write_to_csv
from utils import zip_out_folders
from utils import build_comments


def compile_files_and_check_tests():
    directory_str = "./assignments/"
    compile_log = open('compilation_log.txt', 'w')
    compile_log.write('.\n')
    compile_log.close()
    compile_log = open('compilation_log.txt', 'a')

    for student_dir in os.listdir(directory_str):  # iterate on all students folders!
        splitted_filename = student_dir.split("_")
        student_id = splitted_filename[1]
        student_name = splitted_filename[0]
        student_GRADE = 100
        student_comment = ''

        exe_files_path = directory_str + student_dir + "/"  # ->  ./assignments/Yuval Checker_999999999/
        try:
            compile_log.write("{}\n".format(student_dir))  # Not syncronized.. but doesnt matter At the moment
            # p = sp.Popen(args=['pwd'],
            #              cwd=exe_files_path,
            #              stdout=compile_log, stderr=compile_log
            #              )
            p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=c99', "hw1_concat.c"
                , "-o", "hw1_concat"],
                         cwd=exe_files_path,
                         stdout=compile_log, stderr=compile_log
                         )
            p.wait()
            if p.returncode != 0:  # check if compilation works
                student_GRADE = 0
                student_comment = 'Compilation error'
                print("{}".format(student_name), " Compilation Failed")
                write_to_csv(student_name, student_id, student_GRADE, student_comment)
            else:  # tests
                # print("student {} ".format(student_name), "compilation successful")
                points_to_reduct, is_mem_leak, is_test_errors = run_tests(exe_files_path)
                student_GRADE -= points_to_reduct

                student_comment = build_comments(is_mem_leak, is_test_errors)
                write_to_csv(student_name, student_id, student_GRADE, student_comment)

        except OSError as e:
            print("OSError1: ", e)
        except ValueError as e2:
            print("ValueError1: ", e2)

    compile_log.close()


''' 
Checks the tests on 1 student
Returns the number of points needed to reduct from the student
'''


def run_tests(file_path_to_exe):  # ./assignments/Yuval Checker_999999999/
    # TODO: go over all of the directories I used.. didn't put too much effort into doing this in this function
    log_name_path = file_path_to_exe + 'valgrind_log.txt'
    output_log = open(log_name_path, 'w')  # a File to throw logs for debugging
    output_log.write('.\n')
    output_log.close()
    output_log = open(log_name_path, 'a')

    supp_file_path = "../../supp_file.supp"
    valgrind_err_num = 33
    points_to_reduct = 0
    points_to_reduct_for_test = 3  # TODO: change this to whatever would work with the tests
    points_to_reduct_mem_leak = 1  # TODO: change this to whatever would work with the tests
    is_mem_leak, is_test_errors = False, False

    # os.putenv(varname, value)
    os.unsetenv("HW1TF")
    os.unsetenv("HW1DIR")

    try:  # check "not defined ENV variables"
        p = sp.Popen(args=["./hw1_concat", "a", "b"],
                     cwd=file_path_to_exe,
                     stdout=output_log, stderr=output_log
                     )
        p.wait()
        if p.returncode != 1 and p.returncode != -1:
            output_log.write('not defined ENV wasn\'t checked \n')
            points_to_reduct += points_to_reduct_for_test
    except OSError as e:
        print("OSError22: ", e)

    environment_vars = [{'HW1DIR': '../../input_files', 'HW1TF': "test_0"},
                        {'HW1DIR': '../../input_files', 'HW1TF': "test_1"}
                        # ,{'HW1DIR': '../../input_files', 'HW1TF': "test2"},
                        # {'HW1DIR': '../../input_files', 'HW1TF': "test3"},
                        ]
    arguments = [('a', 'b'), ('ab', '_c'), ('a', '')]  # TODO: Iterate on different values of these tuples

    print("Running tests for: " + file_path_to_exe)
    for env_test_num, env_dict in enumerate(environment_vars):
        for args_test_num, test_tuple in enumerate(
                arguments):  # Iterate test_0 against expected_{env_test_num}{args_test_num} (example: expected_0_1 )
            # Check the output of the test.
            try:
                output_file = 'output{}_{}.txt'.format(env_test_num,
                                                       args_test_num)  # output1_1.txt . the output of the program.
                output_log_path = file_path_to_exe + 'output{}_{}.txt'.format(env_test_num,
                                                                              args_test_num)  # ./assignments/Yuval Checker_999999999/output1_1.txt
                with open(output_log_path, 'w') as o_log:
                    p = sp.Popen(args=["./hw1_concat", test_tuple[0], test_tuple[1]],
                                 cwd=file_path_to_exe,
                                 env=env_dict,
                                 stdout=o_log, stderr=output_log
                                 )
                p.wait()

            except OSError as e:
                print("OSError2: ", e)

            # Add a "newline" to the output of the student because some students do a newline to make me work harder :(
            with open(output_log_path, 'r') as o_log:
                log_lines_list = o_log.readlines()
                if (log_lines_list):
                    last_line = log_lines_list[len(log_lines_list) - 1]
                    if (last_line.endswith('\n') == False):  # add only if there isn't a newline already
                        with open(output_log_path, 'a') as o_log:
                            o_log.write('\n')

            # Run diff with the expected test
            path = "./input_files/"
            try:
                p = sp.Popen(
                    args=['diff', output_log_path, "./input_files/expected_{}_{}".format(env_test_num, args_test_num)],
                    stdout=output_log, stderr=output_log

                )
                p.wait()
            except OSError as e:
                print("OSError3: ", e)
            if p.returncode == 0:  # see if the outputs are the same and if its ok Check for memory leaks
                try:
                    pgrind = sp.Popen(args=['valgrind', "--gen-suppressions=all", "--log-file=valgrind_log.txt",
                                            "--leak-check=full",
                                            "--suppressions={}".format(supp_file_path),
                                            "--error-exitcode={}".format(valgrind_err_num),
                                            "./hw1_concat", test_tuple[0], test_tuple[1]],
                                      cwd=file_path_to_exe,
                                      env=env_dict,
                                      stdout=output_log, stderr=output_log
                                      )
                    pgrind.wait()

                    if pgrind.returncode == valgrind_err_num:
                        points_to_reduct += points_to_reduct_mem_leak
                        is_mem_leak = True
                except OSError as e:
                    print("OSError4: ", e)

            else:  # This point indicates the outputs aren't the same
                points_to_reduct += points_to_reduct_for_test
                is_test_errors = True

    print(points_to_reduct, is_mem_leak, is_test_errors)

    return points_to_reduct, is_mem_leak, is_test_errors


if __name__ == '__main__':
    # zip_out_folders()
    compile_files_and_check_tests()
    print("hi")
