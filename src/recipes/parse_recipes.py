#!/usr/bin/env python

"""
Recipe Markdown Parser and Formatter.

This module:
1. Parses markdown recipe files
2. Populates a SQLite database with structured data
3. Provides a markdown preprocessing extension that applies HTML styling

Usage:
- As a standalone script to populate the database
- As a MkDocs extension for formatting
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Any


class RecipeParser:
    """Parser for recipe markdown files."""

    def __init__(self, file_path: str) -> None:
        """Initialize with the path to a markdown recipe file.

        Args:
            file_path: Path to the markdown recipe file
        """
        self.file_path = file_path
        with Path(file_path).open(encoding="utf-8") as f:
            self.content = f.read()

        self.recipe_data: dict[str, Any] = {
            "title": "",
            "description": "",
            "info": {},
            "ingredients": {},
            "instructions": {},
            "storage_tips": [],
            "serving_suggestions": [],
            "recipe_notes": [],
        }
        self.parse()

    def parse(self) -> None:
        """Parse the markdown content into structured data."""
        self._parse_title_and_description()
        self._parse_recipe_info()
        self._parse_ingredients()
        self._parse_instructions()
        self._parse_additional_sections()

    def _parse_title_and_description(self) -> None:
        """Extract the title and description from the markdown."""
        # Extract title (H1)
        title_match = re.search(r"^# (.+)$", self.content, re.MULTILINE)
        if title_match:
            self.recipe_data["title"] = title_match.group(1).strip()

        # Extract description (italicized text after title)
        desc_match = re.search(r"^# .+\n\n\*(.+)\*", self.content, re.MULTILINE | re.DOTALL)
        if desc_match:
            self.recipe_data["description"] = desc_match.group(1).strip()

    def _parse_recipe_info(self) -> None:
        """Extract recipe information section."""
        info_section = self._extract_section(
            r"## Recipe Information\n(.*?)(?:\n##|\Z)",
            self.content,
        )
        if info_section:
            info_lines = re.findall(r"- \*\*(.+?):\*\* (.+)", info_section)
            self.recipe_data["info"] = {
                key.lower().replace(" ", "_"): value for key, value in info_lines
            }

    def _parse_ingredients(self) -> None:
        """Extract ingredients section."""
        ingredients_section = self._extract_section(
            r"## Ingredients\n(.*?)(?:\n##|\Z)",
            self.content,
        )
        if ingredients_section:
            # Find all ingredient categories (### headers)
            categories = re.findall(r"### (.+)\n(.*?)(?=\n###|\Z)", ingredients_section, re.DOTALL)
            for category, items in categories:
                ingredient_items = re.findall(r"- (.+)", items)
                self.recipe_data["ingredients"][category.strip()] = [
                    item.strip() for item in ingredient_items
                ]

    def _parse_instructions(self) -> None:
        """Extract instructions section."""
        instructions_section = self._extract_section(
            r"## Instructions\n(.*?)(?:\n##|\Z)",
            self.content,
        )
        if instructions_section:
            # Find all instruction phases (### headers)
            phases = re.findall(r"### (.+)\n(.*?)(?=\n###|\Z)", instructions_section, re.DOTALL)
            for phase, items in phases:
                step_items = re.findall(r"\d+\.\s+(.+)", items)
                self.recipe_data["instructions"][phase.strip()] = [
                    item.strip() for item in step_items
                ]

    def _parse_additional_sections(self) -> None:
        """Extract storage tips, serving suggestions, and notes."""
        # Extract storage tips
        self._parse_list_section("storage_tips", "## Storage Tips")

        # Extract serving suggestions
        self._parse_list_section("serving_suggestions", "## Serving Suggestions")

        # Extract recipe notes
        self._parse_list_section("recipe_notes", "## Recipe Notes")

    def _parse_list_section(self, section_name: str, section_header: str) -> None:
        """Parse a section containing a list of items.

        Args:
            section_name: Name of the section in recipe_data
            section_header: Markdown header for the section
        """
        pattern = f"{section_header}\\n(.*?)(?:\\n##|\\Z)"
        section_content = self._extract_section(pattern, self.content)
        if section_content:
            self.recipe_data[section_name] = [
                item.strip() for item in re.findall(r"- (.+)", section_content)
            ]

    def _extract_section(self, pattern: str, text: str) -> str | None:
        """Extract a section of text using a regex pattern.

        Args:
            pattern: Regular expression pattern to match
            text: Text to search in

        Returns
        -------
            The extracted section text or None if not found
        """
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else None

    def get_data(self) -> dict[str, Any]:
        """Return the parsed recipe data.

        Returns
        -------
            Dictionary containing structured recipe data
        """
        return self.recipe_data

    def get_formatted_markdown(self) -> str:
        """Convert the clean markdown to styled markdown with HTML elements.

        Returns
        -------
            Formatted markdown string with HTML styling
        """
        formatted_md: list[str] = []

        # Add title and description
        self._add_header_section(formatted_md)

        # Add info table and image container
        self._add_info_and_image_section(formatted_md)

        # Add ingredients section
        self._add_ingredients_section(formatted_md)

        # Add instructions section
        self._add_instructions_section(formatted_md)

        # Add additional sections
        self._add_additional_sections(formatted_md)

        # Add footer
        formatted_md.append("---\n")
        formatted_md.append("*Recipe formatted with automatic styling*")

        return "\n".join(formatted_md)

    def _add_header_section(self, formatted_md: list[str]) -> None:
        """Add title and description to the formatted markdown.

        Args:
            formatted_md: List to append markdown lines to
        """
        formatted_md.append(f"# {self.recipe_data['title']}\n")
        formatted_md.append(f"> *{self.recipe_data['description']}*\n")

    def _add_info_and_image_section(self, formatted_md: list[str]) -> None:
        """Add info section and image to the formatted markdown.

        Args:
            formatted_md: List to append markdown lines to
        """
        formatted_md.append("## Recipe Information\n")

        # Convert recipe info to HTML table
        formatted_md.append(
            '<div style="display: flex; flex-direction: row; align-items: center;">',
        )
        formatted_md.append('    <div style="flex: 1; display: flex; justify-content: center;">')
        formatted_md.append("        <table>")
        formatted_md.append("            <tr><th>Information</th><th>Details</th></tr>")

        for key, value in self.recipe_data["info"].items():
            formatted_md.append(f"            <tr><td>{key}</td><td>{value}</td></tr>")

        formatted_md.append("        </table>")
        formatted_md.append("    </div>")

        # Extract image name from file path (without extension)
        file_path = Path(self.file_path)
        image_name = file_path.stem

        # Identify category from file path
        category = None
        for part in file_path.parts:
            if part in ["breakfast", "main", "side", "dessert", "starter"]:
                category = part
                break

        # Add image container
        formatted_md.append(
            '    <div style="flex: 1; padding-left: 20px; display: flex; justify-content: center;">',
        )

        # Use the appropriate path for images - critical to use ../images/ not images/
        image_path = None
        if category:
            # Check all possible image types
            category_images_dir = f"docs/recipes/{category}/images"
            for ext in ["webp", "jpg", "jpeg", "png", "gif"]:
                check_path = Path(f"{category_images_dir}/{image_name}.{ext}")
                if check_path.exists():
                    image_path = f"../images/{image_name}.{ext}"
                    break

        # Default to webp if no image found
        if not image_path:
            image_path = f"../images/{image_name}.webp"

        formatted_md.append(
            f'        <img src="{image_path}" alt="{self.recipe_data["title"]}" style="max-width: 100%;">',
        )

        formatted_md.append("    </div>")
        formatted_md.append("</div>\n")

        # Add section separator
        formatted_md.append("---\n")

    def _add_ingredients_section(self, formatted_md: list[str]) -> None:
        """Add ingredients section to the formatted markdown.

        Args:
            formatted_md: List to append markdown lines to
        """
        formatted_md.append("## Ingredients\n")
        for category, ingredients in self.recipe_data["ingredients"].items():
            formatted_md.append(f"### {category}")
            formatted_md.extend([f"- {ingredient}" for ingredient in ingredients])
            formatted_md.append("")

        # Add section separator
        formatted_md.append("---\n")

    def _add_instructions_section(self, formatted_md: list[str]) -> None:
        """Add instructions section to the formatted markdown.

        Args:
            formatted_md: List to append markdown lines to
        """
        formatted_md.append("## Instructions\n")
        step_counter = 1
        for phase, steps in self.recipe_data["instructions"].items():
            formatted_md.append(f"### {phase}")
            for step in steps:
                bolded_step = self._bold_first_word(step)
                formatted_md.append(f"{step_counter}. {bolded_step}")
                step_counter += 1
            formatted_md.append("")

    def _bold_first_word(self, text: str) -> str:
        """Bold the first word of a string.

        Args:
            text: The text to process

        Returns
        -------
            Text with first word in bold
        """
        first_word_end = text.find(" ")
        if first_word_end > 0:
            return f"**{text[:first_word_end]}** {text[first_word_end + 1 :]}"
        return text

    def _add_additional_sections(self, formatted_md: list[str]) -> None:
        """Add additional sections (tips, suggestions, notes) to the formatted markdown.

        Args:
            formatted_md: List to append markdown lines to
        """
        for section_title, items in [
            ("Storage Tips", self.recipe_data["storage_tips"]),
            ("Serving Suggestions", self.recipe_data["serving_suggestions"]),
            ("Recipe Notes", self.recipe_data["recipe_notes"]),
        ]:
            if items:
                formatted_md.append("---\n")
                formatted_md.append(f"## {section_title}\n")
                formatted_md.extend([f"- {item}" for item in items])
                formatted_md.append("")


class RecipeDatabase:
    """Database handler for recipes."""

    def __init__(self, db_path: str) -> None:
        """Initialize with the path to the SQLite database.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self) -> None:
        """Create the necessary database tables if they don't exist."""
        # Create main recipe table
        self._create_recipe_table()

        # Create ingredient table
        self._create_ingredient_table()

        # Create instruction table
        self._create_instruction_table()

        # Create additional tables
        self._create_additional_tables()

        self.conn.commit()

    def _create_recipe_table(self) -> None:
        """Create the main recipe table."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            file_path TEXT NOT NULL,
            language TEXT,
            category TEXT,
            difficulty TEXT,
            prep_time TEXT,
            cook_time TEXT,
            total_time TEXT,
            servings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

    def _create_ingredient_table(self) -> None:
        """Create the ingredients table."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
            id INTEGER PRIMARY KEY,
            recipe_id INTEGER,
            category TEXT,
            ingredient TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
        )
        """)

    def _create_instruction_table(self) -> None:
        """Create the instructions table."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS instructions (
            id INTEGER PRIMARY KEY,
            recipe_id INTEGER,
            phase TEXT,
            step_number INTEGER,
            instruction TEXT NOT NULL,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
        )
        """)

    def _create_additional_tables(self) -> None:
        """Create tips and notes tables."""
        for table in ["storage_tips", "serving_suggestions", "recipe_notes"]:
            self.cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id INTEGER PRIMARY KEY,
                recipe_id INTEGER,
                text TEXT NOT NULL,
                FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE
            )
            """)

    def clear_all_data(self) -> None:
        """Clear all data from all tables."""
        tables = [
            "recipe_notes",
            "serving_suggestions",
            "storage_tips",
            "instructions",
            "ingredients",
            "recipes",
        ]
        for table in tables:
            self.cursor.execute(f"DELETE FROM {table}")
        self.conn.commit()

    def add_recipe(self, recipe_data: dict[str, Any], file_path: str) -> int:
        """Add a recipe to the database and return its ID.

        Args:
            recipe_data: Structured recipe data
            file_path: Path to the source markdown file

        Returns
        -------
            The ID of the inserted recipe

        Raises
        ------
            ValueError: If unable to get recipe ID after insertion
        """
        # Insert main recipe data
        recipe_id = self._insert_recipe_main_data(recipe_data, file_path)

        # Insert related data
        self._insert_recipe_ingredients(recipe_id, recipe_data)
        self._insert_recipe_instructions(recipe_id, recipe_data)
        self._insert_recipe_additional_data(recipe_id, recipe_data)

        self.conn.commit()
        return recipe_id

    def _insert_recipe_main_data(self, recipe_data: dict[str, Any], file_path: str) -> int:
        """Insert main recipe data and return the recipe ID.

        Args:
            recipe_data: Structured recipe data
            file_path: Path to the source markdown file

        Returns
        -------
            The ID of the inserted recipe

        Raises
        ------
            ValueError: If unable to get recipe ID after insertion
        """
        # Determine language by checking for Dutch keywords in the title
        language = self._determine_language(recipe_data["title"])

        # Extract category and difficulty if present
        category = recipe_data["info"].get("course", "")
        difficulty = recipe_data["info"].get("difficulty", "")

        # Insert main recipe info
        self.cursor.execute(
            """
        INSERT INTO recipes (
            title, description, file_path, language,
            category, difficulty, prep_time, cook_time,
            total_time, servings
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                recipe_data["title"],
                recipe_data["description"],
                file_path,
                language,
                category,
                difficulty,
                recipe_data["info"].get("prep_time", ""),
                recipe_data["info"].get("cook_time", ""),
                recipe_data["info"].get("total_time", ""),
                recipe_data["info"].get("servings", ""),
            ),
        )

        recipe_id = self.cursor.lastrowid
        if recipe_id is None:
            msg = "Failed to get recipe ID after insertion"
            raise ValueError(msg)

        return recipe_id

    def _determine_language(self, title: str) -> str:
        """Determine the language of a recipe based on its title.

        Args:
            title: Recipe title

        Returns
        -------
            Language code ('nl' for Dutch, 'en' for English)
        """
        # Dutch keywords often found in recipe titles
        dutch_keywords = [
            "boterkoek",
            "appeltaart",
            "stroopwafel",
            "poffertjes",
            "speculaas",
            "stamppot",
            "hutspot",
            "erwtensoep",
            "bitterballen",
            "oliebollen",
            "zoete",
            "koek",
            "taart",
            "saus",
            "soep",
            "gebak",
        ]

        # Check if any Dutch keywords are in the title
        title_lower = title.lower()
        for keyword in dutch_keywords:
            if keyword in title_lower:
                return "nl"

        # Default to English
        return "en"

    def _insert_recipe_ingredients(self, recipe_id: int, recipe_data: dict[str, Any]) -> None:
        """Insert recipe ingredients.

        Args:
            recipe_id: ID of the recipe
            recipe_data: Structured recipe data
        """
        for category, ingredients in recipe_data["ingredients"].items():
            for ingredient in ingredients:
                self.cursor.execute(
                    """
                INSERT INTO ingredients (recipe_id, category, ingredient)
                VALUES (?, ?, ?)
                """,
                    (recipe_id, category, ingredient),
                )

    def _insert_recipe_instructions(self, recipe_id: int, recipe_data: dict[str, Any]) -> None:
        """Insert recipe instructions.

        Args:
            recipe_id: ID of the recipe
            recipe_data: Structured recipe data
        """
        for phase, steps in recipe_data["instructions"].items():
            for step_num, instruction in enumerate(steps, 1):
                self.cursor.execute(
                    """
                INSERT INTO instructions (recipe_id, phase, step_number, instruction)
                VALUES (?, ?, ?, ?)
                """,
                    (recipe_id, phase, step_num, instruction),
                )

    def _insert_recipe_additional_data(self, recipe_id: int, recipe_data: dict[str, Any]) -> None:
        """Insert tips, suggestions, and notes.

        Args:
            recipe_id: ID of the recipe
            recipe_data: Structured recipe data
        """
        for field in ["storage_tips", "serving_suggestions", "recipe_notes"]:
            for item in recipe_data.get(field, []):
                self.cursor.execute(
                    f"""
                INSERT INTO {field} (recipe_id, text)
                VALUES (?, ?)
                """,
                    (recipe_id, item),
                )

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()


# MkDocs extension for recipe formatting
class RecipePreprocessor:
    """Preprocessor for MkDocs that converts clean markdown recipes to styled ones."""

    def __init__(self, recipes_dir: str = "docs/recipes") -> None:
        """Initialize the preprocessor.

        Args:
            recipes_dir: Directory containing recipe markdown files
        """
        self.recipes_dir = recipes_dir

    def on_page_markdown(
        self,
        markdown_content: str,
        page: Any,
        config: dict[str, Any],
        files: Any,  # noqa: ARG002
        **kwargs: object,  # noqa: ARG002
    ) -> str:
        """MkDocs hook to process the markdown content before rendering.

        Args:
            markdown_content: Original markdown content
            page: Page object containing file information
            config: MkDocs configuration
            files: MkDocs files collection
            **kwargs: Additional arguments (unused)

        Returns
        -------
            Processed markdown content
        """
        if not self._should_process_page(page.file.src_path):
            return markdown_content

        try:
            # Parse the recipe file
            file_path = Path(config["docs_dir"]) / page.file.src_path
            parser = RecipeParser(str(file_path))

            # Return the HTML-enhanced markdown
            return parser.get_formatted_markdown()
        except Exception as e:  # noqa: BLE001
            print(f"Error processing recipe {page.file.src_path}: {e}")
            return markdown_content

    def _should_process_page(self, src_path: str) -> bool:
        """Determine if this is a recipe page that should be processed.

        Args:
            src_path: Source path of the page

        Returns
        -------
            True if the page should be processed, False otherwise
        """
        return src_path.startswith("recipes/") and src_path.endswith(".md")


# Function to create a MkDocs extension
def make_extension(*args: Any, **kwargs: Any) -> RecipePreprocessor:
    """Create a MkDocs extension.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns
    -------
        Initialized RecipePreprocessor
    """
    return RecipePreprocessor(*args, **kwargs)


def populate_database() -> None:
    """Populate the recipe database from markdown files."""
    print("Starting recipe parser...")

    # Setup paths
    recipes_dir = Path("docs/recipes")
    db_path = Path("docs/database/recipes.db")
    db_path.parent.mkdir(exist_ok=True, parents=True)

    # Initialize database
    db = RecipeDatabase(str(db_path))

    # Clear existing data
    db.clear_all_data()

    # Process recipe files
    process_recipe_files(recipes_dir, db)

    db.close()
    print("Recipe database generation complete!")


def process_recipe_files(recipes_dir: Path, db: RecipeDatabase) -> None:
    """Process all recipe files in the directory.

    Args:
        recipes_dir: Directory containing recipe markdown files
        db: Database instance for storing recipe data
    """
    # Skip index files like main.md, breakfast.md, side.md, etc.
    index_files = ["main.md", "breakfast.md", "side.md", "dessert.md", "sides.md", "starter.md"]

    recipe_files = [
        file for file in list(recipes_dir.glob("**/*.md")) if file.name not in index_files
    ]
    print(f"Found {len(recipe_files)} recipe files")

    for file_path in recipe_files:
        print(f"Processing {file_path}...")
        try:
            parser = RecipeParser(str(file_path))
            recipe_data = parser.get_data()
            recipe_id = db.add_recipe(recipe_data, str(file_path))
            print(f"Added recipe ID {recipe_id}: {recipe_data['title']}")
        except Exception as e:  # noqa: BLE001
            print(f"Error processing {file_path}: {e}")


if __name__ == "__main__":
    populate_database()
