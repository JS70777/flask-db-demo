from flask import Flask, request, jsonify, render_template, redirect, url_for
from google.cloud import datastore

app = Flask(__name__)
datastore_client = datastore.Client()

@app.route('/', methods=['GET'])
def home():
    """Display homepage with form and list of items"""
    # Query all items
    query = datastore_client.query(kind='Item')
    items = []
    for entity in query.fetch():
        item = dict(entity)
        item['id'] = entity.key.id
        items.append(item)
    return render_template('home.html', items=items)


@app.route('/create', methods=['POST'])
def create():
    """Handle form submission to create new item"""
    try:
        name = request.form.get('name')
        description = request.form.get('description')

        # Create new entity
        key = datastore_client.key('Item')
        entity = datastore.Entity(key=key)
        entity.update({
            'name': name,
            'description': description
        })
        datastore_client.put(entity)

        return redirect(url_for('home'))
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/view/<int:item_id>')
def view_item(item_id):
    """Display individual item page"""
    key = datastore_client.key('Item', item_id)
    entity = datastore_client.get(key)

    if not entity:
        return "Item not found", 404

    item = dict(entity)
    item['id'] = entity.key.id
    return render_template('view_item.html', item=item)

if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)