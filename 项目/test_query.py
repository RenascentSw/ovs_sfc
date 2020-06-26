import json

def query(choice, range_or_instant):
    query_dict = {}
    query_dict['choice'] = choice
    query_dict['range_or_instant'] = range_or_instant
    return query_dict