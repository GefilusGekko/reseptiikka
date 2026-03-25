"""The main application file that defines the Flask app instance"""

from flask import Flask, request, jsonify, render_template

from extensions import db
from models import Recipe, Ingredient, Instruction, Tag


app = Flask(__name__)

# Configure DB URI (Default to SQLite for local dev)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the shared db instance with the app
db.init_app(app)

# Create tables only once
with app.app_context():
    # db.drop_all()  # WARNING: This deletes all existing data!
    db.create_all()


@app.route('/')
def index():
    """Route for serving the web page"""
    return render_template('index.html')


@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    """Show single recipe details"""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return render_template('404.html'), 404
    return render_template('recipe_detail.html', recipe=recipe)


@app.route('/recipes', methods=['POST'])
def create_recipe():
    try:
        data = request.get_json()

        if not data or 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400

        recipe = Recipe(
            name=data['name'],
            category=data.get('category', '')  # Optional field
        )

        # Handle ingredients
        if 'ingredients' in data and isinstance(data['ingredients'], list):
            for ing_data in data['ingredients']:
                if all(k in ing_data for k in ['name', 'unit']):
                    quantity = ing_data.get('quantity')
                    ingredient = Ingredient(
                        name=ing_data['name'],
                        quantity=quantity,
                        unit=ing_data['unit'],
                        recipe=recipe
                    )
                    db.session.add(ingredient)

        # Handle instructions
        if 'instructions' in data and isinstance(data['instructions'], list):
            for idx, desc in enumerate(data['instructions'], 1):
                if desc.strip():  # Skip empty instructions
                    instruction = Instruction(
                        step_number=idx,
                        description=desc,
                        recipe=recipe
                    )
                    db.session.add(instruction)

        if 'tags' in data and isinstance(data['tags'], list):
            recipe.tags = []  # Clear existing
            for tag_name in data['tags']:
                if not tag_name.strip(): continue
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                recipe.tags.append(tag)

        db.session.add(recipe)
        db.session.commit()

        return jsonify({'id': recipe.id, 'message': 'Recipe created successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/recipes', methods=['GET'])
def get_recipes():
    """Get all recipes or a category of recipes"""
    try:
        category_filter = request.args.get('category')
        if category_filter:
            recipes = Recipe.query.filter_by(category=category_filter).all()
        else:
            recipes = Recipe.query.all()

        result = []
        for r in recipes:
            result.append({
                'id': r.id,
                'name': r.name,
                'category': r.category,
                'tags': [t.name for t in r.tags],
                'instructions': [i.description for i in r.instructions],
                'ingredients': [
                    {'name': i.name, 'quantity': i.quantity, 'unit': i.unit}
                    for i in r.ingredients
                ]
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_single_recipe(recipe_id):
    """Get a single recipe by its ID"""
    recipe = Recipe.query.get_or_404(recipe_id)

    return jsonify({
        'id': recipe.id,
        'name': recipe.name,
        'category': recipe.category,
        'tags': [t.name for t in recipe.tags],
        'instructions': [
            {'step_number': i.step_number, 'description': i.description}
            for i in recipe.instructions
        ],
        'ingredients': [
            {'name': i.name, 'quantity': i.quantity, 'unit': i.unit}
            for i in recipe.ingredients
        ]
    })


@app.route('/recipes/<int:recipe_id>', methods=['PUT'])
def update_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    try:
        data = request.get_json()

        if 'name' in data:
            recipe.name = data['name']

        if 'category' in data:
            recipe.category = data['category']

        if 'tags' in data:
            recipe.tags = []  # Clear existing
            if isinstance(data['tags'], list):
                for tag_name in data['tags']:
                    if not tag_name.strip(): continue
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    recipe.tags.append(tag)

        # Replace all instructions
        if 'instructions' in data:
            Instruction.query.filter_by(recipe_id=recipe_id).delete()
            if isinstance(data['instructions'], list):
                for idx, desc in enumerate(data['instructions'], 1):
                    if desc.strip():
                        instruction = Instruction(
                            step_number=idx,
                            description=desc,
                            recipe=recipe
                        )
                        db.session.add(instruction)

        # Replace all ingredients
        if 'ingredients' in data:
            Ingredient.query.filter_by(recipe_id=recipe_id).delete()
            if isinstance(data['ingredients'], list):
                for ing_data in data['ingredients']:
                    if all(k in ing_data for k in ['name', 'unit']):
                        quantity = ing_data.get('quantity')
                        ingredient = Ingredient(
                            name=ing_data['name'],
                            quantity=quantity,
                            unit=ing_data['unit'],
                            recipe=recipe
                        )
                        db.session.add(ingredient)

        db.session.commit()
        return jsonify({'message': 'Recipe updated successfully', 'id': recipe.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    recipe = Recipe.query.get_or_404(recipe_id)

    try:
        db.session.delete(recipe)
        db.session.commit()
        return jsonify({'message': 'Recipe deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/recipes/search', methods=['GET'])
def search_recipes():
    """Search recipes by ingredient(s)"""
    try:
        # Get search parameters
        ingredients_param = request.args.get('ingredients', '')
        match_type = request.args.get('match', 'any')  # 'any' (OR) or 'all' (AND)
        
        if not ingredients_param:
            return jsonify([])
        
        # Parse ingredients (comma-separated)
        search_ingredients = [ing.strip().lower() for ing in ingredients_param.split(',') if ing.strip()]
        
        if not search_ingredients:
            return jsonify([])
        
        # Query logic
        if match_type == 'all':
            # AND logic: Recipe must have ALL ingredients
            # This requires a more complex query - count matching ingredients per recipe
            from sqlalchemy import func
            
            # Get recipes that have all search ingredients
            matching_recipes = []
            for recipe in Recipe.query.all():
                recipe_ingredients = [ing.name.lower() for ing in recipe.ingredients]
                if all(search_ing in recipe_ingredients for search_ing in search_ingredients):
                    matching_recipes.append(recipe)
        else:
            # OR logic: Recipe must have ANY ingredient
            matching_recipes = []
            for recipe in Recipe.query.all():
                recipe_ingredients = [ing.name.lower() for ing in recipe.ingredients]
                if any(search_ing in recipe_ingredients for search_ing in search_ingredients):
                    matching_recipes.append(recipe)
        
        # Serialize results (same format as get_recipes)
        result = []
        for r in matching_recipes:
            result.append({
                'id': r.id,
                'name': r.name,
                'category': r.category,
                'tags': [t.name for t in r.tags],
                'instructions': [i.description for i in r.instructions],
                'ingredients': [
                    {'name': i.name, 'quantity': i.quantity, 'unit': i.unit}
                    for i in r.ingredients
                ]
            })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # In production, use gunicorn/uwsgi, not debug=True
    app.run(debug=True, host='0.0.0.0')
