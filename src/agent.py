import os
from pydantic import BaseModel, Field
from pydantic_ai import Instructor
from google.generativeai import GenerativeModel
import google.generativeai as genai
from typing import List, Optional

class SocialMediaPost(BaseModel):
    """Represents a social media post with a caption and an image prompt."""
    caption: str = Field(..., description="A catchy and engaging caption for the social media post.")
    image_prompt: str = Field(..., description="A detailed prompt for an image generation model to create a visually appealing and relevant image.")

class PastPost(BaseModel):
    """Represents a past social media post for learning purposes."""
    caption: str
    likes: int
    comments: int
    shares: int

def generate_post(topic: str, past_posts: Optional[List[PastPost]] = None) -> SocialMediaPost:
    """Generates a social media post for a given topic using an LLM, learning from past posts."""
    # 0. Configure the API key
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    # 1. Construct the prompt with examples of past posts
    prompt = f"""Generate a social media post about '{topic}'. The post should be engaging and designed to capture audience attention.
    Your goal is to maximize likes and comments.
    """

    if past_posts:
        prompt += "\n\nHere are some examples of past posts on this topic and their engagement. Learn from them to create even better content:\n"
        for post in past_posts:
            prompt += f"- Caption: {post.caption}\n"
            prompt += f"  - Likes: {post.likes}, Comments: {post.comments}, Shares: {post.shares}\n"

    # 2. Generate the structured output
    client = GenerativeModel(model_name="gemini-pro")
    instructor = Instructor(client=client)
    
    post = instructor.generate(
        model="gemini-pro",
        prompt=prompt,
        response_model=SocialMediaPost
    )
    
    return post
