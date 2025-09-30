from src import db

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    posts = db.relationship('Post', backref='topic', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    caption = db.Column(db.Text, nullable=True)
    image_prompt = db.Column(db.Text, nullable=True)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    is_published = db.Column(db.Boolean, default=False)
