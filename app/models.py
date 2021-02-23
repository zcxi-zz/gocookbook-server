from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from app.integrations.spoonacular_module import spoonacular_module


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    recipes = db.relationship('RU_Association')
    prefers_metric_volume = db.Column(db.Boolean, default=True)
    prefers_metric_mass = db.Column(db.Boolean, default=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




def get_user_volume_preference(user_id):
    selectUser = User.query.get(int(user_id))
    if selectUser is not None:
        return selectUser.prefers_metric_volume
    else:
        return True

def get_user_mass_preference(user_id):
    selectUser = User.query.get(int(user_id))
    if selectUser is not None:
        return selectUser.prefers_metric_mass
    else:
        return True


# Association table for user recipe relations
class RU_Association(db.Model):
    __tablename__ = "RU"
    r_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), primary_key=True)
    u_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    saved = db.Column(db.Boolean)
    rating = db.Column(db.Float)
    review = db.Column(db.String(500))
    recipe = db.relationship("Recipe")
    user = db.relationship("User")

# Use Association Table for many-to-many relationship btwn recipes and ingredients
# 3rd column is the amounts required
class RI_Association(db.Model):
    __tablename__ = "RI"
    r_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), primary_key=True)
    i_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), primary_key=True)
    amount = db.Column(db.Float)
    recipe = db.relationship("Recipe")
    ingredient = db.relationship("Ingredient")

class Recipe(db.Model):
    __tablename__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    time = db.Column(db.Integer)
    rating = db.Column(db.Float)
    description = db.Column(db.String(500))
    steps = db.Column(db.String(500)) # temporary. replace with enum maybe
    #ingredients = db.relationship('Ingredient',secondary=RI_Association)
    ingredients = db.relationship('RI_Association')
    users = db.relationship('RU_Association')

class Recipe_val():
    def __init__(self, recipe):
        self.name = recipe.name
        self.time = recipe.time
        self.rating = recipe.rating
        self.description = recipe.description
        self.steps = recipe.steps.split("\n") # we want a list of steps
        self.ingredients = [ingredient.ingredient for ingredient in recipe.ingredients]
        self.amounts = [ingredient.amount for ingredient in recipe.ingredients]

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    # determine what type of unit to use (volume, units, mass, etc)
    measure = db.Column(db.String(64))

def get_ingredient_is_countable(id):
    if (db.session.query(Ingredient).filter(id=id, measure='count').first()) != None:
        return False
    return True

def get_all_ingredients(descend=False): 
    ingredients = db.session.query(Ingredient).order_by(Ingredient.name).with_entities(Ingredient.id, Ingredient.name).all()
    return ingredients

def search_ingredients(phrase):
    ingredients = db.session.query(Ingredient).order_by(Ingredient.name).filter(Ingredient.name.like("%{}%".format(phrase)))
    return ingredients

def get_all_recipes(descend=False):
     recipes = db.session.query(Recipe).order_by(Recipe.name).with_entities(Recipe.id, Recipe.name).all()
     return recipes

def add_ingredient(name, measure):
    ingredient = Ingredient(name=name, measure=measure)
    db.session.add(ingredient)
    db.session.commit()
    return ingredient.id

def get_recipe(id):
    r_query = db.session.query(Recipe).get(id)
    recipe = Recipe_val(r_query)
    return recipe

def get_ingredient(id):
    ingredient = db.session.query(Ingredient).get(id)
    return ingredient

def get_ingredient_name(id):
    ingredient = db.session.query(Ingredient).get(id)
    return ingredient.name

def get_ingredient_by_name(name):
    return db.session.query(Ingredient).filter_by(name = name).first()

def get_ingredient_measure(id):
    ingredient = db.session.query(Ingredient).get(id)
    return ingredient.measure

def reset_database():
    db.session.rollback()
    db.drop_all()
    db.create_all()

def populate_with_dummy_data():
    add_ingredient("carrots", "units")
    add_ingredient("lettuce", "units")
    add_ingredient("mushrooms", "units")
    add_ingredient("cucumber", "units")
    add_ingredient("ranch dressing", "volume")
    add_ingredient("water", "volume")
    add_ingredient("salt", "mass")

    add_recipe("salt water", 420, "1. add water\n2. add salt", 
              [(6,0,10,0),(7,0,1,0)])
    add_recipe("salad", 360, "1. add vegetables into bowl\n2. mix\n3. add dressing", 
              [(1,0,5,0),(2,0,5,0),(3,0,5,0),(4,0,5,0),(5,0,5,0)])
    add_recipe("water", 1, "1. literally just water", 
                   [(6,0,10,0)])


