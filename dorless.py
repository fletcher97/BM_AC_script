import datetime
from os import getenv
import sys
from pprint import pprint as pp

from sqlalchemy import create_engine, MetaData, Table, select, asc
from sqlalchemy.engine import Connection

from datetime import datetime, timedelta

conn:Connection
persona:Table
msgA:Table
checkDorlet:bool

debug = getenv('AC_DEBUG') == 'true'

def dprint(s: str):
	if debug:
		print(s, file=sys.stderr, flush=True)

def setup() -> None:
	global conn, persona, msgA, checkDorlet
	checkDorlet = getenv("AC_CHECK") == "true"
	if not checkDorlet:
		dprint("setup: AC check disabled")
		return
	dprint("setup: reading environment vars")
	ip = getenv("AC_IP")
	port = getenv("AC_PORT")
	user = getenv("AC_USER")
	pw = getenv("AC_PASS")
	db_name = getenv("AC_DB_NAME")
	driver = getenv("AC_DRIVER")
	engine = create_engine(f"mssql+pyodbc://{user}:{pw}@{ip}:{port}/{db_name}?driver={driver}", echo=False)
	dprint("connecting to db...")
	conn = engine.connect()
	md = MetaData()
	dprint("loading PersonasT table...")
	persona = Table("PersonasT", md, autoload_with=engine)
	dprint("loading MensajesAcceso table...")
	msgA = Table("MensajesAcceso", md, autoload_with=engine)

def getUserId(userName:str) -> int:
	dprint("fetching user id on AC db...")
	ret = conn.execute(select([persona]).where(persona.columns.Nombre == userName)).first()
	if (ret == None):
		dprint(f"ERROR - getUserId: User \'{userName}\'not found ...")
		return -1
	return ret.Id

# Lector ID has been hardcoded. Consider changing it later
def getTimes(userID: int, dateStart: str, dateEnd: str, count: int = 0):
	entranceId = 9 # entrance lector ID on the db
	dbDateLenght = 17 # The date lenght inside the db
	pythonDateLenght = 20 # The date lenght in python
	dateFormat = "%Y%m%d%H%M%S%f"
	entranceTimeDelay=16

	# Remove all letters and symbols from the date and make it the length dateLenght by appending 0 at the end
	dateStart = dateStart.translate({ord(i): None for i in '-:TZ'}).ljust(dbDateLenght, '0')
	dateEnd = dateEnd.translate({ord(i): None for i in '-:TZ'}).ljust(dbDateLenght, '0')

	if userID == -1:
		return -1
	if dateStart > dateEnd:
		return count
	dprint("fetching access from db...")
	ret = conn.execute(
		select([msgA])
		.where(msgA.columns.FkLector == entranceId)
		.where(msgA.columns.FkPersona == userID)
		.where(msgA.columns.Mensaje == 'Acceso válido')
		.where(msgA.columns.FechaYHoraLlegada >= dateStart)
		.where(msgA.columns.FechaYHoraLlegada <= dateEnd)
		.order_by(asc(msgA.columns.FechaYHoraLlegada))
	).first()
	if ret == None:
		return count
	dateStart = ret.FechaYHoraLlegada
	dateStart = datetime.strftime(datetime.strptime(dateStart.ljust(pythonDateLenght, '0'), dateFormat) + timedelta(hours=entranceTimeDelay), dateFormat)[:dbDateLenght]
	return getTimes(userID, dateStart, dateEnd, count + 1)
