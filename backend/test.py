import sys
sys.dont_write_bytecode = True
import util.database_setup
import database.redis

util.database_setup.setup()