def populate_with_data():

    module = spoonacular_module()
    parse_spoonacular_response(module.get_random_recipes("breakfast"))
    parse_spoonacular_response(module.get_random_recipes("lunch"))
    parse_spoonacular_response(module.get_random_recipes("dinner"))

# add_recipe(recipeForm.name, recipeForm.time, recipeForm.steps, session.get('ingredients'))
# Note: Ingredients are a list of tuples consisting of: (ingredientID, ingredientName, ingredientQuantity, ingredientMeasure)
def add_recipe(name, time, steps, ingredients, rating=4.5, description=""):
    recipe = Recipe(name=name, time=time, steps=steps, rating=rating, description=description)
    if ingredients is not None:
        for idx, ingred_tuple in enumerate(ingredients):
            #ingredient = Ingredient.query.filter_by(name=ingred_name).first()
            ingredient = db.session.query(Ingredient).get(ingred_tuple[0]) # if add_recipe is using ids
            assoc = RI_Association(ingredient=ingredient, amount=ingred_tuple[2])
            #assoc.ingredient = ingredient
            recipe.ingredients.append(assoc)

    db.session.add(recipe)
    db.session.commit()
    return recipe.id

def search_recipe_by_ingredient(recipe_name="", ingred_ids=[]):
    # returns a list of recipe ids that include the name as a substring and include the ingredients

    # do a left join using recipes filtered by name, with the ingredient association list
    potential_recipes = db.session.query(Recipe).outerjoin(RI_Association).filter(Recipe.name.like("%{}%".format(recipe_name)))\
        .filter(RI_Association.i_id.in_(ingred_ids)).order_by(Recipe.name).with_entities(Recipe.id)
    pot_rec_set = {r.id for r in potential_recipes}
    
    bad_recipes = db.session.query(Recipe).outerjoin(RI_Association).filter(Recipe.name.like("%{}%".format(recipe_name)))\
        .filter(RI_Association.i_id.notin_(ingred_ids)).order_by(Recipe.name).with_entities(Recipe.id)
    bad_rec_set = {r.id for r in bad_recipes}

    # filter out recipes that have ingredients not in the provided list
    pot_good_recipes = pot_rec_set - bad_rec_set

    return list(pot_good_recipes)

def search_recipe_by_ingredient_amounts(recipe_name="", ingred_ids=[], amounts=[]):
    # Acquire list of recipes with correct ingredients, and then check their amounts with expected amounts
    pot_recipes = search_recipe_by_ingredient(recipe_name, ingred_ids)

    recipe_ids = []
    for r_id in pot_recipes:
        correct_amounts = True
        recipe = get_recipe(r_id)
        for i_idx, ingredient in enumerate(recipe.ingredients):
            try:
                i_idx2 = ingred_ids.index(ingredient.id)
                if (recipe.amounts[i_idx] > amounts[i_idx2]):
                    # if ingredient amount in recipe greater than amount provided, recipe is bad
                    correct_amounts = False
                    break
            except ValueError:
                # if ingredient not in provided list, recipe is bad
                # theoretically this shouldn't occur
                # print("Shouldn't occur")
                # print(recipe.ingredients)
                # print(ingred_ids)
                correct_amounts = False
                break
        if correct_amounts:
            recipe_ids.append(r_id)
    return recipe_ids



# Get all saved recipes for a given user
def get_user_saved_recipes(userID):
    return db.session.query(Recipe).join(RU_Association).filter_by(u_id=userID, saved=True)

# Get all recipes user has reviewed
def get_user_reviewed_recipes(userID):
    return db.session.query(RU_Association).filter_by(u_id=userID).filter(RU_Association.rating.isnot(None))

# Returns recipe's average rating
def get_aggragate_recipe_rating(recipeID):
    rating = 0
    num = 0
    for recipe in db.session.query(RU_Association).filter_by(r_id=recipeID).filter(RU_Association.rating.isnot(None)):
        rating = rating + recipe.rating
        num = num + 1
    if num != 0:
        return rating / num
    else:
        return 0

