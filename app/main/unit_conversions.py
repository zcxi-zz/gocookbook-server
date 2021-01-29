import math
from . import main
from ..user import get_user_volume_preference, get_user_mass_preference

@main.context_processor
def volume_conversion_processor():
    def template_get_user_volume_preference_string(userID, volume):
        return get_user_volume_preference_string(userID, volume)
    return {'template_get_user_volume_preference_string' : template_get_user_volume_preference_string}

@main.context_processor
def mass_conversion_processor():
    def template_get_user_mass_preference_string(userID, volume):
        return get_user_mass_preference_string(userID, volume)
    return {'template_get_user_mass_preference_string' : template_get_user_mass_preference_string}

def metric_to_spoons_volume(volume):
    numQuarterCups = math.floor(volume / 62.5)
    cupRemainder = volume - 62.5 * numQuarterCups
    numCups = numQuarterCups // 4
    numQuarterCups = numQuarterCups - 4 * numCups
    numTeaSpoon = cupRemainder / (4.92892)
    numTbSpoon = math.floor(numTeaSpoon / 3)
    numTeaSpoon = numTeaSpoon - 3 * numTbSpoon
    numTeaSpoon = round(numTeaSpoon * 4) / 4
    return numCups, numQuarterCups, numTbSpoon, numTeaSpoon

def spoons_to_metric_volume(numCups, numQuarterCups, numTbSpoon, numTeaSpoon):
    return numCups * 250 + numQuarterCups * 62.5 + numTbSpoon * (62.5 / 4) + numTeaSpoon * (4.92892)

def metric_to_imp_mass(mass):
    numOz = mass / 28.35
    numPound = math.floor(numOz / 16)
    numOz = numOz - 16 * numPound
    return numPound, numOz

def imp_to_metric_mass(numPound, numOz):
    return 16 * numPound * 28.35 + numOz * 28.35


def get_user_volume_preference_string(userID, volume):
    if userID != 0:
        if get_user_volume_preference(userID):
            returnString = "{:0.2f} ml"
            returnString = returnString.format(volume)
            return returnString
        else:
            cups, quarterCups, tbsps, tsps = metric_to_spoons_volume(volume)
            returnString = ""
            first = True
            if cups > 0:
                if cups != 1:
                    returnString = returnString + "{} cups"
                else:
                    returnString = returnString + "{} cup"
                returnString = returnString.format(cups)
                first = False
            if quarterCups > 0:
                if not first:
                    returnString = returnString + ", "
                if quarterCups % 2 != 0:
                    if quarterCups != 1:
                        returnString = returnString + "{} quarter cups"
                    else:
                        returnString = returnString + "{} quarter cup"
                    first = False
                    returnString = returnString.format(quarterCups)
                else:
                    first = False
                    returnString = returnString + "1 half cup"
            if tbsps > 0:
                if not first:
                    returnString = returnString + ", "
                if tbsps != 1:
                    returnString = returnString + "{} tablespoons"
                else:
                    returnString = returnString + "{} tablespoon"
                first = False
                returnString = returnString.format(tbsps)
            if tsps > 0:
                if not first:
                    returnString = returnString + ", "
                if tsps != 1:
                    returnString = returnString + "{} teaspoons"
                else:
                    returnString = returnString + "{} teaspoon"
                first = False
                returnString = returnString.format(tsps)
            return returnString
    else:
        returnString = "{:0.2f} ml"
        returnString = returnString.format(volume)
        return returnString

def get_user_mass_preference_string(userID, mass):
    if userID != 0:
        if get_user_mass_preference(userID):
            returnString = "{:0.2f} g"
            returnString = returnString.format(mass)
            return returnString
        else:
            pounds, oz = metric_to_imp_mass(mass)
            returnString = ""
            first = True
            if pounds > 0:
                if pounds != 1:
                    returnString = returnString + "{} lbs"
                else:
                    returnString = returnString + "{} lb"
                first = False
                returnString = returnString.format(pounds)
            if oz > 0:
                if not first:
                    returnString = returnString + " and "
                if oz != 1:
                    returnString = returnString + "{:0.2f} ozs"
                else:
                    returnString = returnString + "{:0.2f} oz"
                returnString = returnString.format(oz)
            return returnString
    else:
        returnString = "{:0.2f} g"
        returnString = returnString.format(mass)
        return returnString