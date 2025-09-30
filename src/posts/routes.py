from flask import Blueprint, request, jsonify
from datetime import datetime
from src import db
from src.posts.models import Post, Topic
from src.agent import generate_post, PastPost
from src.social_media import post_to_facebook, post_to_instagram
from src.tasks import generate_and_post_task, fetch_engagement_task

posts_bp = Blueprint('posts', __name__)

@posts_bp.route('/generate', methods=['POST'])
def generate_content():
    data = request.get_json()
    if not data or 'topic' not in data:
        return jsonify({'error': 'Missing "topic" in request body'}), 400

    topic_name = data['topic']
    
    try:
        topic = Topic.query.filter_by(name=topic_name).first()
        if not topic:
            topic = Topic(name=topic_name)
            db.session.add(topic)
            db.session.commit()

        # --- Milestone 5: Learning --- #
        # Fetch past successful posts to use as context
        past_posts_data = Post.query.filter_by(topic_id=topic.id, is_published=True).order_by(Post.likes.desc()).limit(5).all()
        past_posts_for_agent = [
            PastPost(caption=p.caption, likes=p.likes, comments=p.comments, shares=p.shares) 
            for p in past_posts_data
        ]

        generated_post = generate_post(topic_name, past_posts=past_posts_for_agent)
        
        new_post = Post(
            topic_id=topic.id,
            caption=generated_post.caption,
            image_prompt=generated_post.image_prompt,
            scheduled_at=datetime.utcnow(),
            is_published=True
        )
        db.session.add(new_post)
        db.session.commit()

        placeholder_image_url = "https://via.placeholder.com/1080"
        post_to_facebook(generated_post.caption, placeholder_image_url)
        post_to_instagram(generated_post.caption, placeholder_image_url)

        # Trigger engagement fetch after a delay
        fetch_engagement_task.apply_async(args=[new_post.id], countdown=3600) # Fetch in 1 hour

        return jsonify({
            'status': 'Posted and saved to database',
            'post_id': new_post.id,
            'caption': new_post.caption,
            'image_prompt': new_post.image_prompt
        }), 201

    except Exception as e:
        return jsonify({'error': f'Error generating content: {e}'}), 500

@posts_bp.route('/schedule', methods=['POST'])
def schedule_content():
    data = request.get_json()
    if not data or 'topic' not in data or 'scheduled_at' not in data:
        return jsonify({'error': 'Missing "topic" or "scheduled_at" in request body'}), 400

    topic_name = data['topic']
    scheduled_at_str = data['scheduled_at']

    try:
        scheduled_at_dt = datetime.fromisoformat(scheduled_at_str)
        topic = Topic.query.filter_by(name=topic_name).first()
        if not topic:
            topic = Topic(name=topic_name)
            db.session.add(topic)
            db.session.commit()
        
        new_post = Post(topic_id=topic.id, scheduled_at=scheduled_at_dt)
        db.session.add(new_post)
        db.session.commit()

        generate_and_post_task.apply_async(args=[new_post.id], eta=scheduled_at_dt)

        return jsonify({
            'status': 'Post scheduled successfully',
            'post_id': new_post.id
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Error scheduling post: {e}'}), 500

@posts_bp.route('/posts/<topic_name>', methods=['GET'])
def get_posts_by_topic(topic_name):
    topic = Topic.query.filter_by(name=topic_name).first()
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404

    posts = Post.query.filter_by(topic_id=topic.id).order_by(Post.scheduled_at.desc()).all()
    
    return jsonify([{
        'id': post.id,
        'caption': post.caption,
        'is_published': post.is_published,
        'scheduled_at': post.scheduled_at,
        'likes': post.likes,
        'comments': post.comments,
        'shares': post.shares
    } for post in posts])

@posts_bp.route('/posts/<int:post_id>/fetch_engagement', methods=['POST'])
def trigger_fetch_engagement(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    if not post.is_published:
        return jsonify({'error': 'Cannot fetch engagement for an unpublished post'}), 400

    fetch_engagement_task.delay(post_id)

    return jsonify({
        'status': 'Engagement fetch task triggered',
        'post_id': post_id
    }), 202
