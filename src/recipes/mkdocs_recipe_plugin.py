"""MkDocs plugin for recipes."""

import json
import re
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

from mkdocs.config import config_options
from mkdocs.config.base import Config
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page


class RecipePluginConfig(Config):
    """Configuration options for the RecipePlugin.

    This class inherits from mkdocs.config.base.Config and defines the
    configuration schema for the RecipePlugin.

    Attributes
    ----------
        recipes_dir: Directory path where recipe markdown files are stored
        images_dir: Directory path where recipe images are stored
        image_extensions: Map of recipe names to image extensions (defaults to jpg)
    """

    recipes_dir = config_options.Type(str, default="docs/recipes")
    images_dir = config_options.Type(str, default="docs/images")
    image_extensions = config_options.Type(dict, default={})


class RecipePlugin(BasePlugin[RecipePluginConfig]):
    """MkDocs plugin that transforms recipe markdown files to include HTML tables and images.

    This plugin processes markdown files in the configured recipes directory,
    extracting recipe information and transforming it into an HTML table
    with the recipe image displayed alongside.
    """

    def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
        """Process the configuration before building.

        Args:
            config: MkDocs configuration dictionary

        Returns
        -------
            The modified configuration
        """
        # Generate index files for recipes
        try:
            from recipes.auto_index import on_startup

            on_startup()
        except Exception as e:
            print(f"Error generating recipe index files: {e}")

        # Ensure the database exists
        db_path = Path("docs/database/recipes.db")
        if not db_path.exists():
            # Create an empty database file
            db_path.parent.mkdir(exist_ok=True, parents=True)

            try:
                # Try to populate the database with recipe data
                from recipes.parse_recipes import populate_database

                populate_database()
            except Exception as e:
                print(f"Error populating recipe database: {e}")
                # Create an empty file if we can't import the database
                with open(db_path, "wb") as f:
                    pass

        # Generate the recipes JSON file directly in the docs directory
        # This ensures it will be copied to the site directory during build
        json_dir = Path("docs/recipes/api")
        json_dir.mkdir(exist_ok=True, parents=True)
        self._generate_recipe_json(db_path, json_dir / "recipes.json")

        return config

    def on_serve(self, server: Any, config: MkDocsConfig, builder: Any) -> Any:
        """Add recipe API endpoint to the development server.

        Args:
            server: The WSGI server instance
            config: The MkDocs configuration dictionary
            builder: The MkDocs builder

        Returns
        -------
            The server instance, potentially modified
        """
        return server

    def on_post_build(self, config: MkDocsConfig) -> None:
        """Run operations after the build is complete.

        Args:
            config: MkDocs configuration dictionary
        """
        # No need to regenerate the JSON file here since we're doing it in on_config
        # and the file will be copied from docs to site directory during the build

    def _generate_recipe_json(self, db_path: Path, output_path: Path) -> None:
        """Generate a JSON file with recipe data.

        Args:
            db_path: Path to the database file
            output_path: Path where the JSON file should be saved
        """
        recipes = []

        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Get table info to check for column existence
                cursor.execute("PRAGMA table_info(recipes)")
                columns = [column_info[1] for column_info in cursor.fetchall()]

                # Build query based on available columns
                select_fields = ["id", "title", "description", "file_path", "language"]
                if "category" in columns:
                    select_fields.append("category")
                if "difficulty" in columns:
                    select_fields.append("difficulty")
                if "prep_time" in columns:
                    select_fields.append("prep_time")
                if "cook_time" in columns:
                    select_fields.append("cook_time")
                if "total_time" in columns:
                    select_fields.append("total_time")
                if "servings" in columns:
                    select_fields.append("servings")

                query = f"SELECT {', '.join(select_fields)} FROM recipes"
                cursor.execute(query)

                recipes = [dict(row) for row in cursor.fetchall()]
                conn.close()
            except Exception as e:
                print(f"Error generating recipe JSON: {e}")

        # Ensure directory exists
        output_path.parent.mkdir(exist_ok=True, parents=True)

        # Write JSON to file
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)

        print(f"Generated recipe API file at {output_path} with {len(recipes)} recipes")

    def on_page_markdown(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,  # noqa: ARG002
        files: Files,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> str:
        """Transform markdown for recipe pages.

        Args:
            markdown: The markdown content of the page
            page: The page object containing file information
            config: The MkDocs configuration dictionary
            files: The Files collection
            **kwargs: Additional arguments passed by MkDocs

        Returns
        -------
            str: The transformed markdown content
        """
        file_path = page.file.src_path

        # Skip processing if not a recipe file
        if not self._is_recipe_file(file_path):
            return markdown

        # Extract recipe name from the first heading
        recipe_name = self._extract_recipe_name(markdown)
        if not recipe_name:
            return markdown

        # Extract and parse recipe information section
        recipe_section_match = self._extract_recipe_info_section(markdown)
        if not recipe_section_match:
            return markdown

        # Parse recipe information items
        info_items = self._parse_recipe_info_items(recipe_section_match[2].strip())
        if not info_items:
            return markdown

        # Create image path
        image_path = self._get_image_path(file_path)

        # Generate HTML table with recipe info and image
        html_table = self._generate_recipe_html_table(recipe_name, info_items, image_path)

        # Replace original section with new HTML content
        return self._replace_recipe_section(
            markdown,
            recipe_section_match[0],
            recipe_section_match[1],
            html_table,
            recipe_section_match[3],
        )

    def _is_recipe_file(self, file_path: str) -> bool:
        """Determine if the file should be processed as a recipe.

        Args:
            file_path: Path to the markdown file

        Returns
        -------
            bool: True if file should be processed, False otherwise
        """
        # Skip files that are already in HTML format
        if "_html" in file_path:
            return False

        # Only process files in the recipes directory
        # Allow for both with and without the docs/ prefix
        return (
            file_path.startswith((self.config.recipes_dir, f"docs/{self.config.recipes_dir}"))
            or f"/{self.config.recipes_dir}/" in file_path
        )

    def _extract_recipe_name(self, markdown: str) -> str | None:
        """Extract recipe name from the first heading in markdown.

        Args:
            markdown: The markdown content

        Returns
        -------
            Optional[str]: The recipe name if found, None otherwise
        """
        recipe_name_match = re.search(r"^# (.*?)$", markdown, re.MULTILINE)
        if not recipe_name_match:
            return None
        return recipe_name_match.group(1)

    def _extract_recipe_info_section(self, markdown: str) -> tuple[str, str, str, str] | None:
        """Extract the recipe information section from markdown.

        Args:
            markdown: The markdown content

        Returns
        -------
            Optional[Tuple[str, str, str, str]]: A tuple containing:
                - Full matched section
                - Section heading
                - Section content
                - Next heading
                Or None if section not found
        """
        recipe_info_section_match = re.search(
            r"(## Recipe Information\s+)(.*?)(##)",
            markdown,
            re.DOTALL,
        )

        if not recipe_info_section_match:
            return None

        return (
            recipe_info_section_match.group(0),
            recipe_info_section_match.group(1),
            recipe_info_section_match.group(2),
            recipe_info_section_match.group(3),
        )

    def _parse_recipe_info_items(self, info_content: str) -> list[tuple[str, str]]:
        """Parse recipe information items from the content.

        Args:
            info_content: Content of the recipe information section

        Returns
        -------
            List[Tuple[str, str]]: List of (key, value) pairs of recipe information
        """
        info_items: list[tuple[str, str]] = []

        # Use a more flexible pattern to match the list items
        pattern = r"- \*\*(.*?)\*\*:?\s*(.*?)(?:\r\n|\n|$)"
        matches = re.findall(pattern, info_content, re.MULTILINE)

        # Process each match and add it to info_items
        for key, value in matches:
            stripped_key = key.strip().removesuffix(":")
            stripped_value = value.strip()
            if stripped_key and stripped_value:  # Ensure we have both key and value
                info_items.append((stripped_key, stripped_value))

        return info_items

    def _get_image_path(self, file_path: str) -> str:
        """Create image path based on markdown filename.

        Args:
            file_path: Path to the markdown file

        Returns
        -------
            str: Relative path to the image file
        """
        # Get basic file name without extension
        file_path = Path(file_path)
        image_stem = file_path.stem

        # Determine category from file path
        category = None
        for part in file_path.parts:
            if part in ["breakfast", "main", "side", "dessert", "starter"]:
                category = part
                break

        # If we found the category, check for actual image files
        if category:
            # Base path for category images
            category_images_dir = f"docs/recipes/{category}/images"

            # Check for all possible image extensions, including jpeg
            for ext in ["webp", "jpg", "jpeg", "png", "gif"]:
                image_path = Path(f"{category_images_dir}/{image_stem}.{ext}")
                if image_path.exists():
                    print(f"Found image: {image_path}")
                    # Use ../images for all images (relative path from recipe page)
                    return f"../images/{image_stem}.{ext}"

        # Use fallback based on what we usually have
        if category:
            print(f"No image found, defaulting to ../images/{image_stem}.webp")
            return f"../images/{image_stem}.webp"
        print(f"No category found, defaulting to ../images/{image_stem}.webp")
        return f"../images/{image_stem}.webp"

    def _generate_recipe_html_table(
        self,
        recipe_name: str,
        info_items: list[tuple[str, str]],
        image_path: str,
    ) -> str:
        """Generate HTML table with recipe information and image.

        Args:
            recipe_name: Name of the recipe
            info_items: List of (key, value) pairs of recipe information
            image_path: Path to the recipe image

        Returns
        -------
            str: HTML table with recipe information and image
        """
        # Create HTML table
        table_html = '<div style="display: flex; flex-direction: row; align-items: center;">\n'
        table_html += '    <div style="flex: 1; display: flex; justify-content: center;">\n'
        table_html += "        <table>\n"
        table_html += "            <tr><th>Information</th><th>Details</th></tr>\n"

        for key, value in info_items:
            table_html += f"            <tr><td>{key}</td><td>{value}</td></tr>\n"

        table_html += "        </table>\n"
        table_html += "    </div>\n"
        table_html += '    <div style="flex: 1; padding-left: 20px; display: flex; justify-content: center;">\n'
        table_html += (
            f'        <img src="{image_path}" alt="{recipe_name}" style="max-width: 100%;">\n'
        )
        table_html += "    </div>\n"
        table_html += "</div>\n"

        return table_html

    def _replace_recipe_section(
        self,
        markdown: str,
        original_section: str,
        section_heading: str,
        html_content: str,
        next_heading: str,
    ) -> str:
        """Replace the original Recipe Information section with HTML content.

        Args:
            markdown: The original markdown content
            original_section: The full original section to replace
            section_heading: The section heading to preserve
            html_content: The new HTML content to insert
            next_heading: The next heading after the section

        Returns
        -------
            str: The transformed markdown content
        """
        section_start_index = markdown.find(original_section)
        next_heading_index = section_start_index + len(original_section) - len(next_heading)

        # Replace the original Recipe Information section with our HTML table
        return (
            markdown[:section_start_index]
            + section_heading  # Keep the "## Recipe Information" heading
            + html_content
            + markdown[
                next_heading_index:
            ]  # Keep everything after, including the next "##" heading
        )
