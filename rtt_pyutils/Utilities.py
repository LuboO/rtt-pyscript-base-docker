import logging
import shlex
import sys
import os
from getpass import getpass
from subprocess import call
from multiprocessing import Process
from rtt_pyutils.EnvVariableGetter import EnvVariableGetter

import MySQLdb

class Utilities:
    @staticmethod
    def exec_sys_call_check(command, stdin=None, stdout=None, acc_codes=[0]):
        rval = call(shlex.split(command), stdin=stdin, stdout=stdout)
        if rval not in acc_codes:
            raise EnvironmentError("Executing command \'{}\', error code: {}"
                                   .format(command, rval))


    @staticmethod
    def init_basic_logger(script_name, log_file_path=None):
        if log_file_path is None:
            log_file_path = Utilities.get_default_script_log_path(script_name)

        logger = logging.getLogger(script_name)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s",
                                      "%Y-%m-%d %H:%M:%S")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger


    @staticmethod
    def get_default_script_log_path(script_name):
        return os.path.join(EnvVariableGetter.get_rtt_pyscript_logs_dir(), f"{script_name}.log")


    @staticmethod
    def get_default_script_config_path(script_name):
        return os.path.join(EnvVariableGetter.get_rtt_pyscript_cnf_dir(), f"{script_name}.cnf")


    @staticmethod
    def get_script_name(script_filename):
        return os.path.splitext(os.path.basename(script_filename))[0]


    @staticmethod
    def prompt_new_password():
        while True:
            pwd1 = getpass("Enter new password: ")
            pwd2 = getpass("Repeat new password: ")
            if pwd1 != pwd2:
                print("Passwords does not match. Please repeat.")
            else:
                return pwd1


    @staticmethod
    def prompt_confirmation(message):
        confirm = input(f"{message}? [Y/n] ")
        return confirm == "Y"


    @staticmethod
    def prompt_purge_confirmation(machine_info, verification_phrase):
        print("=========================== !!!WARNING!!! ============================")
        print("======================================================================")
        print("=== You are about to purge all RTT related data and programs       ===")
        print("=== from this machine. This includes docker containers and images, ===")
        print("=== databases, logs, user accounts and such.                       ===")
        print("======================================================================")
        print("=========================== !!!WARNING!!! ============================")
        print()
        print(f"To be purged: {machine_info}")
        if not prompt_confirmation("Are you ABSOLUTELY sure you want to continue"):
            print()
            return False
        phrase = input(f"Repeat phrase \"{verification_phrase}\" to confirm purge: ")
        print()
        return phrase == verification_phrase


    @staticmethod
    def create_mysql_database_connection(db_info):
        try:
            return MySQLdb.connect(host=db_info.host, port=db_info.port, db=db_info.database,
                                   user=db_info.user, passwd=db_info.password)
        except Exception as e:
            raise RuntimeError(f"creating MySQL database connection: {e}")

    @staticmethod
    def call_process_function(logger, fnc):
        try:
            fnc()
        except Exception as ex:
            logger.error(f"executing process function: {ex}")

    @staticmethod
    def run_with_timeout(logger, fnc, timeout=60):
        # Caller is responsible for catching exceptions
        fnc_process = Process(target=Utilities.call_process_function, args=(logger, fnc))
        fnc_process.start()
        fnc_process.join(timeout=timeout)

        if fnc_process.is_alive():
            fnc_process.terminate()
            raise TimeoutError("Process timeouted and was terminated.")
