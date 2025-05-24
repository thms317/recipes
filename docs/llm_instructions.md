# Recipe Reformatting Guide

## Goal

Convert raw recipe text into structured Markdown while preserving the original language and information.

## Output Format

```markdown
# Recipe Title

> *Brief description*

## Recipe Information

- **Prep Time:** X minutes
- **Cook Time:** X minutes
- **Rest Time:** X minutes
- **Total Time:** X minutes
- **Servings:** X servings
- **Course:** starter, main, dessert, side
- **Difficulty:** simple, medium, complex
- **Language:** EN / NL

## Ingredients

### Main Ingredients

- Ingredient 1
- Ingredient 2

## Instructions

1. First step
2. Second step

## Recipe Notes

- Note 1
- Note 2
```

## Conversion Steps

1. **Title & Description**
   - Convert recipe name to H1 heading (`# Title`)
   - Format description in italics below title, led by a `>`

2. **Recipe Information**
   - Format as bulleted list with bold categories
   - Include timing, servings, and other key details from original
   - Add category and difficulty if present in original
   - If category is not present, om

3. **Ingredients**
   - Use H2 heading (`## Ingredients`)
   - Group into categories with H3 headings if present in original
   - Use "Main Ingredients" if no categories exist
   - Format as bulleted list

4. **Instructions**
   - Use H2 heading (`## Instructions`)
   - Only use H3 subcategories if recipe has multiple distinct phases
   - Format as numbered list
   - Preserve exact wording of each step as much as possible

5. **Notes**
   - Include only if present in original
   - Format as bulleted list

6. **Final Check**
   - Correct obvious spelling errors
   - Verify formatting (## for sections, ### for subsections)
   - Ensure no information was invented or omitted

## Key Principles

- Preserve original language - never translate
- Don't invent missing information
- Maintain original measurements and terminology
- Fix obvious typos but preserve technical terms
- Use proper Markdown headings (# for title, ## for sections, ### for subsections)
