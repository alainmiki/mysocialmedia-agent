import os
import random
from src import celery, db
from src.social_media import post_to_facebook, post_to_instagram
from src.agent import generate_post
from src.posts.models import Post, Topic

@celery.task
def generate_and_post_task(post_id):
    """A Celery task to generate content and post it."""
    post = Post.query.get(post_id)
    if not post:
        print(f"Post with ID {post_id} not found.")
        return

    topic = Topic.query.get(post.topic_id)
    if not topic:
        print(f"Topic for post ID {post_id} not found.")
        return

    print(f"Generating content for topic: {topic.name}")
    try:
        # In Milestone 5, the agent will learn from past posts
        generated_content = generate_post(topic.name)

        # Update the post with the generated content
        post.caption = generated_content.caption
        post.image_prompt = generated_content.image_prompt
        post.is_published = True
        db.session.commit()

        # Post to social media
        image_url = "https://via.placeholder.com/1080" # Placeholder
        post_to_facebook(post.caption, image_url)
        post_to_instagram(post.caption, image_url)

        print(f"Post {post_id} has been published.")

    except Exception as e:
        print(f"Error processing post {post_id}: {e}")
        post.is_published = False
        db.session.commit()

@celery.task
def fetch_engagement_task(post_id):
    """A Celery task to simulate fetching engagement data for a post."""
    post = Post.query.get(post_id)
    if not post or not post.is_published:
        print(f"Skipping engagement fetch for post {post_id}.")
        return

    print(f"Fetching engagement for post {post_id}...")
    
    # --- Placeholder for Real API Call ---
    # Simulate fetching data from social media APIs
    post.likes = random.randint(10, 500)
    post.comments = random.randint(5, 100)
    post.shares = random.randint(1, 50)
    db.session.commit()

    print(f"Updated engagement for post {post_id}")
