from datetime import datetime, tzinfo
import rule
import female
import groups

# Treat all activities as Running
class Activity:
    valid_type = ("Run", "Trail Run")
    def __init__(self):
        self.id = ""    # /activities/1234567890
        self.athlete_id = "" # /athletes/1234567890
        self.athlete_name = ""
        self.type = ""
        self.distance = 0 # km
        self.pace = 0.0 # min/km
        self.startdate = None # datetime obj
        self.validity = None # True if the activity is valid
    
    ################################
    # Parse from csv file
    def parse(athlete_id: str, id: str, type: str, location: str, athlete_name:str, date: str, distance: str, pace: str, unit: str, duration: str):
        # Activity ID
        if "/activities/" in id and "/athletes/" in athlete_id:
            self_id = id
            self_athlete_id = athlete_id
        else:
            print("DBG: Invalid activity ID or athletes ")
            return None
        if not distance:
            print("DBG: Invalid distance")
            return None
        
        # Activity type ==> No need to check, Club is already for running
        # Get the type to check pace rule only
        self_type = ""
        if type in Activity.valid_type:
            self_type = type
        elif type == "unknown":
            unknown_type_list = ["Morning Run", "Afternoon Run", "Evening Run", "Morning Trail Run", "Afternoon Trail Run", "Evening Trail Run"]
            for ukwn_type in unknown_type_list:
                if ukwn_type in location:
                    self_type = ukwn_type
                    break
            self_type = "Run"
        else:
            print("DBG: Type {} not found. Check manually.".format(type))
            self_type = "Run"
        
        # Date
        self_startdate = datetime.fromisoformat(date)

        # Distance
        distance_float = 0
        if unit == "m":
            distance_float = float(distance) / 1000.0
        else: # km
            distance_float = float(distance)

        # Pace
        if pace != "":
            h = 0
            if len (pace.split(":")) > 2: 
                h, m, s = map(int, pace.split(":"))
            else: 
                m, s = map(int, pace.split(":"))
            self_pace =  h * 60 + m + (s / 60)
        else:
            # Split into hours, minutes, seconds
            h, m, s = map(int, duration.split(":"))
            minute = h * 60 + m + s / 60
            self_pace = minute / distance_float
        
        activity = Activity()
        activity.athlete_id = self_athlete_id
        activity.id = self_id
        activity.type = self_type
        activity.athlete_name = athlete_name
        activity.distance = distance_float
        activity.startdate = self_startdate
        activity.pace = self_pace

        return activity


class Athlete:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.gender = "male"
        self.activities = []
        self.total_distance = 0
    
    def add_activity(self, activity: Activity):
        for act in self.activities:
            if act.id == activity.id:
                print("Duplicated activity")
                return

        # Add valid activity
        self.activities.append(activity)

    # Return total km of an athlete
    def calc_total_km(self) -> float:
        km = 0.0
        for act in self.activities:
            if act.validity == True:
                km += act.distance
        self.total_distance = round(km, 2)
        return self.total_distance

class AthleteList:
    def __init__(self):
        self.list_name = ""
        self.athlete_list = []
        self.total_distance = 0.0
        # Contain member name list in case of listing all group members
        self.member_name_list = []

    # Make object interable
    def __iter__(self):
        return iter(self.athlete_list)

    # Add an athlete to the list
    def __add_athlete(self, athlete: Athlete):
        self.athlete_list.append(athlete)
    
    # Add an activity to the athlete in the list. If the athlete does not exist, create one
    def add_actitvity(self, activity: Activity):
        # Find the athlete
        for ath in self.athlete_list:
            # Athlete exist
            if activity.athlete_id == ath.id:
                # Search for duplicated activity
                for act in ath.activities:
                    if act.id == activity.id:
                        return # Exit the loop without executing else block
                # No duplicated activity found, add this one
                else:
                    ath.add_activity(activity)
                    break

        # Athlete not exist. Add one and add their activity
        else:
            print("New athlete: {}".format(activity.athlete_name))
            new_athlete = Athlete(activity.athlete_id, activity.athlete_name)
            new_athlete.activities.append(activity)
            self.__add_athlete(new_athlete)
    
    def calc_total_km(self) -> float:
        km = 0.0
        for ath in self.athlete_list:
            ath.calc_total_km()
            km += ath.total_distance
        self.total_distance = round(km, 2)
        return self.total_distance

    def initialize_name_list(self):
        all_member_id = groups.groups[self.list_name]
        for mem_id in all_member_id:
            self.member_name_list.append(groups.members[mem_id])



