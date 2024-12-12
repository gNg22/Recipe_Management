# Recipe Management System API

## Getting Started

### Installation

1. Clone the project repository using `git clone`.
2. Install the required dependencies by running `pip install -r requirements.txt` in your terminal.

### Project Setup

1. Open the `settings.py` file and comment out the `REST_FRAMEWORK` dictionary.
2. Create a new user using the `Create User` API. You can pass a `role` field with the value `creator` if you want the user to have creator privileges. If not, the user will be assigned the `viewer` role by default. This API will also provide an access token.

### API Usage

1. To use other APIs, uncomment the `REST_FRAMEWORK` dictionary in the `settings.py` file.
2. Pass the access token obtained in step 2 as a Bearer token in the `Authorization` field of the API request.

## Note

This project is currently in the development phase. The master branch has been pushed, and updates will be made soon.

## API Endpoints

- **Create User:** `POST /users/`
- **Recipe List:** `GET /recipes/`
- **Recipe Create:** `POST /recipes/`
- **Recipe Detail:** `GET /recipes/{id}/`
- **Recipe Update:** `PUT /recipes/{id}/`
- **Recipe Delete:** `DELETE /recipes/{id}/`
- **Bulk Upload:** `POST /recipes/bulk-upload/`
- **Favorite Recipe:** `POST /recipes/{id}/favorite/`
- **Download Recipe Card:** `GET /recipes/{id}/download/`
- **Ingredients List:** `GET /ingredients/`
- **Ingredient Recipes:** `GET /ingredients/{id}/recipes/`
- **Recipe Category Durations:** `GET /recipes/category-durations/`

## API Collection

API Collection will be added soon.

