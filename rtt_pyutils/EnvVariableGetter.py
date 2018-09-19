import os

class EnvVariableGetter:
    @staticmethod
    def get_env_variable(name, required=True, default=None):
        try:
            return os.environ[name]
        except KeyError as ex:
            if required:
                raise ex
            else:
                return default


    @staticmethod
    def get_rtt_pyscript_logs_dir(required=True, default=None):
        return EnvVariableGetter.get_env_variable("RTT_PYSCRIPT_LOGS_DIR")


    @staticmethod
    def get_rtt_pyscript_cnf_dir(required=True, default=None):
        return EnvVariableGetter.get_env_variable("RTT_PYSCRIPT_CNF_DIR")