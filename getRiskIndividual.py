from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WEIGHTS = {"age":4,"proximity_factor":2,"gender":1,"nearby_infected_individuals":20,"infectiousness":4}# age,proximity,gender
normalization_factor = np.sum(list(WEIGHTS.values()))
gender_factor_list = [0.42,1.00] # female, male'''



def getData():

    age_vs_deathRate = pd.read_csv("data/age_vs_deathRate.csv")

    gender_vs_deathRate = pd.read_csv("data/gender_vs_deathRate.csv")

    gender_factor_list = gender_vs_deathRate["death_rate"].values / np.max(gender_vs_deathRate["death_rate"].values)
    #print("gender_factor_list",gender_factor_list)

    age_risk_factor_list = age_vs_deathRate["death_rate"].values / np.max(age_vs_deathRate["death_rate"].values)

    ages = age_vs_deathRate["age_bin"].values

    # con.close()

    return ages, age_risk_factor_list, gender_factor_list


ages,age_risk_factor_list,gender_factor_list = getData() # fetch the data from transcend

f_age = interp1d(ages,age_risk_factor_list,kind='cubic') # a continuous function for age


def get_infectiousness(x):
    w_shape = 2.83
    w_scale = 5.67
    return (w_shape / w_scale) * (x / w_scale)**(w_shape - 1) * np.exp(-(x / w_scale)**w_shape)


def get_risk_due_to_density(x):
    sigmoid = 1 / (1 + np.exp(-0.1*x))
    return (sigmoid-0.5)/0.5

def get_risk_shape_factor(x): # at which x value do we get risk value of 0.9
    desired_risk = 0.99
    return np.log((2/(1+(desired_risk)) - 1))/(-x)

def get_risk_generic(factor,x):
    sigmoid = 1 / (1 + np.exp(-factor*x))
    return (sigmoid-0.5)/0.5

def get_risk_due_to_nearby_infected_individuals(x):
    sigmoid = 1 / (1 + np.exp(-0.5*x))
    return (sigmoid-0.5)/0.5


def getRiskIndividual(age,number_of_people_around,gender=None,nearby_infected_individuals=None,infectiousness=None):# TO INCREASE WITH NUMBER OF INFECTED INDIVIDUALS AROUND LATER
    normalization_factor = np.sum(list(WEIGHTS.values()))
    
    if gender=="male":
        gender_factor = gender_factor_list[1]
    elif gender == "female":
        gender_factor = gender_factor_list[0]
    else:
        gender_factor = 0
        normalization_factor = normalization_factor - WEIGHTS["gender"]

    
    if age<=80:
        age_factor = np.max([f_age(age),0])
    else:
        age_factor = 1
    
    
    proximity_factor = get_risk_due_to_density(number_of_people_around)

    if nearby_infected_individuals == None:
        normalization_factor = normalization_factor - WEIGHTS["nearby_infected_individuals"]
        infected_individuals_factor = 0
    else:
        infected_individuals_factor = get_risk_due_to_nearby_infected_individuals(nearby_infected_individuals)
    
    if infectiousness == None:
        normalization_factor = normalization_factor - WEIGHTS["infectiousness"]
        infectiousness_factor = 0
    else:
        infectiousness_factor = min(infectiousness/0.2,1.0) # assuming max infection prob can be around 0.2
    
    
    
    risk = (WEIGHTS["age"]*age_factor + 
            WEIGHTS["proximity_factor"]*proximity_factor +
            WEIGHTS["gender"]*gender_factor + 
            WEIGHTS["nearby_infected_individuals"]*infected_individuals_factor + 
            WEIGHTS["infectiousness"]*infectiousness_factor
            )/normalization_factor

    return risk
    

