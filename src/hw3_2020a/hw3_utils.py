import subprocess as sp
import os
import stat
import logging


def compile_static_files(gen_log):
    files_path = "../"
    try:
        p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_reader_true.c"
            , "-o", "message_reader_true"],
                     cwd=files_path,
                     stdout=gen_log, stderr=gen_log
                     )
        p.wait()
        if p.returncode != 0:  # check if compilation works
            print("Reader compile failed")  # DEBUG
            return 1
        os.chmod("{}{}".format(files_path, 'message_reader_true'),
                 stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)  # DEBUG: testing this

        p = sp.Popen(args=['gcc', '-o3', '-Wall', '-std=gnu99', "message_sender_true.c"
            , "-o", "message_sender_true"],
                     cwd=files_path,
                     stdout=gen_log, stderr=gen_log
                     )
        p.wait()
        if p.returncode != 0:  # check if compilation works
            print("Sender compile failed")  # DEBUG
            return 1
        os.chmod("{}{}".format(files_path, 'message_sender_true'),
                 stat.S_IRWXO | stat.S_IRWXG | stat.S_IRWXU)  # DEBUG: testing this
    except OSError as e:
        print("OSError compile_files: ", e)
        return 1

    return 0


def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
