# Nested-nested-nested replies are now supported

import os
import googleapiclient.discovery
import argparse
import re
from urllib.parse import urlparse, parse_qs

def clean_text(text):
    """Clean text from HTML formatting and mentions"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Fix HTML entities
    text = text.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    
    # Remove all @ mentions including special characters
    text = re.sub(r'@[\w\-\+\.]+\s*', '', text)  # Standard mentions
    text = re.sub(r'@[^\s]+\s*', '', text)       # Catch any remaining @ patterns
    
    # Remove zero-width spaces and other invisible characters
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def get_nested_replies(youtube, parent_id, all_replies=None):
    """
    Recursively fetch all nested replies for a comment.
    
    Args:
        youtube: YouTube API client
        parent_id (str): ID of the parent comment
        all_replies (list): List to store all replies
    
    Returns:
        list: List of reply dictionaries
    """
    if all_replies is None:
        all_replies = []
        
    try:
        request = youtube.comments().list(
            part="snippet",
            parentId=parent_id,
            maxResults=100
        )
        response = request.execute()
        
        for item in response.get("items", []):
            reply_snippet = item["snippet"]
            reply_data = {
                "author": reply_snippet["authorDisplayName"],
                "text": clean_text(reply_snippet["textDisplay"]),  # Clean the text
                "likes": reply_snippet["likeCount"],
                "published": reply_snippet["publishedAt"],
                "replies": []
            }
            all_replies.append(reply_data)
            
            # Recursively get replies to this reply
            get_nested_replies(youtube, item["id"], reply_data["replies"])
            
    except Exception as e:
        print(f"Error fetching nested replies: {e}")
    
    return all_replies

def get_video_comments(video_id, api_key, max_results=100):
    """
    Fetch comments and ALL their nested replies for a YouTube video.
    """
    youtube = googleapiclient.discovery.build(
        "youtube", "v3", developerKey=api_key
    )
    
    comments = []
    next_page_token = None
    
    while len(comments) < max_results:
        try:
            # Get top-level comments
            request = youtube.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=min(100, max_results - len(comments)),
                pageToken=next_page_token
            )
            
            response = request.execute()
            
            # Process comment data
            for item in response.get("items", []):
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comment_data = {
                    "author": comment["authorDisplayName"],
                    "text": clean_text(comment["textDisplay"]),  # Clean the text
                    "likes": comment["likeCount"],
                    "published": comment["publishedAt"],
                    "replies": []
                }
                
                # Get all nested replies
                if item.get("replies"):
                    comment_id = item["snippet"]["topLevelComment"]["id"]
                    comment_data["replies"] = get_nested_replies(youtube, comment_id)
                
                comments.append(comment_data)
            
            next_page_token = response.get("nextPageToken")
            if not next_page_token or len(comments) >= max_results:
                break
                
        except Exception as e:
            print(f"Error fetching comments: {e}")
            break
    
    return comments

def write_replies_to_csv(writer, replies, parent_author, parent_text, depth=1):
    """Helper function to write nested replies recursively"""
    for reply in replies:
        reply_level = f"reply_level_{depth}"
        writer.writerow([
            reply_level,
            reply["author"],  
            reply["text"],
            reply["likes"],
            reply["published"],
            parent_author,
            parent_text
        ])
        if reply["replies"]:
            write_replies_to_csv(writer, reply["replies"], reply["author"], reply["text"], depth + 1)

def json_to_csv(json_file, csv_file):
    import json
    import csv

    with open(json_file, 'r', encoding='utf-8') as f:
        comments = json.load(f)

    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "comment_type", 
            "author", 
            "text", 
            "likes", 
            "published", 
            "parent_author",
            "parent_text"
        ])
        
        for comment in comments:
            # Write main comment
            writer.writerow([
                "main", 
                comment["author"], 
                comment["text"], 
                comment["likes"], 
                comment["published"], 
                "",  # No parent author for main comments
                ""   # No parent text for main comments
            ])
            
            # Write all nested replies
            write_replies_to_csv(writer, comment["replies"], comment["author"], comment["text"])

def extract_video_id(video_input):
    """
    Extract video ID from either a full YouTube URL or video ID string.
    
    Args:
        video_input (str): YouTube URL or video ID
        
    Returns:
        str: Video ID
    """
    # Check if it's a URL
    if "youtube.com" in video_input or "youtu.be" in video_input:
        # Handle youtube.com URLs
        if "youtube.com" in video_input:
            parsed_url = urlparse(video_input)
            return parse_qs(parsed_url.query)['v'][0]
        # Handle youtu.be URLs
        elif "youtu.be" in video_input:
            return video_input.split('/')[-1].split('?')[0]
    # Assume it's already a video ID
    else:
        # Remove any parameters that might be attached to the ID
        return video_input.split('&')[0]
    
def print_comment_tree(comment, level=0, prefix=""):
    """Helper function to print nested comment structure"""
    if level == 0:
        print(f"{comment['author']}: {comment['text']}")
        print(f"Likes: {comment['likes']} | Published: {comment['published']}")
        prefix = "   "
    
    if comment.get('replies'):
        for i, reply in enumerate(comment['replies'], 1):
            print(f"{prefix}└─ {reply['author']}: {reply['text']}")
            print(f"{prefix}   Likes: {reply['likes']} | Published: {reply['published']}")
            print_comment_tree(reply, level + 1, prefix + "   ")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Scrape comments from a YouTube video")
    parser.add_argument("video_input", help="YouTube video URL or ID")
    parser.add_argument("--api-key", "-k", required=True, help="YouTube Data API key")
    parser.add_argument("--max", "-m", type=int, default=100, help="Maximum number of comments to retrieve")
    parser.add_argument("--output", "-o", help="Output file path (optional)")
    args = parser.parse_args()
    
    # Extract video ID
    video_id = extract_video_id(args.video_input)
    
    # Fetch comments
    print(f"Fetching up to {args.max} comments for video {video_id}...")
    comments = get_video_comments(video_id, args.api_key, args.max)
    
    # Calculate total comments including replies
    total_comments = sum(len(comment['replies']) + 1 for comment in comments)
    
    # Display or save results
    if args.output:
        if args.output.endswith('.csv'):
            import json
            # Create a temporary JSON file
            temp_json = 'temp_comments.json'
            with open(temp_json, 'w', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
            
            # Convert JSON to CSV
            json_to_csv(temp_json, args.output)
            
            # Remove temporary JSON file
            os.remove(temp_json)
            print(f"Saved {total_comments} comments (including replies) to {args.output}")
        else:
            # Save as JSON
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=2)
            print(f"Saved {total_comments} comments (including replies) to {args.output}")
    else:
        for i, comment in enumerate(comments, 1):
            print(f"\n{i}.")
            print_comment_tree(comment)
            print("-" * 80)
    
    print(f"Total comments retrieved: {len(comments)} main comments and {total_comments - len(comments)} replies")
    print(f"Total including replies: {total_comments}")

if __name__ == "__main__":
    main()