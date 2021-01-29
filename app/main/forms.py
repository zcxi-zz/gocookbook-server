from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SubmitField, SelectField, FloatField, TextAreaField, IntegerField
from wtforms.validators import Required


class RecipeForm(FlaskForm):
    name = StringField('Recipe Name', validators=[Required()])
    description = StringField('Description', validators=[Required()])
    time = IntegerField('Completion Time (in minutes)', validators=[Required()])
    steps = TextAreaField('Recipe Steps', validators=[Required()])
    submit = SubmitField('Submit')
    
class IngredientForm(FlaskForm):
    ingredientID = SelectField(u'Ingredient', coerce=int)
    quantity = FloatField('Quantity')
    add = SubmitField('Add Ingredient')

class IngredientAddForm(FlaskForm):
    name = StringField('Ingredient Name', validators=[Required()])
    measure = SelectField('How to Measure', choices=['volume', 'mass', 'units'])
    add = SubmitField('Add Ingredient')

class SaveRecipeToggleForm(FlaskForm):
    saveRecipe = SubmitField('Save Recipe')

class UnsaveRecipeToggleForm(FlaskForm):
    unsaveRecipe = SubmitField('Unsave Recipe')