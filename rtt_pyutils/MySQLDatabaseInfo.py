class MySQLDatabaseInfo:
    def __init__(self, host, port, database, username, password):
        self.host = host
        self.port = int(port)
        self.database = database
        self.username = username
        self.password = password


    @staticmethod
    def get_from_cnf(config):
        config.check_has_section("MySQL-Database")

        try:
            host = config.safe_get("MySQL-Database", "Host")
            port = config.safe_get("MySQL-Database", "Port")
            database = config.safe_get("MySQL-Database", "Database")
            username = config.safe_get("MySQL-Database", "Username")
            password = config.safe_get("MySQL-Database", "Password")

            return MySQLDatabaseInfo(host=host, port=port, database=database, username=username, password=password)

        except Exception as e:
            raise RuntimeError(f"config \"{config.file}\": can't read MySQL Database information: {e}")
