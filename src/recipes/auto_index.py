"""Script to automatically generate index files during docs build."""

import os
import re
from pathlib import Path
from typing import Dict, List


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


def scan_recipe_directories() -> dict[str, list[dict[str, str]]]:
    """Scan all recipe directories and build a map of categories to recipe files.

    Returns
    -------
        A dictionary mapping category names to lists of recipe info dictionaries
    """
    recipes_dir = Path("docs/recipes")
    categories = ["breakfast", "main", "side", "dessert", "starter"]

    result = {}

    for category in categories:
        category_dir = recipes_dir / category
        if not category_dir.exists() or not category_dir.is_dir():
            print(f"Category directory {category_dir} does not exist")
            continue

        # Get all markdown files in the category directory
        recipe_files = sorted([f for f in os.listdir(category_dir) if f.endswith(".md")])

        # Skip if no recipe files found
        if not recipe_files:
            print(f"No recipe files found in {category_dir}")
            continue

        # Build list of recipe info
        recipes = []
        for recipe_file in recipe_files:
            recipe_path = category_dir / recipe_file
            title = extract_title_from_markdown(str(recipe_path))
            recipes.append(
                {
                    "title": title,
                    "filename": recipe_file,
                    "path": str(recipe_path),
                },
            )

        result[category] = recipes

    return result


def generate_index_files(recipes_by_category: dict[str, list[dict[str, str]]]) -> None:
    """Generate index markdown files for all categories.

    Args:
        recipes_by_category: Dictionary mapping categories to recipe information
    """
    recipes_dir = Path("docs/recipes")

    # Map of category to display title
    category_titles = {
        "breakfast": "Breakfast",
        "main": "Main Dishes",
        "side": "Side Dishes",
        "dessert": "Desserts",
        "starter": "Starters",
    }

    for category, recipes in recipes_by_category.items():
        index_file = recipes_dir / f"{category}.md"
        title = category_titles.get(category, category.title())

        content = [
            f"# {title}",
            "",
            "## Recipes",
            "",
        ]

        # Add links to each recipe with actual titles
        for recipe in recipes:
            content.append(f"- [{recipe['title']}]({category}/{recipe['filename']})")

        # Write the index file
        with open(index_file, "w") as f:
            f.write("\n".join(content))

        print(f"Generated index file for {category} at {index_file}")


def on_startup() -> None:
    """Function to run when the docs site is starting up."""
    # Scan recipe directories
    recipes_by_category = scan_recipe_directories()

    # Generate index files
    generate_index_files(recipes_by_category)

    print("Recipe index files have been generated/updated.")


if __name__ == "__main__":
    on_startup()
