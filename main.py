import os
import sys
import dropi
from pprint import pprint as pp

import tqdm

import dorless


a:dropi.Api42
debug = os.getenv('AC_DEBUG') == 'true'

def connect():
	psize = os.getenv('DROPI_POOL_SIZE')
	if psize:
		dropi.config.max_poolsize = int(psize)
	global a
	dprint(f"connecting to intra...")
	a = dropi.Api42()
	dorless.setup()

def dprint(s: str):
	if debug:
		print(s, file=sys.stderr, flush=True)

def getUserData(min_date: str, max_date: str, user):
	dprint(f"processing {user['login']}...")

	id = user['id']
	dprint("fetching scale_teams...")
	scales = a.get(f"users/{id}/scale_teams")

	# Get how many correction the user did
	ranged_scales = [x for x in scales if not x['filled_at'] == None and x['filled_at'][:len(min_date)] >= min_date and x['filled_at'][:len(max_date)] <= max_date]
	evals = len([x for x in ranged_scales if not x['corrector'] == {} and x['corrector']['id'] == id])

	# Get how many projects where attempted and how many passed
	dprint("fetching projects_users...")
	projects = a.get(f"users/{id}/projects_users")
	ranged_projects = [x for x in projects if not x['marked_at'] == None and x['marked_at'][:len(min_date)] >= min_date and x['marked_at'][:len(max_date)] <= max_date]
	attempt = len([x for x in ranged_projects if x['marked']])
	validated = len([x for x in ranged_projects if x['validated?']])
	if dorless.checkDorlet:
		tqdm.tqdm.write(f"{id},{user['login']},{evals},{attempt},{validated},{dorless.getTimes(dorless.getUserId(user['login']), min_date, max_date)}")
	else :
		tqdm.tqdm.write(f"{id},{user['login']},{evals},{attempt},{validated}")

def getUsersData(min_date: str, max_date: str):
	campus_id = os.getenv("CAMPUS_ID")
	if campus_id == None:
		print("No campus id. Did someone forget to source .env?")
		exit(-1)

	users = a.get("cursus/21/cursus_users", data={'filter':{'campus_id':campus_id}})
	print("user_id,login,evals_done,attempts,validations,building_access")
	if not debug:
		users = tqdm.tqdm(users)
	for user in users:
		if not debug:
			users.set_description(user['user']['login'])
		getUserData(min_date, max_date, user['user'])

if __name__ == "__main__":
	if (len(sys.argv) == 3):
		dprint("Setting up connections...")
		connect()
		dprint("Getting all students...")
		getUsersData(sys.argv[1], sys.argv[2])
	elif (len(sys.argv) == 4):
		dprint("Setting up connections...")
		connect()
		dprint(f"Getting user {sys.argv[3]}")
		user = a.get(f"users/{sys.argv[3]}")
		if user == None:
			print(f"user with login {sys.argv[3]} not found")
			exit(-1)
		else:
			getUserData(sys.argv[1], sys.argv[2], user)
	else:
		print("usage: python main.py <min_date_tiem> <max_date_time> [login]\n\tmin and max date time are inclusive and must be of the form YYYY-MM-DDThh:mm:ss:mmmZ. You may truncate the date-time at any time")
		exit(-1)
