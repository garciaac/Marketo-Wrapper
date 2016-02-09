import json
import datetime
import csv
from statistics import mean

#def map_ids(activity):
#    activity["leadId"] = str(int(activity["leadId"])+1420560)
#    return activity

def map_ids(activity):
#    if activity["activityTypeId"] == "100010":
#        activity["activityTypeId"] = "100007"
#    elif activity["activityTypeId"] == "100011":
#        activity["activityTypeId"] = "100009"
#    elif activity["activityTypeId"] == "100012":
#        activity["activityTypeId"] = "100006"
#    elif activity["activityTypeId"] == "100013":
#        activity["activityTypeId"] = "100008"
    activity["id"] = str(int(activity["id"])+1420560)
    return activity

def del_leadId(lead):
    del lead["leadId"]
    return lead
    
def add_partition(lead):
    lead["lastName"] = "McRandom"
    return lead

#csvfile = open('Trello/add-team-member-activities.csv', 'r')
#jsonfile = open('Trello/add-team-member-activities.json', 'w')
#
#fieldnames = ("leadId","activityDate","activityTypeId","primaryAttributeValue")
#reader = csv.DictReader( csvfile, fieldnames)
#for row in reader:
#    json.dump(row, jsonfile)
#    jsonfile.write('\n')

#csvfile = open('Trello/invite-activities.csv', 'r')
#jsonfile = open('Trello/invite-activities.json', 'w')
#
#fieldnames = ("leadId","activityDate","activityTypeId","primaryAttributeValue")
#reader = csv.DictReader( csvfile, fieldnames)
#for row in reader:
#    json.dump(row, jsonfile)
#    jsonfile.write('\n')

#csvfile = open('Trello/joined-board-activities.csv', 'r')
#jsonfile = open('Trello/joined-board-activities.json', 'w')
#
#fieldnames = ("leadId","activityDate","activityTypeId","primaryAttributeValue","members","powerups","visibility")
#reader = csv.DictReader( csvfile, fieldnames)
#for row in reader:
#    json.dump(row, jsonfile)
#    jsonfile.write('\n')
#    
#jsonfile.close()

#csvfile = open('Trello/login-activities.csv', 'r')
#jsonfile = open('Trello/login-activities.json', 'w')
#
#fieldnames = ("leadId","activityDate","activityTypeId","primaryAttributeValue")
#reader = csv.DictReader( csvfile, fieldnames)
#for row in reader:
#    json.dump(row, jsonfile)
#    jsonfile.write('\n')

#with open("Trello/Carter/invite-activities.json") as invites:
#    iactivities = invites.readlines()
#    iactivities = list(map(json.loads, iactivities))
#    iactivities = list(map(map_ids, iactivities))
#with open("Trello/Carter/invite-activities.json", "w") as invites:
#    invites.write("\n".join(list(map(json.dumps, iactivities))))
#    
#with open("Trello/Carter/add-team-member-activities.json") as adds:
#    aactivities = adds.readlines()
#    aactivities = list(map(json.loads, aactivities))
#    aactivities = list(map(map_ids, aactivities))
#with open("Trello/Carter/add-team-member-activities.json", "w") as adds:
#    adds.write("\n".join(list(map(json.dumps, aactivities))))
#    
#with open("Trello/Carter/login-activities.json") as logins:
#    lactivities = logins.readlines()
#    lactivities = list(map(json.loads, lactivities))
#    lactivities = list(map(map_ids, lactivities))
#with open("Trello/Carter/login-activities.json", "w") as logins:
#    logins.write("\n".join(list(map(json.dumps, lactivities))))
#
#def nest_attributes(item):
#    attributes = []
#    for key in item:
#        if key == "visibility" or key == "members" or key == "powerups":
#            attribute = {"name": key, "value": item[key]}
#            attributes.append(attribute)
#    item["attributes"] = attributes
#    return item
##

#with open("Trello/Carter/joined-board-activities.json") as joins:
#    jactivities = joins.readlines()
#    jactivities = list(map(json.loads, jactivities))
#    jactivities = list(map(map_ids, jactivities))
#    
#    
#    jactivities = list(map(nest_attributes, jactivities))
#    for obj in jactivities:
#        del obj["members"]
#        del obj["powerups"]
#        del obj["visibility"]

#with open("Trello/Carter/joined-board-activities.json", "w") as joins:
#    joins.write("\n".join(list(map(json.dumps, jactivities))))

#csvfile = open('AndyList-100k - updates.csv', 'r')
#jsonfile = open('Trello/AndyList-100k - updates.json', 'w')
#
#reader = csv.DictReader(csvfile)
#for row in reader:
#    json.dump(row, jsonfile)
#    jsonfile.write('\n')
#
#def update_email(address):
#    address["email"] = address["email"].split("_")[0] + "@" + address["email"].split("@")[1]
#    return address
#
#with open("Trello/AndyList-100k - updates.json") as leads:
#    lead_list = leads.readlines()
#    lead_list = list(map(json.loads, lead_list))
#    lead_list = list(map(update_email, lead_list))
    
#lead_list = []
#for ii in range(1000260,1100260):
#    lead_list.append({"id": ii, "lastName": "Random"})
#
#with open("Trello/update100k.json") as in_leads:
#    leads = in_leads.readlines()
#    leads = list(map(json.loads, leads))
#    leads = list(map(add_partition, leads))
#
#with open("Trello/Carter/update100k.json", "w") as out_leads:
#    out_leads.write("\n".join(list(map(json.dumps, leads))))

with open("Trello/leads-100.json") as data:
    results = data.readlines()
    results = list(map(json.loads, results))
    
    for result in results:
        result["mean_time"] = mean(result["execution_times"])
    
with open("Trello/leads-100.json", "w") as out_data:
    out_data.write("\n".join(list(map(json.dumps, results))))
    
    