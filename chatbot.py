import aiml
import os
import requests
import json

## Frankie Antenucci Final Project

# Setting up caching
CACHE_FNAME = 'cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    cache_file.close()
    CACHE_DICTION = json.loads(cache_contents)
except:
    CACHE_DICTION = {}


# Defining the caching function
def getWithCaching(baseURL, params = {}):
    req = requests.Request(method = 'GET', url = baseURL, params = sorted(params.items()))
    prepped = req.prepare()
    fullURL = prepped.url
    if fullURL not in CACHE_DICTION:
        response = requests.Session().send(prepped)
        CACHE_DICTION[fullURL] = response.text

        cache_file = open(CACHE_FNAME, 'w')
        cache_file.write(json.dumps(CACHE_DICTION))
        cache_file.close()
    return CACHE_DICTION[fullURL]


# kernel is responsible for responding to users
kernel = aiml.Kernel()

# load every aiml file in the 'standard' directory
# use os.listdir and a for loop to do this
for file in os.listdir('aiml_data')[1:]:
    kernel.learn(os.path.join('aiml_data', file))
kernel.learn(os.path.join('aiml_data', 'std-hello.aiml'))


# Defining the function to request from Google API
def googleRequest(city):
    try:
        google_full_url = 'https://maps.googleapis.com/maps/api/geocode/json'
        google_api_key = 'AIzaSyAd8j4NqjAzv69R_RPtQL37t85woMOxfa0'
        param = {'address': city, 'key': google_api_key}
        google_cache = getWithCaching(google_full_url, params = param)
        google_data = json.loads(google_cache)
        # print json.dumps(google_data, indent = 4)
        coordinates = (google_data['results'][0]['geometry']['location']['lat'], google_data['results'][0]['geometry']['location']['lng'])
        return coordinates
    except:
        return 'Is {} a city?'.format(city)


# Defining the function to request from the DarkSky API
def darkskyRequest(city):
    try:
        lat_lng = googleRequest(city)
        darksky_base_url = 'https://api.darksky.net/forecast/'
        darksky_api_key = 'fef8167470b82d6fd2b27d0d9ff19d88'
        darksky_full_url = darksky_base_url + darksky_api_key + '/' + str(lat_lng[0]) + ',' + str(lat_lng[1])
        darksky_cache = getWithCaching(darksky_full_url)
        darksky_data = json.loads(darksky_cache)
        # print json.dumps(darksky_data, indent = 4)
        return darksky_data
    except:
        return "Sorry, I don't know"


# Answering 'What's the weather lik in {city}?
def getWeatherCurrently(city):
    try:
        my_city = darkskyRequest(city)
        current_temp = my_city['currently']['apparentTemperature']
        condition = my_city['currently']['summary']
        return ('In {}, it is {} and {}'.format(city, current_temp, condition))
    except:
        return 'Is {} a city?'.format(city)
kernel.addPattern("What's the weather like in {city}?", getWeatherCurrently)


# Answering 'How hot will it get in {city} today?'
def getMaxTempToday(city):
    try:
        my_city = darkskyRequest(city)
        temp_max = my_city['daily']['data'][0]['temperatureMax']
        return ('In {} it will reach {}'.format(city, temp_max))
    except:
        return 'Is {} a city?'.format(city)
kernel.addPattern('How hot will it get in {city} today?', getMaxTempToday)


# Answering 'How cold will it get in {city} today?'
def getMinTempToday(city):
    try:
        my_city = darkskyRequest(city)
        temp_min = my_city['daily']['data'][0]['temperatureMin']
        return ('In {} the low will be {}'.format(city, temp_min))
    except:
        return 'Is {} a city?'.format(city)
kernel.addPattern('How cold will it get in {city} today?', getMinTempToday)


# Answering 'Is it going to rain in {city} today?'
def rainToday(city):
    try:
        my_city = darkskyRequest(city)
        rain_prob = my_city['currently']['precipProbability']
        if rain_prob < 0.1:
            return 'It almost definitely will not rain in {}'.format(city)
        elif rain_prob >= 0.1 and rain_prob < 0.5:
            return 'It probably will not rain in {}'.format(city)
        elif rain_prob >= 0.5 and rain_prob < 0.9:
            return 'It probably will rain in {}'.format(city)
        elif rain_prob >= 0.9:
            return 'It will almost definitely rain in {}'.format(city)
    except:
        return 'Is {} a city?'.format(city)
kernel.addPattern('Is it going to rain in {city} today?', rainToday)


# Answering 'How hot will it get in {city} this week?'
def getMaxTempWeek(city):
    try:
        temp_data = darkskyRequest(city)['daily']['data']
        week_max_temp = temp_data[0]['temperatureMax']
        for day in range(1,8):
            if temp_data[day]['temperatureMax'] > week_max_temp:
                week_max_temp = temp_data[day]['temperatureMax']
        return 'In {} it will reach {}'.format(city, week_max_temp)
    except:
        return 'Is {} a city?'.format(city)
kernel.addPattern('How hot will it get in {city} this week?', getMaxTempWeek)


# Answering 'How cold will it get in {city} this week?'
def getMinTempWeek(city):
    try:
        temp_data = darkskyRequest(city)['daily']['data']
        week_min_temp = temp_data[0]['temperatureMin']
        for day in range(1,8):
            if temp_data[day]['temperatureMin'] < week_min_temp:
                week_min_temp = temp_data[day]['temperatureMin']
        return 'In {} it will reach {}'.format(city, week_min_temp)
    except:
        return 'Is {} a city?'.format(city)
kernel.addPattern('How cold will it get in {city} this week?', getMinTempWeek)


# Answering 'Is it going to rain in {city} this week?'
def rainWeek(city):
    try:
        rain_data = darkskyRequest(city)['daily']['data']
        week_prob = (1 - rain_data[0]['precipProbability'])
        for day in range(1,8):
            week_prob *= (1 - rain_data[day]['precipProbability'])
        week_data = 1 - week_prob
        if week_data < 0.1:
            return 'It almost definitely will not rain in {} this week'.format(city)
        elif week_data >= 0.1 and week_data < 0.5:
            return 'It probably will not rain in {} this week'.format(city)
        elif week_data >= 0.5 and week_data < 0.9:
            return 'It probably will rain in {} this week'.format(city)
        elif week_data >= 0.9:
            return 'It will almost definitely rain in {} this week'.format(city)
    except:
        return 'Is {} a city?'.format(city)
kernel.addPattern('Is it going to rain in {city} this week?', rainWeek)


user_input = ''
while user_input != 'exit':
    user_input = raw_input('> ')
    print kernel.respond(user_input)


# add a new response for when the user says "example * and *"
# note that the ARGUMENT NAMES (first and second) must match up with
# the names in kernel.addPattern
def myExampleResponse(city, state):
    return '{}, eh? Do you like it in {}?'.format(state, city)
kernel.addPattern('I live in {city}, {state}', myExampleResponse)


# get a few example responses
print('Example queries:\n')
queries = ['hello', 'Francesca', 'I live in Ann Arbor, Michigan', "What's the weather like in Ann Arbor?", 'Is it going to rain in Ypsilanti today?', 'How hot will it get in Detroit today?', 'How cold will it get in Flint today?', 'Is it going to rain in East Lansing this week?', 'How hot will it get in Grand Rapids this week?', 'How cold will it get in Kalamazoo this week?']
for q in queries:
    print('> {}'.format(q))
    print('...{}\n'.format(kernel.respond(q)))
