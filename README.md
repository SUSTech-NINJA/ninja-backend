# ninja-backend

This is the backend for the NINJA project.

## Usage

> [!NOTE]
> If you don't have `poetry` installed, you can install it by running `pip install poetry`.
> We recommend using [Apifox](https://apifox.com) to test the APIs.
> 
> Rust is required by dependencies. Install it from [official website](https://www.rust-lang.org/)

First, add a secret key and api key to the `.env` file

```
echo "SECRET=your_secret_key\n \
AIPROXY_API_KEY=your_api_key\n \
MAIL_USERNAME=your_email\n     \
MAIL_PASSWORD=your_password" > .env
```

Then, start a virtual environment and run the server

```bash
poetry shell
# you can choose alternatively to install on bare metal
poetry install 
flask run
```

Visit by [localhost:5000](http://localhost:5000/)


## Frameworks

- Poetry
- Flask
    - Flask-CORS
    - SQLAlchemy (SQLite)
    - dotenv
- JWT
- OpenAI


## License
MIT License