class Rule:
    # Return True on valid data, False on invalid

    # Check the activity data is not before start date and after end date
    def check_activity_date(activity: Activity):
        if datetime.fromisoformat(rule.START_DATE) <= activity.startdate < datetime.fromisoformat(rule.END_DATE):
            return True
        else:
            print("Activity out of start and end date")
            return False

    # Pace must be within a valid range
    def check_pace(activity: Activity):
        pace = float(activity.pace)
        if "Trail Run" in activity.type:
            if rule.MIN_PACE_TRAIL_RUN < pace < rule.MAX_PACE_TRAIL_RUN:
                return True
        elif "Run" in activity.type:
            if rule.MIN_PACE_RUN < pace < rule.MAX_PACE_RUN:
                return True
        else:
            # Should not reach this case
            pass
        print("Pace {} is not valid for {}".format(pace, activity.type))
        return False
    def check_min_distance(activity: Activity):
        if activity.distance < rule.MIN_DISTANCE:
            return False
        else:
            return True
    def check_valid_activity(activity: Activity):
        #print (activity.id)
        if activity.id in rule.acception_activity_list:
            print ("invalid activities", activity.id, activity.athlete_name)
            return False
        else:
            return True


########################################################################################
import os
import csv
import json
import glob

def sort_athlete_by_distance(athlete_list: AthleteList) -> tuple[AthleteList, AthleteList]:
    male_athletes = []
    female_athletes = []
    for athlete in athlete_list:
        athlete.calc_total_km()
        if athlete.id in female.female_list:
            female_athletes.append(athlete)
        else:
            male_athletes.append(athlete)


    print("****** RESULT MALE *******")
    sorted_male = sorted(male_athletes, key=lambda athlete: athlete.total_distance, reverse=True)
    for athlete in sorted_male:
        print("ID: {}, Name: {}, Total km: {}".format(athlete.id, athlete.name, athlete.total_distance))


    print("****** RESULT FEMALE *******")
    sorted_female = sorted(female_athletes, key=lambda athlete: athlete.total_distance, reverse=True)
    for athlete in sorted_female:
        print("ID: {}, Name: {}, Total km: {}".format(athlete.id, athlete.name, athlete.total_distance))
    
    return male_athletes, female_athletes



def sort_group_by_distance(athlete_list: AthleteList) -> list:
    group_list = []
    for group_name, athlete_ids in groups.groups.items():
        curr_group = AthleteList()

        # Add athletes to the groups
        for athlete in athlete_list:
            if athlete.id in athlete_ids:
                curr_group.athlete_list.append(athlete)
        curr_group.calc_total_km()
        curr_group.list_name = group_name
        group_list.append(curr_group)

    print("****** RESULT GROUP *******")
    sorted_group = sorted(group_list, key=lambda group: group.total_distance, reverse=True)
    
    # Print group name, group total distance and members
    for group in sorted_group:
        print("Group: {}, Total km: {}".format(group.list_name, group.total_distance))
        for ath in group.athlete_list:
            print("   ID: {}, Name: {}, Total km: {}".format(ath.id, ath.name, ath.total_distance))
        print("")
    
    return group_list

def export_json_personal(ath_list, file_name) -> list:
    ath_json = []
    for ath in ath_list:
        ath_json.append({"id": ath.id.replace('/', '_'), "name": ath.name, "distance": ath.total_distance })
    with open(file_name, "w", encoding="utf-8") as f:
        json_text = json.dumps(ath_json, ensure_ascii=False)
        f.write(json_text)
    
    return ath_json

