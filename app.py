from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime, timedelta
from extract import extractor
from timeloop import Timeloop
import os

tl = Timeloop()

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Init DB
db = SQLAlchemy(app)

# Init MA
ma = Marshmallow(app)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    body = db.Column(db.String())
    link = db.Column(db.String())
    create_date = db.Column(db.DateTime())


class ArticleSchema(ma.Schema):
    class Meta:
        fields = ('id', 'title', 'body', 'link', 'create_date')


# Init Schema
article_schema = ArticleSchema()
articles_schema = ArticleSchema(many=True)

# Create database if not already created
if not os.path.isfile('db.sqlite'):
    print("First run. Creating DB...")
    db.create_all()
else:
    print('DB exists. Skipping Create...')


@app.route('/article', methods=['POST'])
def add_article(article=None):
    if not article:
        title = request.json['title']
        body = request.json['body']
        link = request.json['link']
    else:
        title = article.get('title', '')
        body = article.get('body', '')
        link = article.get('link', '')

    create_date = datetime.now()

    new_article = Article(title=title, body=body, link=link, create_date=create_date)
    db.session.add(new_article)
    db.session.commit()
    return article_schema.jsonify(new_article)


@app.route('/article', methods=['GET'])
def get_all_articles_in_daterange():
    day_range = request.args.get('range') or 1
    filter_timerange = datetime.today() - timedelta(days=int(day_range))
    all_articles = Article.query.filter(Article.create_date >= filter_timerange).all()
    result = articles_schema.dump(all_articles)
    return jsonify(result)


@app.route('/article/<id>', methods=['GET'])
def get_article(id):
    article = Article.query.get(id)
    return article_schema.jsonify(article)


@app.route('/article/<id>', methods=['PUT'])
def update_article(id):
    article = Article.query.get(id)

    title = request.json['title']
    body = request.json['body']
    link = request.json['link']
    create_date = datetime.now()

    article.title = title
    article.body = body
    article.link = link
    article.create_date = create_date

    db.session.commit()
    return article_schema.jsonify(article)


@app.route('/article/<id>', methods=['DELETE'])
def delete_article(id):
    article = Article.query.get(id)
    db.session.delete(article)
    db.session.commit()
    return article_schema.jsonify(article)

@app.route('/run', methods=['GET'])
def start_scheduler():
    tl.start(block=True)

@app.route('/stop', methods=['GET'])
def stop_scheduler():
    tl.stop()


@tl.job(interval=timedelta(minutes=10))
def run_extractor():
    print('running extractor: {}'.format(str(datetime.now())))
    articles = extractor()
    for article in articles:
        add_article(article)
    return app.response_class(
        response="extractor run",
        status=200,
        mimetype='application/json'
    )


# Run server
if __name__ == '__main__':
    app.run(debug=True)