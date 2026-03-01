import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_URL = "https://api.monday.com/v2"

def get_column_titles(board_id: str):
    """
    Fetches only the column titles for a specific board ID.
    Returns a list of column titles.
    """
    if not MONDAY_API_KEY:
        raise ValueError("MONDAY_API_KEY environment variable is not set.")
    
    headers = {
        "Authorization": MONDAY_API_KEY,
        "API-Version": "2023-10"
    }
    
    query = """
    query {
        boards (ids: %s) {
            columns {
                title
            }
        }
    }
    """ % board_id

    response = requests.post(MONDAY_API_URL, json={'query': query}, headers=headers)
    if response.status_code != 200:
        return []
    
    data = response.json()
    boards = data.get("data", {}).get("boards", [])
    if not boards:
        return []
        
    return [col.get("title") for col in boards[0].get("columns", [])]


def fetch_board_data(board_id: str, columns_to_keep: list = None):
    """
    Fetches all items and their column values for a specific board ID.
    If columns_to_keep is provided, only those column titles will be included in the output.
    Returns a list of dictionaries, where each dictionary represents an item.
    """
    if not MONDAY_API_KEY:
        raise ValueError("MONDAY_API_KEY environment variable is not set.")
    
    headers = {
        "Authorization": MONDAY_API_KEY,
        "API-Version": "2023-10"
    }
    
    # We query the board for items, getting the name and the column values (title and text value)
    query = """
    query {
        boards (ids: %s) {
            name
            columns {
                id
                title
            }
            items_page (limit: 500) {
                items {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
    }
    """ % board_id

    response = requests.post(MONDAY_API_URL, json={'query': query}, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")
    
    data = response.json()
    
    if "errors" in data:
         raise Exception(f"GraphQL Errors: {data['errors']}")
         
    try:
        boards = data.get("data", {}).get("boards", [])
        if not boards:
            return []
            
        board = boards[0]
        
        # Create a mapping of column ID -> column Title
        column_mapping = {}
        for col in board.get("columns", []):
            column_mapping[col.get("id")] = col.get("title")
            
        items = board.get("items_page", {}).get("items", [])
        
        parsed_items = []
        for item in items:
            parsed_item = {
                "id": item.get("id"),
                "name": item.get("name")
            }
            # Add dynamic columns
            for col in item.get("column_values", []):
                val = col.get("text")
                if val:
                    col_id = col.get("id")
                    col_title = column_mapping.get(col_id, col_id)
                    
                    # Filter conditionally
                    if columns_to_keep:
                        if col_title in columns_to_keep:
                             parsed_item[col_title] = val
                    else:
                        parsed_item[col_title] = val
                
            parsed_items.append(parsed_item)
            
        return parsed_items
        
    except Exception as e:
        print(f"Error parsing Monday.com response: {e}")
        return []

# Simple test block if run directly
if __name__ == "__main__":
    test_board_id = os.getenv("MONDAY_DEALS_BOARD_ID")
    if test_board_id:
        print(f"Fetching data for board: {test_board_id}")
        try:
            items = fetch_board_data(test_board_id)
            print(f"Successfully fetched {len(items)} items.")
            if items:
                print("Sample item:", json.dumps(items[0], indent=2))
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        print("Set MONDAY_DEALS_BOARD_ID to run the test.")
