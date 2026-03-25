"""Model file for defining the recipe data strucure."""

from extensions import db

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

recipe_tags = db.Table('recipe_tags',
    db.Column('recipe_id', db.Integer, db.ForeignKey('recipe.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)

class Recipe(db.Model):
    """
    Represents a recipe in the database.

    Attributes:
        id (int): Unique identifier for the recipe.
        name (str): Name of the recipe.
        ingredients (list): List of Ingredient instances associated with this recipe.
        instructions (str): Instructions for preparing the recipe.
    """
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    tags = db.relationship('Tag', secondary=recipe_tags, lazy='subquery',
                          backref=db.backref('recipe', lazy=True))
    category = db.Column(db.String(50), nullable=True)
    ingredients = db.relationship('Ingredient', backref='recipe', lazy=True,
                                cascade="all, delete-orphan")
    instructions = db.relationship('Instruction', backref='recipe', lazy=True,
                                cascade="all, delete-orphan", order_by='Instruction.step_number')

    def __repr__(self):
        return f"Recipe('{self.name}')"

class Ingredient(db.Model):
    """
    Represents a single ingredient in the database.

    Attributes:
        id (int): Unique identifier for the ingredient.
        name (str): Name of the ingredient.
        quantity (float): Quantity of the ingredient needed for the recipe.
        unit (str): Unit of measurement for the ingredient quantity.
        recipe_id (int): Foreign key referencing the Recipe instance this ingredient is 
        associated with.
    """
    __tablename__ = 'ingredient'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(10), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

    def __repr__(self):
        return f"Ingredient('{self.name}', '{self.quantity} {self.unit}')"


class Instruction(db.Model):
    """Represents a single instruction step in a recipe."""
    __tablename__ = 'instructions'
    id = db.Column(db.Integer, primary_key=True)
    step_number = db.Column(db.Integer, nullable=False)  # Order of the step
    description = db.Column(db.Text, nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

    def __repr__(self):
        return f"Instruction(step {self.step_number})"
