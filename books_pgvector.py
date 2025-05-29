import openai
import requests
import json
import psycopg2
import os
from typing import List, Dict, Any

from load_models import get_embedding

def store_book(title: str, book_json: str, embedding: List[float]) -> None:
    """
    Store a book with its embedding in the PostgreSQL database.
    Args:
        title: The title of the book
        book_json: JSON string containing book data
        embedding: Vector embedding of the book description
    Returns:
        None
    """
    # Get database connection string from environment variable
    db_url = os.environ.get("DATABASE_URL", "postgresql://chinook:chinook@localhost:5433/chinook_db")
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        # Insert the book data and embedding into the database
        cursor.execute(
            """
            INSERT INTO items (name, item_data, embedding)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (title, book_json, embedding)
        )
        # Get the ID of the newly inserted book
        book_id = cursor.fetchone()[0]
        # Commit the transaction
        conn.commit()
        print(f"Successfully stored '{title}' with ID {book_id} in the database")
    except Exception as e:
        print(f"Error storing book in database: {e}")
        # Roll back the transaction in case of error
        if conn:
            conn.rollback()
    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def fetch_books(search_query: str = "python programming",
                limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch books from the Open Library API.
    Args:
        search_query: The search term for finding books (default: "python programming")
        limit: Maximum number of books to return (default: 10)
    Returns:
        A list of dictionaries containing book information
    """
    base_url = "https://openlibrary.org/search.json"
    # Define parameters for the API request
    params = {
        "q": search_query,
        "limit": limit,
        "fields": "key,title,author_name,first_publish_year,cover_i,edition_count,subject"
    }
    try:
        # Make the API request
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        books = data.get("docs", [])
        # Process and format the book data
        formatted_books = []
        for book in books:
            # Create a cleaner book object with consistent fields
            formatted_book = {
                "title": book.get("title", "Unknown Title"),
                "authors": book.get("author_name", ["Unknown Author"]),
                "publish_year": book.get("first_publish_year", "Unknown"),
                "cover_id": book.get("cover_i"),
                "edition_count": book.get("edition_count", 0),
                "subjects": book.get("subject", []),
                "key": book.get("key", "")
            }
            formatted_books.append(formatted_book)
        print(f"Successfully fetched {len(formatted_books)} books about '{search_query}'")
        return formatted_books
    except requests.exceptions.RequestException as e:
        print(f"Error fetching books from Open Library API: {e}")
        return []
def load_books_to_db():
    """Load books with embeddings into PostgreSQL"""
    # 1. Fetches books from Open Library API
    books = fetch_books()
    for book in books:
        # 2.Create text description for embedding
        print(book)
        description = f"Book titled '{book['title']}' by {', '.join(book['authors'])}. "
        description += f"Published in {book['publish_year']}. "
        description += f"This is a book about {[x + ', ' for x in book['subjects']]}."
        # 3. Generate embedding using OpenAI
        embedding = get_embedding(description)
        # 4. Stores books and embeddings in PostgreSQL
        store_book(book["title"], json.dumps(book), embedding)
if __name__ == '__main__':
    print(1)
    load_books_to_db()