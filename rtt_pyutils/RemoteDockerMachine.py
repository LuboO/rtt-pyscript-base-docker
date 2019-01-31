import json

from fabric2 import Config, Connection
from paramiko import RSAKey
from shlex import quote
from rtt_pyutils.Utilities import *


class RemoteDockerMachine:
    AUTH_METHODS = {
        "private_key":  "1",
        "password":     "2",
        "quit":         "Q"
    }

    def __init__(self, user, hostname, port, alias="", as_root=False):
        self.user = user
        self.hostname = hostname
        self.port = port
        self.exec_with_sudo = user != "root" and as_root
        self.machine_human_id = f"{hostname}:{port}"
        if alias != "":
            self.machine_human_id = f"{alias} ({self.machine_human_id})"

        print(f"\n=== Log into remote machine ===")
        print(f"Host - {self.machine_human_id}")
        print(f"User - {user}", end="")
        if self.exec_with_sudo:
            print(" (The user must be sudoer!)")
        else:
            print()

        print("Authentication methods: 1. Private key, 2. Password, Q. Quit")
        first_loop = True

        while True:
            if first_loop:
                first_loop = False
            else:
                print("Try again.")

            auth_method = input("\nChoose authentication method. [1/2/Q] ")

            # Find out authentication method
            if auth_method == self.AUTH_METHODS["private_key"]:
                print("You will be logged in using private key.")
                identity_file_path = input("Path to identity file (leave empty for ~/.ssh/id_rsa): ")
                password = getpass("Identity file password (leave empty for none): ")
                if len(identity_file_path) == 0:
                    identity_file_path = os.path.abspath(os.path.expanduser("~/.ssh/id_rsa"))
                if len(password) == 0:
                    password = None

                try:
                    # Try to load the key
                    # Retry whole process on failure
                    RSAKey.from_private_key_file(identity_file_path, password)
                except Exception as e:
                    print(f"Error while loading private key: {e}")
                    continue

            elif auth_method == self.AUTH_METHODS["password"]:
                print("You will be logged in using password.")
                identity_file_path = None
                password = getpass("Password: ")
                if len(password) == 0:
                    password = None

            elif auth_method == self.AUTH_METHODS["quit"]:
                # Abort the login process
                if Utilities.prompt_confirmation("Are you sure you want to quit"):
                    raise RuntimeError(f"Login to {self.machine_human_id} aborted.")
                else:
                    continue

            else:
                print("Unknown option! Choose 1, 2 or Q.")
                continue

            # Get sudo password if needed
            if self.exec_with_sudo:
                if auth_method != self.AUTH_METHODS["password"] \
                        or Utilities.prompt_confirmation("Is the sudo password different from your login password"):
                    sudo_pass = getpass('Sudo password (leave empty for none): ')
                else:
                    sudo_pass = password

                connection_config = Config(overrides={'sudo': {'password': sudo_pass}})
            else:
                connection_config = None

            # Attempt login, try again on failure
            try:
                self.connection = Connection(host=hostname, user=user, port=port, config=connection_config,
                                             connect_kwargs={'look_for_keys': False, 'allow_agent': False,
                                                             'password': password, 'key_filename': identity_file_path})
                # Force open connection to detect authentication failure
                self.connection.open()

            except Exception as e:
                print(f"Error while logging in: {e}")
                continue

            # Test sudo ability if needed, try again on failure
            if self.exec_with_sudo:
                try:
                    result = self.connection.sudo("whoami", hide=True)
                    # Sanity check, should never happen. Previous line raises exception on authentication failure
                    if result.exited != 0 or result.stdout.strip() != "root":
                        raise RuntimeError("\"sudo whoami\" didn't return 0 or didn't output \"root\"")
                except Exception as e:
                    self.connection.close()
                    print(f"Error while attempting sudo: {e}")
                    continue

            print(f"=== Login to {self.machine_human_id} was successful! ===\n")
            break

    def exec_cmd(self, cmd, expected_exit_codes={0}, hide=True):
        # hide=True - I don't want to print output to console
        # Instead, caller will handle the output
        try:
            if self.exec_with_sudo:
                # To avoid fuckery with commands such as 'sudo echo hello > file.txt' resulting in permission denied
                # All commands with sudo are called as 'sudo su -c "<command>"'
                return self.connection.sudo(f"su -c {quote(cmd)}", hide=hide)
            else:
                return self.connection.run(cmd, hide=hide)
        except Exception as e:
            # Write report and throw exception only if the non-zero exit code was not anticipated by the caller
            if e.result.exited not in expected_exit_codes:
                print("=== Failed command execution report ===")
                print(f"Machine: {self.machine_human_id}")
                print(f"Command: {e.result.command}")
                print(f"Exit code: {e.result.exited}")
                print(f"Stderr: {e.result.stderr.strip()}")
                print("=== End of report ===")
                raise RuntimeError("Execution of command on remote machine failed.")
            else:
                return e.result

    def file_exists(self, path, directory=False):
        if directory:
            param = "-d"
        else:
            param = "-f"
        return self.exec_cmd(f"[ {param} {quote(path)} ] && printf 1 || printf 0").stdout == "1"

    def create_directory(self, path, access="770"):
        self.exec_cmd(f"mkdir -p {quote(path)}")
        self.exec_cmd(f"chmod -R {quote(access)} {quote(path)}")

    def upload_file(self, local_file, remote_path, access="660"):
        self.exec_cmd("rm tmp_file", expected_exit_codes={0, 1})
        self.connection.put(local_file, "tmp_file")

        if self.exec_with_sudo:
            self.exec_cmd(f"chown root:root tmp_file")
        self.exec_cmd(f"chmod {quote(access)} tmp_file")
        self.exec_cmd(f"mv tmp_file {quote(remote_path)}")

    def remove_directory(self, path):
        self.exec_cmd(f"rm -rf {quote(path)}")

    def check_installed_docker(self):
        try:
            self.exec_cmd("docker -v")
        except RuntimeError:
            print("It seems that remote machine is missing Docker.")
            print("It can be installed by running\n"
                  "\"sudo apt install docker.io\"   (Ubuntu/Debian)\n"
                  "\"yum install docker\"           (RedHat/CentOS)\n")
            raise RuntimeError("Failed to run \"docker -v\".")

    def container_exists(self, name):
        filter_string = f"name=^/{name}$"
        return self.exec_cmd(f"docker ps -a -q --filter {quote(filter_string)}").stdout != ""

    def pull_image(self, docker_image):
        print(f"\nPulling docker image {docker_image}. This might take a few minutes...")
        self.exec_cmd(f"docker pull {quote(docker_image)}", hide="stderr")

    def remove_image(self, docker_image):
        self.exec_cmd(f"docker rmi -f {quote(docker_image)}")

    def remove_container(self, name, ignore_failure=False):
        if ignore_failure:
            expected_exit_codes = {0, 1}
        else:
            expected_exit_codes = {0}
        self.exec_cmd(f"docker rm -f {quote(name)}", expected_exit_codes=expected_exit_codes)

    def stop_container(self, name):
        if not self.container_exists(name):
            raise RuntimeError(f"Container {name} does not exists on {self.machine_human_id}. "
                               f"Cannot stop.")
        self.exec_cmd(f"docker stop {quote(name)}")

    def start_container(self, name):
        if not self.container_exists(name):
            raise RuntimeError(f"Container {name} does not exists on {self.machine_human_id}. "
                               f"Cannot start.")
        self.exec_cmd(f"docker start {quote(name)}")

    def restart_container(self, name):
        if not self.container_exists(name):
            raise RuntimeError(f"Container {name} does not exists on {self.machine_human_id}. "
                               f"Cannot restart.")
        self.exec_cmd(f"docker restart {quote(name)}")

    def get_image_env_var(self, image, variable_name, required=True, default=None):
        result = self.exec_cmd(f"docker inspect {quote(image)}")
        image_info = json.loads(result.stdout)[0]

        for env_variable in image_info['ContainerConfig']['Env']:
            name, value = env_variable.split('=')
            if name == variable_name:
                return value

        if required:
            raise RuntimeError(f"Environment variable {variable_name} is not defined in image {image}.")

        return default
