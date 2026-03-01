import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_URL = "https://api.monday.com/v2"


def _get_headers():
    if not MONDAY_API_KEY:
        raise ValueError("MONDAY_API_KEY environment variable is not set.")

    return {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json",
        "API-Version": "2023-10"
    }


def get_column_titles(board_id: str):
    """
    Fetch only column titles for a given board.
    Returns a list of column title strings.
    """
    query = """
    query ($board_id: [ID!]) {
        boards(ids: $board_id) {
            columns {
                id
                title
            }
        }
    }
    """

    response = requests.post(
        MONDAY_API_URL,
        json={
            "query": query,
            "variables": {"board_id": int(board_id)}
        },
        headers=_get_headers()
    )

    if response.status_code != 200:
        raise Exception(f"Monday API error: {response.status_code} {response.text}")

    data = response.json()

    if "errors" in data:
        raise Exception(f"GraphQL Errors: {data['errors']}")

    boards = data.get("data", {}).get("boards", [])
    if not boards:
        return []

    return [col["title"] for col in boards[0].get("columns", [])]


def fetch_board_data(board_id: str, columns_to_keep: list | None = None):
    """
    Fetch all items from a board.
    Optionally filter to specific column titles.
    Returns list of dictionaries.
    """

    query = """
    query ($board_id: [ID!]) {
        boards(ids: $board_id) {
            name
            columns {
                id
                title
            }
            items_page(limit: 500) {
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
    """

    response = requests.post(
        MONDAY_API_URL,
        json={
            "query": query,
            "variables": {"board_id": int(board_id)}
        },
        headers=_get_headers()
    )

    if response.status_code != 200:
        raise Exception(f"Monday API error: {response.status_code} {response.text}")

    data = response.json()

    if "errors" in data:
        raise Exception(f"GraphQL Errors: {data['errors']}")

    boards = data.get("data", {}).get("boards", [])
    if not boards:
        return []

    board = boards[0]

    # Map column ID → Title
    column_mapping = {
        col["id"]: col["title"]
        for col in board.get("columns", [])
    }

    items = board.get("items_page", {}).get("items", [])

    parsed_items = []

    for item in items:
        parsed_item = {
            "id": item.get("id"),
            "name": item.get("name")
        }

        for col in item.get("column_values", []):
            value = col.get("text")
            if not value:
                continue

            col_id = col.get("id")
            col_title = column_mapping.get(col_id, col_id)

            if columns_to_keep:
                if col_title in columns_to_keep:
                    parsed_item[col_title] = value
            else:
                parsed_item[col_title] = value

        parsed_items.append(parsed_item)

    return parsed_items


# ----------------------------
# Local Test
# ----------------------------
if __name__ == "__main__":
    test_board_id = os.getenv("MONDAY_DEALS_BOARD_ID")

    if not test_board_id:
        print("Set MONDAY_DEALS_BOARD_ID in your .env file.")
    else:
        try:
            items = fetch_board_data(test_board_id)
            print(f"Fetched {len(items)} items.")
            if items:
                print(json.dumps(items[0], indent=2))
        except Exception as e:
            print("Test failed:", e)