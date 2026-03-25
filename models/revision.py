"""Model file for defining the revision history data strucure."""

from datetime import datetime
from extensions import db

class RecipeRevision(db.Model):
    """Header table for each revision of a recipe."""
    __tablename__ = 'recipe_revisions'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    version = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)  # Optional: user comment about this revision
    
    recipe = db.relationship('Recipe', backref=db.backref('revisions', lazy=True))
    
    # Relationships to revision-specific data
    revision_ingredients = db.relationship('RevisionIngredient', 
                                           backref='revision', 
                                           lazy=True,
                                           cascade="all, delete-orphan")
    revision_instructions = db.relationship('RevisionInstruction', 
                                            backref='revision', 
                                            lazy=True,
                                            cascade="all, delete-orphan")
    revision_tags = db.relationship('RevisionTag', 
                                    backref='revision', 
                                    lazy=True,
                                    cascade="all, delete-orphan")

    def __repr__(self):
        return f"RecipeRevision(recipe_id={self.recipe_id}, version={self.version})"


class RevisionIngredient(db.Model):
    """Ingredient snapshot tied to a specific revision."""
    __tablename__ = 'revision_ingredients'
    id = db.Column(db.Integer, primary_key=True)
    revision_id = db.Column(db.Integer, db.ForeignKey('recipe_revisions.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f"RevisionIngredient(revision_id={self.revision_id}, name='{self.name}')"


class RevisionInstruction(db.Model):
    """Instruction snapshot tied to a specific revision."""
    __tablename__ = 'revision_instructions'
    id = db.Column(db.Integer, primary_key=True)
    revision_id = db.Column(db.Integer, db.ForeignKey('recipe_revisions.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"RevisionInstruction(revision_id={self.revision_id}, step={self.step_number})"


class RevisionTag(db.Model):
    """Tag association tied to a specific revision (many-to-many junction)."""
    __tablename__ = 'revision_tags'
    revision_id = db.Column(db.Integer, db.ForeignKey('recipe_revisions.id'), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), primary_key=True)
    
    tag = db.relationship('Tag', backref=db.backref('revision_associations', lazy=True))