def get_geo_risk(avg_age,avg_gender,avg_days_since_infection,number_of_people_around,nearby_infected_individuals):


    if avg_age<=80:
        age_factor = np.max([f_age(avg_age),0])
    else:
        age_factor = 1

    gender_factor = gender_factor_list[0] + avg_gender * (gender_factor_list[1] - gender_factor_list[0])

    proximity_factor = get_risk_due_to_density(number_of_people_around)

    infected_individuals_factor = get_risk_due_to_nearby_infected_individuals(nearby_infected_individuals)


    infectiousness_factor = min(get_infectiousness(avg_days_since_infection) / 0.2, 1.0)

    risk = (WEIGHTS["age"] * age_factor +
            WEIGHTS["proximity_factor"] * proximity_factor +
            WEIGHTS["gender"] * gender_factor +
            WEIGHTS["nearby_infected_individuals"] * infected_individuals_factor +
            WEIGHTS["infectiousness"] * infectiousness_factor
            ) / normalization_factor

    return risk,age_factor,gender_factor,proximity_factor,infected_individuals_factor,infectiousness_factor


##### Testing code and code for plotting the risk factors #####
if __name__ == "__main__":

    FIGSIZE=[12,8]
    plt.rcParams.update({"font.size": 30})

    print(get_geo_risk(60,1,5,10,1))
    age_factor = f_age(np.arange(5,80))
    age_factor[age_factor<0] = 0


    # to run the below code, first create  directory called "risk_model"

    plt.figure(figsize=FIGSIZE)
    plt.plot(np.arange(5,80),age_factor,c='#4b5d67')
    plt.xlabel("Age")
    plt.ylabel("Risk due to Age")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/age.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.bar([1,2],gender_factor_list,color='#4b5d67')
    xticks,xticklabels = plt.xticks()
    plt.xticks([1,2],["female","male"])
    plt.xlabel("Gender")
    plt.ylabel("Risk due to Gender")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/gender.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.plot(np.arange(0, 50, 0.2), get_risk_due_to_density(np.arange(0, 50, 0.2)),c='#00bcd4')
    plt.xlabel("Number of Individuals (Proximity)")
    plt.ylabel("Risk due to Proximity")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/proximity.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.plot(np.arange(0, 50, 0.2), get_risk_due_to_nearby_infected_individuals(np.arange(0, 50, 0.2)),c='#00bcd4')
    plt.xlabel("Number of Near by Individuals (Proximity to Infected)")
    plt.ylabel("Risk due to Proximity to Infected")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/proximity_infected.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.plot(np.arange(0,30,0.2),get_infectiousness(np.arange(0,30,0.2))/0.12,c='#00bcd4')
    plt.xlabel("Days since infection")
    plt.ylabel("Risk to Infectiousness")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/infectiousness.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.bar([0,1,2,3,4,5],[0.28,0.28,0.34,0.48,0.49,1.0],color='#4b5d67')
    plt.xticks([0, 1, 2, 3, 4, 5], ["Cardiovascular", "Diabetes", "Respiratory","Obesity","Hypertension", "Multiple"],rotation=45)
    plt.ylabel("Risk due to Comorbidity")
    plt.subplots_adjust(bottom=0.33)
    plt.savefig("risk_model/comorbidity.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.bar([0, 1, 2], [1, 0.5, 0],color='#4b5d67')
    plt.xticks([0, 1, 2], ["Health worker", "Other job", "No Job or\nRemote worker"])
    plt.ylabel("Risk due to Type of Job")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/type_of_job.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.bar([0, 1], [0.35, 1.0],color='#48C9B0')#color='#eebb4d')
    plt.xticks([0, 1], ["Wears a mask", "Does not wear a mask"])
    plt.ylabel("Risk due to Mask compliance")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/mask_wearing.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.plot(np.arange(0, 30, 0.2), get_risk_generic(0.5, np.arange(0, 30, 0.2)),c='#4b5d67')
    plt.xlabel("Household size")
    plt.ylabel("Risk due to Household size")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/household_size.png",transparent=True)

    plt.figure(figsize=FIGSIZE)
    plt.plot(np.arange(0, 3, 0.1), get_risk_generic(5.29, np.arange(0, 3, 0.1)),c='#00bcd4')
    plt.xlabel("Exposure time (hours)")
    plt.ylabel("Risk due to Exposure")
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("risk_model/exposure.png",transparent=True)

