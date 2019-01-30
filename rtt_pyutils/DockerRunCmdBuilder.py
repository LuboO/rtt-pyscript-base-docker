from shlex import quote


class DockerRunCmdBuilder:
    run_command = "docker run"

    def __init__(self, image):
        self.image = image

    def detach(self):
        self.run_command += " --detach"
        return self

    def name(self, name):
        self.run_command += f" --name={quote(name)}"
        return self

    def env(self, variable_name, variable_value):
        pair = f"{variable_name}={variable_value}"
        self.run_command += f" --env={quote(pair)}"
        return self

    def volume(self, host_dir, container_dir):
        self.run_command += f" --volume={quote(host_dir)}:{quote(container_dir)}"
        return self

    def publish(self, host_port, container_port):
        self.run_command += f" --publish={quote(str(host_port))}:{quote(str(container_port))}"
        return self

    def build(self):
        return f"{self.run_command} {self.image}"
