# from App import app
from flask import Flask, Blueprint
import views   


app = Flask(__name__)
for obj in vars(views).values():
        if isinstance(obj, Blueprint):
            app.register_blueprint(obj, url_prefix='/')



if __name__ == "__main__":
    app.run(host='localhost', port=5050, debug=True)