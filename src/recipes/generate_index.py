"""Generate index files for recipe categories."""

import os
import re
from pathlib import Path


def extract_title_from_markdown(file_path: str) -> str:
    """Extract the recipe title from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns
    -------
        The extracted title, or a capitalized filename if title not found
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
            # Look for H1 title (# Title)
            title_match = re.search(r"^# (.+)$", content, re.MULTILINE)
            if title_match:
                return title_match.group(1).strip()
    except Exception as e:
        print(f"Error reading title from {file_path}: {e}")

    # Fallback to filename
    filename = os.path.splitext(os.path.basename(file_path))[0]
    return filename.replace("_", " ").title()


def generate_category_index(category: str, title: str) -> None:
    """Generate an index markdown file for a recipe category.

    Args:
        category: The category folder name (e.g., 'breakfast', 'main')
        title: The title to use for the index page
    """
    recipes_dir = Path("docs/recipes")
    category_dir = recipes_dir / category
    index_file = recipes_dir / f"{category}.md"

    # Skip if the category directory doesn't exist
    if not category_dir.exists() or not category_dir.is_dir():
        print(f"Category directory {category_dir} does not exist")
        return

    # Get all markdown files in the category directory
    recipe_files = sorted([f for f in os.listdir(category_dir) if f.endswith(".md")])

    # Skip if no recipe files found
    if not recipe_files:
        print(f"No recipe files found in {category_dir}")
        return

    # Generate the index content
    content = [
        f"# {title}",
        "",
        "## Recipes",
        "",
    ]

    # Add links to each recipe - use proper relative path without doubling "recipes/"
    for recipe_file in recipe_files:
        # Extract the actual title from the markdown file
        recipe_path = category_dir / recipe_file
        recipe_title = extract_title_from_markdown(str(recipe_path))
        content.append(f"- [{recipe_title}]({category}/{recipe_file})")

    # Write the index file
    with open(index_file, "w") as f:
        f.write("\n".join(content))

    print(f"Generated index file for {category} at {index_file}")


def generate_all_indexes() -> None:
    """Generate index files for all recipe categories."""
    categories = {
        "breakfast": "Breakfast",
        "main": "Main Dishes",
        "side": "Side Dishes",
        "dessert": "Desserts",
        "starter": "Starters",
    }

    for category, title in categories.items():
        generate_category_index(category, title)


if __name__ == "__main__":
    generate_all_indexes()
