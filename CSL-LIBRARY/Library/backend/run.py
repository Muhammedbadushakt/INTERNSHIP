from app.__init__ import create_app
from flask_cors import CORS

app = create_app()

CORS(app, origins=["http://10.110.1.88"])

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)