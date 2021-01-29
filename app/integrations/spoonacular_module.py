import requests
import os
from config import Config

class spoonacular_module:

    def __init__(self,):

        self.baseUrl = 'https://api.spoonacular.com'
        self.userName = os.environ.get('SPOONACULAR_USER')
        self.secret = Config.SPOONACULAR_SECRET
        #categories
        self.recipeEndPoint = '/recipes'
        
        #functions
        self.autoCompleteFunction = '/autocomplete'
        self.getRecipeBulkFunction = '/informationBulk'
    def get_recipes_by_keyword(self, queryString, numResults):
        
        endpoint = self.baseUrl + self.recipeEndPoint
        
        queryEndpoint = endpoint + self.autoCompleteFunction + '?apiKey=' + str(self.secret) + '&query=' + queryString + '&number=' + str(numResults)
        response = requests.get(queryEndpoint).json()

        bulkRecipeEndPoint = endpoint + self.getRecipeBulkFunction + '?apiKey=' + str(self.secret) + '&ids='
        for recipe in response:
            if 'id' in recipe:
                bulkRecipeEndPoint += str(recipe['id']) + ','
        bulkRecipeEndPoint += '&includeNutrition=false'
        response = requests.get(bulkRecipeEndPoint).json()

        return response['recipes']

    def get_random_recipes(self, tag):

        endpoint = self.baseUrl + self.recipeEndPoint + '/random'

        queryEndpoint = endpoint + '?apiKey=' + str(self.secret) + '&number=100&tags=' + tag
        response = requests.get(queryEndpoint).json()
        return response['recipes']