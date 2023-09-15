from src.handlers import app

if __name__ == '__main__':
    app.run(server='gunicorn')
