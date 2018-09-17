from configparser import ConfigParser
from rtt_pyutils.MySQLDatabaseInfo import MySQLDatabaseInfo


class RttConfigParser(ConfigParser):
    def __init__(self, file):
        super().__init__()
        self.file = file
        self.safe_read(file)

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

    def get_mysql_db_info(self):
        self.check_has_section("MySQL-Database")

        try:
            host = self.safe_get("MySQL-Database", "Host")
            port = self.safe_get("MySQL-Database", "Port")
            database = self.safe_get("MySQL-Database", "Database")
            credentials_cnf = RttConfigParser(self.safe_get("MySQL-Database", "Credentials-file"))

            user = credentials_cnf.safe_get("Credentials", "User")
            password = credentials_cnf.safe_get("Credentials", "Password")

            return MySQLDatabaseInfo(host=host, port=port, database=database, user=user, password=password)

        except Exception as e:
            raise RuntimeError(f"config \"{self.file}\": can't read MySQL Database information: {e}")
