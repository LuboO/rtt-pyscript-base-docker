class MySQLDatabaseInfo:
    def __init__(self, host, port, database, user, password):
        self.host = host
        self.port = int(port)
        self.database = database
        self.user = user
        self.password = password
