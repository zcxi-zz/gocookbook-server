from flask import render_template, session, redirect, url_for, request, jsonify
from .. import db
from ..models import User, get_all_ingredients, get_ingredient_name, get_ingredient_measure, add_recipe, get_recipe, add_ingredient, get_all_recipes, search_ingredients, save_recipe, is_saved_recipe, get_user_saved_recipes, get_user_volume_preference, get_user_mass_preference
from flask_login import current_user, login_required
from . import main
from .forms import RecipeForm, IngredientForm, IngredientAddForm, SaveRecipeToggleForm, UnsaveRecipeToggleForm
import math

@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html', name=session.get('name'), known=session.get('known', False))

def metric_to_spoons_volume(volume):
    numQuarterCups = math.floor(volume / 62.5)
    cupRemainder = volume - 62.5 * numQuarterCups
    numCups = numQuarterCups // 4
    numQuarterCups = numQuarterCups - 4 * numCups
    numTeaSpoon = cupRemainder / (4.92892)
    numTbSpoon = math.floor(numTeaSpoon / 3)
    numTeaSpoon = numTeaSpoon - 3 * numTbSpoon
    numTeaSpoon = math.floor(numTeaSpoon)
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
    if get_user_volume_preference(userID):
        returnString = "{:0.2f} ml | "
        returnString = returnString.format(volume)
        return returnString
    else:
        cups, quarterCups, tbsps, tsps = metric_to_spoons_volume(volume)
        returnString = ""
        if cups > 0:
            if cups > 1:
                returnString = returnString + "{} cups | "
            else:
                returnString = returnString + "{} cup | "
            returnString = returnString.format(cups)
        if quarterCups > 0:
            if quarterCups % 2 != 0:
                if quarterCups > 1:
                    returnString = returnString + "{} quarter cups | "
                else:
                    returnString = returnString + "{} quarter cup | "
                returnString = returnString.format(quarterCups)
            else:
                returnString = returnString + "1 half cup | "
        if tbsps > 0:
            if tbsps > 1:
                returnString = returnString + "{} tablespoons | "
            else:
                returnString = returnString + "{} tablespoon | "
            returnString = returnString.format(tbsps)
        if tsps > 0:
            if tsps > 1:
                returnString = returnString + "{} teaspoons | "
            else:
                returnString = returnString + "{} teaspoon | "
            returnString = returnString.format(tsps)
        return returnString

def get_user_mass_preference_string(userID, mass):
    if get_user_mass_preference(userID):
        returnString = "{:0.2f} g | "
        returnString = returnString.format(mass)
        return returnString
    else:
        pounds, oz = metric_to_imp_mass(mass)
        returnString = ""
        if pounds > 0:
            if pounds > 1:
                returnString = returnString + "{} lbs | "
            else:
                returnString = returnString + "{} lb | "
            returnString = returnString.format(pounds)
        if oz > 0:
            if oz != 1:
                returnString = returnString + "{:0.2f} ozs | "
            else:
                returnString = returnString + "{:0.2f} oz | "
            returnString = returnString.format(oz)
        return returnString

@main.route('/add_new_recipe', methods=['GET', 'POST'])
@login_required
def add_new_recipe():
    ingredientForm = IngredientForm()
    recipeForm = RecipeForm()
    ingredientForm.ingredientID.choices = [(g.id, g.name) for g in get_all_ingredients()]

    # Adds new ingredient to ingredient list
    if ingredientForm.validate_on_submit():
        ingredient_list = session.get('ingredients')
        if ingredient_list is None:
            ingredient_list = []
        ingredientID = ingredientForm.ingredientID.data
        ingredientName = get_ingredient_name(ingredientID)
        ingredientQuantity = ingredientForm.quantity.data
        ingredientMeasure = get_ingredient_measure(ingredientID)
        ingredient_list.append((ingredientID, ingredientName, ingredientQuantity, ingredientMeasure))
        session['ingredients'] = ingredient_list
        session['name'] = recipeForm.name
        session['description'] = recipeForm.description
        session['steps'] = recipeForm.steps
        session['time'] = recipeForm.time
        return redirect(url_for('main.add_new_recipe'))

    # Clears page if recipe has already been submitted
    if recipeForm.is_submitted():
        session['ingredients'] = None
        session['name'] = None
        session['description'] = None
        session['steps'] = None
        session['time'] = None

    else: # Retrieves data to populate the forms from session memory
        recipeForm.name = session.get('name')
        recipeForm.description = session.get('description')
        recipeForm.steps = session.get('steps')
        recipeForm.time = session.get('time')

    if recipeForm.validate_on_submit(): # Submits recipe to database
        ingredient_list = session.get('ingredients')
        add_recipe(recipeForm.name.data, recipeForm.time.data, recipeForm.steps.data, session.get('ingredients'))
        return redirect(url_for('main.add_new_recipe'))
    return render_template('add_new_recipe.html', rForm = recipeForm, iForm = ingredientForm, ingredients = session.get('ingredients'))

@main.route('/add_new_ingredient', methods=['GET', 'POST'])
@login_required
def add_new_ingredient():
    ingredientAddForm = IngredientAddForm()
    if ingredientAddForm.validate_on_submit():
        add_ingredient(ingredientAddForm.name.data, ingredientAddForm.measure.data)
        return redirect(url_for('main.add_new_ingredient'))
    return render_template('add_new_ingredient.html', inForm = ingredientAddForm)

@main.route('/view_recipe/<recipe_ID>', methods=['GET', 'POST'])
def view_recipe(recipe_ID):
    saveForm = SaveRecipeToggleForm()
    unsaveForm = UnsaveRecipeToggleForm()
    if saveForm.validate_on_submit():
        save_recipe(current_user.id, recipe_ID)
        return redirect(url_for('main.view_recipe', recipe_ID=recipe_ID))
    if unsaveForm.validate_on_submit():
        save_recipe(current_user.id, recipe_ID)
        return redirect(url_for('main.view_recipe', recipe_ID=recipe_ID))
    recipe = get_recipe(recipe_ID)
    if current_user.is_authenticated:
        if is_saved_recipe(current_user.id, recipe_ID):
            return render_template('view_recipe.html', recipe = recipe, saveToggle = unsaveForm)
        else:
            return render_template('view_recipe.html', recipe = recipe, saveToggle = saveForm)
    else:
        del saveForm.saveRecipe
        return render_template('view_recipe.html', recipe = recipe, saveToggle = saveForm)

@main.route('/view_recipes', methods=['GET', 'POST'])
def view_recipes():
    recipes_to_view = get_all_recipes()
    return render_template('view_recipes.html', recipes = recipes_to_view)


@main.route('/view_saved_recipes', methods=['GET', 'POST'])
@login_required
def view_saved_recipes():
    recipes_to_view = get_user_saved_recipes(current_user.id)
    return render_template('view_recipes.html', recipes = recipes_to_view)

@main.route('/select_ingredients', methods=['GET', 'POST'])
def select_ingredients():
    ingredients = get_all_ingredients()
    return render_template('ingredient_combobox.html', ingredients_list = ingredients)

@main.route('/autocomplete', methods=['GET'])
def autocomplete():
    # search_phrase is the phrase that is currently written in the combobox
    search_phrase = request.args.get('term')
    # use database search function to return ingredients that have the phrase as a substring
    ingredients = search_ingredients(search_phrase)
    results = [{"value": i.name, "id": i.id} for i in ingredients]

    return jsonify(matching_results=results)

