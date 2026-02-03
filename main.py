from flask import Flask, request, jsonify, render_template, redirect, url_for
from google.cloud import datastore

app = Flask(__name__)
datastore_client = datastore.Client()

@app.route('/', methods=['GET'])
def home():
    """Display homepage with form and list of quotes"""
    # Query all quotes
    query = datastore_client.query(kind='Quote')
    quotes = []
    for entity in query.fetch():
        quote = dict(entity)
        quote['id'] = entity.key.id
        quotes.append(quote)
    return render_template('home.html', quotes=quotes)


@app.route('/create', methods=['POST'])
def create():
    """Handle form submission to create new quote"""
    try:
        name = request.form.get('name')
        quote = request.form.get('quote')
        submitter = request.form.get('submitter')

        # Create new entity
        key = datastore_client.key('Quote')
        entity = datastore.Entity(key=key)
        entity.update({
            'name': name,
            'quote': quote,
            'submitter': submitter
        })
        datastore_client.put(entity)

        return redirect(url_for('home'))
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/view/<int:quote_id>')
def view_quote(quote_id):
    """Display individual quote page"""
    key = datastore_client.key('Quote', quote_id)
    entity = datastore_client.get(key)

    if not entity:
        return "Quote not found", 404

    quote = dict(entity)
    quote['id'] = entity.key.id
    return render_template('view_quote.html', quote=quote)

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)