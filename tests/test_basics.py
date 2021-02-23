import unittest
from flask import current_app
from app import create_app, db
from app.models import *
from app.main.views import metric_to_spoons_volume, spoons_to_metric_volume, metric_to_imp_mass, imp_to_metric_mass, get_user_volume_preference_string, get_user_mass_preference_string

class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])

    def test_get_ingredient(self):
        populate_with_dummy_data()
        ing = get_ingredient(1)
        ingredient_name = get_ingredient_name(1)
        ingredient_measure = get_ingredient_measure(1)
        self.assertEqual(ing.name, ingredient_name)
        self.assertEqual(ing.measure, ingredient_measure)

    def test_get_recipe(self):
        populate_with_dummy_data()
        rec = get_recipe(1)
        self.assertFalse(rec is None)
        allRec = get_all_recipes()
        self.assertEqual(rec.name, allRec[1].name)

    def test_search_recipe(self):
        populate_with_dummy_data()
        recipes = search_recipe_by_ingredient(recipe_name="alad", ingred_ids=[1,2,3,4,5,6])
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0], 2)
        recipes = search_recipe_by_ingredient(recipe_name="alad", ingred_ids=[1,2,3,4,6])
        self.assertEqual(len(recipes), 0)
    
    def test_search_noname(self):
        populate_with_dummy_data()
        recipes = search_recipe_by_ingredient(recipe_name="", ingred_ids=[1,2,3,4,5,6])
        self.assertEqual(len(recipes), 2)

    def test_search_recipe_amounts(self):
        populate_with_dummy_data()
        recipes = search_recipe_by_ingredient_amounts(recipe_name="alad", 
                    ingred_ids=[1,2,3,4,5,6], amounts=[5,5,5,5,5,5])
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0], 2)
        recipes = search_recipe_by_ingredient_amounts(recipe_name="alad", 
                    ingred_ids=[1,3,4,2,5,6], amounts=[5,5,5,5,5,5])
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0], 2)
        recipes = search_recipe_by_ingredient_amounts(recipe_name="alad", 
                    ingred_ids=[1,2,3,4,5,6], amounts=[5,5,5,4,5,5])
        self.assertEqual(len(recipes), 0)

    def test_user_rating(self):
        populate_with_dummy_data()
        newUser = User(username='Test')
        db.session.add(newUser)
        db.session.commit()
        review = 'Hello world'
        rating = 4
        add_review(newUser.id, 1, rating, review)
        recipeReview = get_user_reviewed_recipes(newUser.id).first()
        self.assertEqual(recipeReview.review, review)
        self.assertEqual(recipeReview.rating, rating)
        self.assertEqual(recipeReview.saved, False)
        reviewedRecipe = get_recipe_reviews(1).first()
        self.assertEqual(reviewedRecipe.review, review)
        self.assertEqual(reviewedRecipe.rating, rating)
        self.assertEqual(reviewedRecipe.saved, False)

    def test_user_saved(self):
        populate_with_dummy_data()
        newUser = User(username='Test')
        db.session.add(newUser)
        db.session.commit()
        save_recipe(newUser.id, 1)
        savedRecipe = get_user_saved_recipes(newUser.id).first()
        self.assertEqual(savedRecipe.id, 1)
        save_recipe(newUser.id, 1)
        savedRecipe = get_user_saved_recipes(newUser.id).first()
        self.assertTrue(savedRecipe is None)

    def test_rating_aggregates(self):
        populate_with_dummy_data()
        newUser1 = User(username='Test1')
        db.session.add(newUser1)
        newUser2 = User(username='Test2')
        db.session.add(newUser2)
        db.session.commit()
        add_review(newUser1.id, 1, 3, 'Review1')
        add_review(newUser1.id, 2, 5, 'Review2')
        add_review(newUser2.id, 2, 3, 'Review1')
        add_review(newUser2.id, 1, 5, 'Review2')

        self.assertEqual(get_aggregate_user_rating(newUser1.id), 4)
        self.assertEqual(get_aggregate_user_rating(newUser2.id), 4)

        self.assertEqual(get_aggragate_recipe_rating(1), 4)
        self.assertEqual(get_aggragate_recipe_rating(2), 4)

    def test_recipes(self):
        # goal is to test adding and retrieving a recipe in detail
        # after the get recipe function is tested above
        populate_with_dummy_data()

        name = "extra salty water"
        time = 420
        step1 = "1. add water"
        step2 = "2. add lots and lots of salt"
        steps = step1+"\n"+step2
        ingredients = [(6,0,10,0),(7,0,1,0)]
        rating = 5
        description = ""

        # Compare result with what was sent to ensure data is properly stored and retrieved
        r_id = add_recipe(name, time, steps, ingredients, rating, description)
        r = get_recipe(r_id)
        self.assertEqual(r.name, name)
        self.assertEqual(r.time, time)
        self.assertEqual(r.steps[0], step1)
        self.assertEqual(r.steps[1], step2)
        self.assertEqual(r.name, name)
        self.assertEqual(r.rating, rating)
        self.assertEqual(r.description, description)

    def test_get_all_ingredients(self):
        populate_with_dummy_data()
        ingredients = get_all_ingredients()
        self.assertEqual(ingredients[0].name, "carrots")
        self.assertEqual(ingredients[1].name, "cucumber")
        self.assertEqual(ingredients[2].name, "lettuce")
        self.assertEqual(len(ingredients), 7)

        
    def test_search_recipe(self):
        populate_with_dummy_data()
        ingredients_query = search_ingredients("arro")
        ingredients = [(g.id, g.name) for g in ingredients_query]
        self.assertEqual(len(ingredients),1)
        self.assertEqual(ingredients[0][1], "carrots")

    def test_unit_conversions(self):
        mass = 250
        lbs, oz = metric_to_imp_mass(mass)
        testMass = imp_to_metric_mass(lbs, oz)
        self.assertAlmostEqual(mass, testMass, places=3)
        self.assertAlmostEqual(oz, 8.81849, places=3)
        volume = 276
        cups, quarterCups, tbsps, tsps = metric_to_spoons_volume(volume)
        test_volume = spoons_to_metric_volume(cups, quarterCups, tbsps, tsps)
        self.assertEqual(cups, 1)
        self.assertEqual(quarterCups, 0)
        self.assertEqual(tbsps, 1)
        self.assertEqual(tsps, 2)
        self.assertAlmostEqual(volume, test_volume, delta=5)

    def test_unit_conversion_strings(self):
        volume = 333
        mass = 600
        newUser1 = User(username='Test1', prefers_metric_volume=True, prefers_metric_mass=True)
        db.session.add(newUser1)
        newUser2 = User(username='Test2', prefers_metric_volume=False, prefers_metric_mass=False)
        db.session.add(newUser2)
        db.session.commit()
        testString1 = "333.00 ml | "
        testString2 = "600.00 g | "
        testString3 = "1 cup | 1 quarter cup | 1 tablespoon | 1 teaspoon | "
        testString4 = "1 lb | 5.16 ozs | "
        self.assertEqual(testString1, get_user_volume_preference_string(newUser1.id, volume))
        self.assertEqual(testString2, get_user_mass_preference_string(newUser1.id, mass))
        self.assertEqual(testString3, get_user_volume_preference_string(newUser2.id, volume))
        self.assertEqual(testString4, get_user_mass_preference_string(newUser2.id, mass))

