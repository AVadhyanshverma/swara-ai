import json

tc_args = {'query': 'user name profile identity', 'limit': 5}
try:
    tc_args_str = json.dumps(tc_args, indent=2)
except Exception:
    tc_args_str = str(tc_args)

print(tc_args_str)
