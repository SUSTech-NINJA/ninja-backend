# ninja-backend

This is the backend for the NINJA project.

## Usage

> [!NOTE]
> If you don't have `poetry` installed, you can install it by running `pip install poetry`.

First, add a secret key to the `.env` file

```
echo "SECRET=your_secret_key" > .env
```

Then, start a virtual environment and run the server

```bash
poetry shell
flask run
```

Visit by `http://localhost:5000/`

## Frameworks
- Flask

## License
MIT License
