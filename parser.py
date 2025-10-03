from datetime import datetime
import rule
import female

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
    
    def isValid(self) -> bool:
        # Filter the activity for valid date, pace here
        # Return true if valid, otherwise false
        return True

    ################################
    # Parse from csv file
    def parse(athlete_id: str, id: str, type: str, location: str, athlete_name:str, date: str, distance: str, pace: str, unit: str, duration: str):
        # Activity ID
        if "/activities/" in id and "/athletes/" in athlete_id:
            self_id = id
            self_athlete_id = athlete_id
        else:
            print("DBG: Invalid activity ID")
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
            m, s = map(int, pace.split(":"))
            self_pace = m + (s / 60)
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
        if not activity.isValid():
            print("Invalid activity")
            return

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
            km += act.distance
        self.total_distance = km
        return km

class AthleteList:
    def __init__(self):
        self.athlete_list = []

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



class Rule:
    # Return True on valid data, False on invalid

    # Check the activity data is not before start date and after end date
    def check_activity_date(activity: Activity):
        if datetime.fromisoformat(rule.START_DATE) <= activity.startdate <= datetime.fromisoformat(rule.END_DATE):
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


########################################################################################
import os
import csv

if __name__ == "__main__":
    csv_list = []
    athlete_list = AthleteList()
    for filename in os.listdir('./CSV'):
        if filename.endswith(".csv"):
            csv_list.append("./CSV/" + filename)

    for csvfile in csv_list:
        with open(csvfile, "r", newline="", encoding='utf-8') as f:
            print("File: ", csvfile)
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
                    Rule.check_min_distance(act):
                        athlete_list.add_actitvity(act)
                else:
                    print("Violated activity detected. Row: ", r)
                    continue

                print("Row: ", r)
                print("Who: {}, ID: {}  , Type: {} , Distance: {},  Pace: {} , Date: {}\n".format(act.athlete_name, act.id, act.type, act.distance, act.pace, act.startdate))
    
    print("################")
    # Sort athlete by Gender
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
    