#####################################################################################
if __name__ == "__main__":
    latest_csv_date = datetime.fromisoformat("2025-10-08T00:00:00.000+07:00")
    csv_list = []
    athlete_list = AthleteList()
    for filename in os.listdir('./CSV'):
        if filename.endswith(".csv"):
            csv_list.append("./CSV/" + filename)
        # Parse datetime from file name
        data, year, month, day, hour = filename.split('.')[0].split('-') # Example: data-2025-10-08-11.csv
        curr_date = datetime(year=int(year), month=int(month), day=int(day), hour=int(hour), tzinfo=latest_csv_date.tzinfo)
        if curr_date > latest_csv_date:
            latest_csv_date = curr_date

    for csvfile in csv_list:
        with open(csvfile, "r", newline="", encoding='utf-8') as f:
            print("\n\nFile: ", csvfile)
            reader = csv.reader(f)        
            # Convert to a list to access by index
            rows = list(reader)

            r = 1
            for row in rows[1:]:
                r += 1
                # "Athlete","Activity", "Type","Location","Name","Date","Distance","Pace","Unit","Duration","Elev","Calo","EstPace","EstSpeed"
                act = Activity.parse(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
                if act == None:
                    print("Cannot parse this activity. Row: ", r)
                    continue
                
                # Check for rule
                if  Rule.check_activity_date(act) and \
                    Rule.check_pace(act) and \
                    Rule.check_min_distance(act) and  \
                    Rule.check_valid_activity(act) :
                        act.validity = True
                        athlete_list.add_actitvity(act)
                else:
                    print("Violated activity detected. Row: ", r)
                    act.validity = False
                    athlete_list.add_actitvity(act)
                    continue

                #print("Row: ", r)
                #print("Who: {}, ID: {}  , Type: {} , Distance: {},  Pace: {} , Date: {}\n".format(act.athlete_name, act.id, act.type, act.distance, act.pace, act.startdate))
    
    print("################\n\n")
    # Sort athlete by Gender
    male_list, female_list = sort_athlete_by_distance(athlete_list)
    print("")
    group_list = sort_group_by_distance(athlete_list)

    male_json = export_json_personal(male_list, "./web/male.json")
    female_json = export_json_personal(female_list, "./web/female.json")

    grp_json = []
    for group in group_list:
        group.initialize_name_list()
        json_obj = {
            "name": group.list_name,
            "distance": group.total_distance,
            "members": group.member_name_list 
        }
        grp_json.append(json_obj)
    with open("./web/group.json", "w", encoding="utf-8") as f:
        json_text = json.dumps(grp_json, ensure_ascii=False)
        f.write(json_text)

    
    # Get today's date in DD-MM-YYYY format
    today_date = latest_csv_date.strftime('%H:%M, %d-%m-%Y')
    # Create a dictionary with the date
    data = { "updateDate": today_date }
    # Save the dictionary to a JSON file
    with open("./web/update_date.json", "w") as json_file:
        json.dump(data, json_file, indent=2)

############################################################################################
    # Export detail activities of each athlete
    os.makedirs("./web/detail", exist_ok=True)
    files = glob.glob('./web/detail/*')
    for f in files:
        os.remove(f)

    for ath in male_list + female_list:
        json_data = { "name": ath.name }
        json_name = ath.id.replace('/', '_')
        json_activity_list = []
        # Sort activity by date
        for act in sorted(ath.activities, key=lambda act: act.startdate):
            json_act = {
                "id": act.id,
                "type": act.type,
                "date": act.startdate.strftime('%d-%m-%Y'),
                "distance": act.distance,
                "pace": act.pace,
                "validity": act.validity
            }
            json_activity_list.append(json_act)
        
        json_data["activities"] = json_activity_list
        with open("./web/detail/" + json_name + ".json", "w") as json_file:
            json.dump(json_data, json_file, indent=2)

############################################################################################
# For fun
############################################################################################

    all_km = 0
    for ath in athlete_list:
        all_km += ath.total_distance
    with open("./web/total_km.json", "w") as json_file:
        json_obj = {"total_km": round(all_km, 2) }
        json.dump(json_obj, json_file)
    
    print("TOTAL KM: ", all_km)