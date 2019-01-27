from configparser import ConfigParser
from rtt_pyutils.MySQLDatabaseInfo import MySQLDatabaseInfo


class RttConfigParser(ConfigParser):
    def __init__(self, file=None, dictionary=None):
        super().__init__()
        if file is not None:
            self.file = file
            self.safe_read(file)
        elif dictionary is not None:
            for section in dictionary.keys():
                self.add_section(section)
                for key in dictionary.get(section).keys():
                    self.set(section, key, dictionary.get(section).get(key))
        else:
            raise RuntimeError("you must provide either filename or dictionary")

    def safe_get(self, section, option, required=True, default=None):
        self.check_has_section(section)

        if self.has_option(section, option):
            return self.get(section, option)
        else:
            if required:
                raise ValueError(f"config \"{self.file}\": missing option \"{option}\" in section \"{section}\"")
            else:
                return default

    def safe_read(self, file):
        self.read(file)
        if len(self.sections()) == 0:
            raise RuntimeError(f"can't read config \"{file}\"")

    def check_has_section(self, section_name):
        if not self.has_section(section_name):
            raise RuntimeError(f"config \"{self.file}\": missing section: {section_name}")
