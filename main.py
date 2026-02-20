import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from google.cloud import datastore

app = Flask(__name__)
datastore_client = datastore.Client()

@app.route('/', methods=['GET'])
def home():
    """Display homepage with form and list of quotes"""
    # Query all quotes
    query = datastore_client.query(kind='Quote')
    query.order = ["-timestamp"]
    quotes = []
    for entity in query.fetch():
        quote = dict(entity)
        quote['id'] = entity.key.id
        quotes.append(quote)
    return render_template('home.html')

@app.route('/create', methods=['POST'])
def create():
    """Handle form submission to create new quote"""
    try:
        name = request.form.get('name').title()
        quote = request.form.get('quote')
        submitter = request.form.get('submitter')
        timestamp = datetime.datetime.now()

        # Create new entity
        key = datastore_client.key('Quote')
        entity = datastore.Entity(key=key)
        entity.update({
            'name': name,
            'quote': quote,
            'submitter': submitter,
            'timestamp': timestamp,
            'likes': 0
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
        return render_template('error_404.html', item='Quote')
    quote = dict(entity)
    quote['id'] = entity.key.id
    return render_template('view_quote.html', quote=quote)

@app.route('/Deal->eat/<int:quote_id>')
def delete_quote(quote_id):
    """Delete quote"""
    key = datastore_client.key('Quote', quote_id)
    entity = datastore_client.get(key)
    if not entity:
        return render_template('error_404.html', item='Quote')
    datastore_client.delete(entity)
    return redirect(url_for('home'))

@app.route('/view-person/<string:person>')
def view_type(person):
    person = person.title()

    by_quotes = datastore_client.query(kind='Quote')
    by_quotes.order = ["-timestamp"]

    by_quotes.add_filter(filter=datastore.query.PropertyFilter("name", "=", person))
    by_quotes_list = list(by_quotes.fetch())

    from_quotes = datastore_client.query(kind='Quote')
    from_quotes.add_filter(filter=datastore.query.PropertyFilter("submitter", "=", person))
    from_quotes_list = list(from_quotes.fetch())

    if len(by_quotes_list) == 0 and len(from_quotes_list) == 0:
        return render_template('error_404.html', item='Person')

    return render_template('view_by.html', person=person,
                           by_quotes=by_quotes_list, from_quotes=from_quotes_list)

@app.route('/quotes')
def quotes():
    filter = request.args.get('filter')
    args = ['timestamp', 'name', 'submitter', 'likes']
    if filter is None or (not args.__contains__(filter) and not args.__contains__(filter[1:])):
        filter = '-timestamp'

    qs = datastore_client.query(kind='Quote')
    qs.order = [filter]
    qs = list(qs.fetch())

    return render_template('quote_list.html', quotes=qs, filter=filter)

@app.route('/like/<int:quote_id>')
def like(quote_id):
    # 1. Create a key for the existing entity
    key = datastore_client.key('Quote', quote_id)
    # 2. Use a transaction for safe updating
    with datastore_client.transaction():
        # Fetch the current entity
        quote = datastore_client.get(key)
        if not quote:
            return render_template('error_404.html', item='Quote')
        # 3. Modify specific properties from form or JSON data
        quote['likes'] += 1
        # 4. Save the modified entity back to Datastore
        datastore_client.put(quote)
    return redirect(url_for('view_quote', quote_id=quote_id))

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)