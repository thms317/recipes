# Recipe Database

<div class="recipe-table-container">
  <input type="text" id="recipeFilter" placeholder="Filter recipes..." class="recipe-filter">
  <table id="recipeTable" class="recipe-table">
    <thead>
      <tr>
        <th onclick="sortTable(0)">Recipe Name ↕</th>
        <th onclick="sortTable(1)">Category ↕</th>
        <th onclick="sortTable(2)">Difficulty ↕</th>
        <th onclick="sortTable(3)">Prep Time ↕</th>
        <th onclick="sortTable(4)">Cook Time ↕</th>
        <th onclick="sortTable(5)">Total Time ↕</th>
      </tr>
    </thead>
    <tbody id="recipeTableBody">
      <!-- Recipe data will be populated dynamically -->
    </tbody>
  </table>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
  const tableBody = document.getElementById('recipeTableBody');
  // Use a relative path that works for both development and production
  const apiUrl = '../recipes/api/recipes.json';

  // Load recipe data from JSON file
  fetch(apiUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(recipes => {
      if (recipes.length === 0) {
        // Show empty state message
        tableBody.innerHTML = `
          <tr>
            <td colspan="6" class="recipe-table-empty">
              No recipes found in the database. Add recipe markdown files to populate this table.
            </td>
          </tr>
        `;
        return;
      }

      // Populate table with recipes
      recipes.forEach(recipe => {
        // Format difficulty for display (capitalize first letter)
        const displayDifficulty = recipe.difficulty ?
          recipe.difficulty.charAt(0).toUpperCase() + recipe.difficulty.slice(1) :
          '-';

        const row = document.createElement('tr');
        row.innerHTML = `
          <td><a href="${recipe.file_path.replace(/^docs\//, '')}">${recipe.title}</a></td>
          <td>${recipe.category || 'Uncategorized'}</td>
          <td>${displayDifficulty}</td>
          <td>${recipe.prep_time || '-'}</td>
          <td>${recipe.cook_time || '-'}</td>
          <td>${recipe.total_time || '-'}</td>
        `;
        tableBody.appendChild(row);
      });
    })
    .catch(error => {
      console.error('Error loading recipe data:', error);
      tableBody.innerHTML = `
        <tr>
          <td colspan="6" class="recipe-table-empty">
            Error loading recipe data. Please check the browser console for details.
          </td>
        </tr>
      `;
    });

  // Filter functionality
  document.getElementById('recipeFilter').addEventListener('input', function() {
    const filterValue = this.value.toLowerCase();
    const rows = document.querySelectorAll('#recipeTableBody tr');
    let hasVisibleRows = false;

    rows.forEach(row => {
      // Skip the empty state row if present
      if (row.querySelector('.recipe-table-empty')) {
        return;
      }

      const text = row.textContent.toLowerCase();
      const isVisible = text.includes(filterValue);
      row.style.display = isVisible ? '' : 'none';

      if (isVisible) {
        hasVisibleRows = true;
      }
    });

    // Show empty state if no matching recipes
    if (!hasVisibleRows && !document.querySelector('.recipe-table-empty')) {
      const emptyRow = document.createElement('tr');
      emptyRow.className = 'filter-empty-row';
      emptyRow.innerHTML = `
        <td colspan="6" class="recipe-table-empty">
          No recipes match your filter criteria.
        </td>
      `;
      tableBody.appendChild(emptyRow);
    } else {
      // Remove empty filter message if results are found
      const emptyFilterRow = document.querySelector('.filter-empty-row');
      if (emptyFilterRow && hasVisibleRows) {
        emptyFilterRow.remove();
      }
    }
  });
});

// Sorting functionality with improved type handling
function sortTable(columnIndex) {
  const table = document.getElementById('recipeTable');
  const tableBody = document.getElementById('recipeTableBody');

  // Don't sort if we only have an empty message
  if (tableBody.querySelector('.recipe-table-empty')) {
    return;
  }

  let rows = Array.from(tableBody.querySelectorAll('tr:not(.filter-empty-row)'));

  // Get current direction from header
  const header = table.querySelectorAll('th')[columnIndex];
  const currentDirection = header.textContent.includes('↑') ? 'desc' : 'asc';

  // Sort the rows
  rows.sort((a, b) => {
    const cellA = a.querySelectorAll('td')[columnIndex].textContent.toLowerCase();
    const cellB = b.querySelectorAll('td')[columnIndex].textContent.toLowerCase();

    // Handle time values specially (convert to minutes if possible)
    if (columnIndex >= 3 && columnIndex <= 5) {
      const minutesA = extractMinutes(cellA);
      const minutesB = extractMinutes(cellB);

      if (!isNaN(minutesA) && !isNaN(minutesB)) {
        return currentDirection === 'asc' ? minutesA - minutesB : minutesB - minutesA;
      }
    }

    // Regular string comparison
    if (currentDirection === 'asc') {
      return cellA.localeCompare(cellB);
    } else {
      return cellB.localeCompare(cellA);
    }
  });

  // Update the table with sorted rows
  rows.forEach(row => tableBody.appendChild(row));

  // Update headers to show sort direction
  const headers = table.getElementsByTagName('th');
  for (let i = 0; i < headers.length; i++) {
    headers[i].textContent = headers[i].textContent.replace(' ↑', '').replace(' ↓', '').replace(' ↕', '');
    if (i === columnIndex) {
      headers[i].textContent += currentDirection === 'asc' ? ' ↑' : ' ↓';
    } else {
      headers[i].textContent += ' ↕';
    }
  }
}

// Helper function to extract minutes from time strings
function extractMinutes(timeStr) {
  if (timeStr === '-') return 0;

  const hourMatch = timeStr.match(/(\d+)\s*hour/);
  const minuteMatch = timeStr.match(/(\d+)\s*minute/);

  let total = 0;
  if (hourMatch) total += parseInt(hourMatch[1]) * 60;
  if (minuteMatch) total += parseInt(minuteMatch[1]);

  return total;
}
</script>

## Database Schema

The recipe database uses the following schema:

```text
recipes
├── id (PRIMARY KEY)
├── title
├── description
├── file_path
├── language
├── category
├── difficulty
├── prep_time
├── cook_time
├── total_time
├── servings
└── created_at

ingredients
├── id (PRIMARY KEY)
├── recipe_id (FOREIGN KEY -> recipes.id)
├── category
└── ingredient

instructions
├── id (PRIMARY KEY)
├── recipe_id (FOREIGN KEY -> recipes.id)
├── phase
├── step_number
└── instruction

storage_tips, serving_suggestions, recipe_notes
├── id (PRIMARY KEY)
├── recipe_id (FOREIGN KEY -> recipes.id)
└── text
```

## Using the Database

If you want to use the recipe database in Python, you can do so with the following code:

```python
import sqlite3

# Connect to the database
conn = sqlite3.connect('docs/database/recipes.db')
cursor = conn.cursor()

# Query all recipes
cursor.execute("SELECT title, language, category, prep_time, cook_time FROM recipes")
recipes = cursor.fetchall()

# Print recipes
for recipe in recipes:
    print(f"Recipe: {recipe[0]} ({recipe[1]})")
    print(f"Category: {recipe[2]}")
    print(f"Prep time: {recipe[3]}, Cook time: {recipe[4]}")
    print("---")

# Close the connection
conn.close()
```

This database is automatically regenerated each time the documentation is built, ensuring it always stays in sync with the markdown recipe files.

## Recipe Categories

The following categories are used to classify recipes:
- Breakfast
- Starter
- Main
- Dessert
- Sides
