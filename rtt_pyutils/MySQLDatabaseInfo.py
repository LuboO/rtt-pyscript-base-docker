class MySQLDatabaseInfo:
    def __init__(self, host, port, database, username, password):
        self.host = host
        self.port = int(port)
        self.database = database
        self.username = username
        self.password = password