def get_aggregate_user_rating(userID):
    rating = 0
    num = 0
    for user in db.session.query(RU_Association).filter_by(u_id=userID).filter(RU_Association.rating.isnot(None)):
        rating = rating + user.rating
        num = num + 1
    if num != 0:
        return rating / num
    else:
        return 0

# Get all reviews for a given recipe
def get_recipe_reviews(recipeID):
    return db.session.query(RU_Association).filter_by(r_id=recipeID).filter(RU_Association.rating.isnot(None))

# If association exists, toggle saved, otherwise create association and set saved to true
def save_recipe(userID, recipeID):
    user_recipe = db.session.query(RU_Association).filter_by(u_id=userID, r_id=recipeID).first()
    if user_recipe is not None:
        if user_recipe.saved == True:
            user_recipe.saved = False
        else:
            user_recipe.saved = True
    else:
        user_recipe = RU_Association(r_id=recipeID, u_id=userID, saved=True)
        current_user = db.session.query(User).filter_by(id=userID).first()
        current_recipe = db.session.query(Recipe).filter_by(id=recipeID).first()
        current_user.recipes.append(user_recipe)
        current_recipe.users.append(user_recipe)
        db.session.add(user_recipe)
    db.session.commit()

def is_saved_recipe(userID, recipeID):
    user_recipe = db.session.query(RU_Association).filter_by(u_id=userID, r_id=recipeID).first()
    if user_recipe is not None:
        return user_recipe.saved
    else:
        return False


# If association exists, add rating and review, otherwise create association and set rating and review
def add_review(userID, recipeID, rating, review):
    user_recipe = db.session.query(RU_Association).filter_by(u_id=userID, r_id=recipeID).first()
    if user_recipe is not None:
        user_recipe.rating = rating
        user_recipe.review = review
    else:
        user_recipe = RU_Association(r_id=recipeID, u_id=userID, saved=False, rating=rating, review=review)
        current_user = db.session.query(User).filter_by(id=userID).first()
        current_recipe = db.session.query(Recipe).filter_by(id=recipeID).first()
        current_user.recipes.append(user_recipe)
        current_recipe.users.append(user_recipe)
        db.session.add(user_recipe)
    db.session.commit()

def parse_spoonacular_response(response):

    for recipe in response:
        toAdd = {}
        ingredients = []
        if 'title' in recipe:
            toAdd['name'] = recipe['title']

        if 'readyInMinutes' in recipe:
            toAdd['time'] = recipe['readyInMinutes']
        else:
            toAdd['time'] = recipe['preparationMinutes'] + recipe['cookingMinutes']
        toAdd['rating'] = recipe['spoonacularScore'] % 6 if 'spoonacularScore' in recipe else 4.5
        for ingredient in recipe['extendedIngredients']:
            ret = ingredient_unit_parser(ingredient)
            if len(ret) > 0:
                ingredients.append(ret)
        instructions = ""
        print(recipe)
        if 'instructions' in recipe:
            instructions = recipe['instructions']
            recipeSteps = instructions.replace(".", "\n")
        elif 'analyzedInstructions' in recipe:
            for ins in recipe['analyzedInstructions']:
                instructions += ins['step'] + '\n'
        toAdd['steps'] = instructions
        toAdd['description'] = recipe['summary'] if 'summary' in recipe else ''
        
        add_recipe(toAdd['name'], toAdd['time'], toAdd['steps'], ingredients, toAdd['rating'], toAdd['description'])
    
def ingredient_unit_parser(ingredient):
    id = -1
    if 'measures' in ingredient:
        if 'metric' in ingredient['measures']:
            if 'unitShort' in ingredient['measures']['metric']:
                if get_ingredient_by_name(ingredient['name']) is None:
                    id = add_ingredient(ingredient['name'], ingredient['measures']['metric']['unitShort'])
                else:
                    return ()
                # else:
                #     id = get_ingredient_by_name(ingredient['name']).id
                ingredientTuple = (id, ingredient['name'], ingredient['measures']['metric']['amount'], ingredient['measures']['metric']['unitShort'])
                return ingredientTuple
    return ()