from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import datetime, timedelta
from extract import extractor, retriever
import threading
import os

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

def run_extractor():
    print('running extractor: {}'.format(str(datetime.now())))
    new_articles = []
    links = extractor()
    for link in links:
        if not db.session.query(Article.id).filter_by(link=link).count():
            # print('new article: {}'.format(link))
            new_articles.append(link)

    retrieved = retriever(new_articles)

    for article in retrieved:
        if not db.session.query(Article.id).filter_by(title=article.get('title')).count():
            print('Adding to database: {}'.format(article.get('title')))
            with app.app_context():
                add_article(article)

    print("Finished....Cron waiting...{}".format(str(datetime.now())))
    # cron -> 30min
    threading.Timer(30*60, run_extractor).start()

# Run server
if __name__ == '__main__':
    threading.Timer(3, run_extractor).start()
    app.run(debug=False, host='0.0.0.0')
