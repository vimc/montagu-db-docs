#!/usr/bin/env python3
import docker
import json
import os
import sys
from datetime import datetime
import dateutil.parser

def datetime_format(x):
    return x.strftime('%Y-%m-%d %H:%M:%S')

def build_schemaspy():
    client = docker.from_env()
    img = client.images.build(path = 'docker', tag = 'schemaspy')
    return img.tags[0]

def generate_docs(db_sha):
    registry = 'docker.montagu.dide.ic.ac.uk:5000'
    db_image_name = '{registry}/montagu-db:{db_sha}'.format(
        db_sha = db_sha, registry = registry)
    migrate_image_name = '{registry}/montagu-migrate:{db_sha}'.format(
        db_sha = db_sha, registry = registry)

    nw_name = 'migration_test'
    db_name = 'db'
    client = docker.from_env()
    command = '-host {db} -db montagu -u vimc '.format(db = db_name) + \
              '-p changeme -s public -o /output'
    dest = 'docs/' + db_sha
    volumes = {os.path.abspath(dest): {'bind': '/output', 'mode': 'rw'}}
    uid = os.geteuid()
    schemaspy = build_schemaspy()
    if os.path.exists(dest):
        if os.path.exists(dest + '/index.html'):
            print("Already created docs for ", db_sha)
            return False
    else:
        os.makedirs(dest)

    nw = db = None
    try:
        print("generating documentation for " + db_sha)
        nw = client.networks.create(nw_name)
        db = client.containers.run(db_image_name,
                                   network = nw.name,
                                   detach = True,
                                   name = 'db')
        date_image = dateutil.parser.parse(db.image.attrs['Created'])
        print("performing migrations")
        client.containers.run(migrate_image_name, network = nw.name,
                              remove = True)
        print("documenting schema")
        client.containers.run(schemaspy,
                              command,
                              remove = True,
                              network = nw_name,
                              volumes = volumes,
                              user = uid,
                              stdout = True)
        add_run(db_sha,
                datetime_format(date_image),
                datetime_format(datetime.now()))
    finally:
        if db:
            db.stop(timeout = 1)
            db.remove()
        if nw:
            nw.remove()

    return True

def add_run(sha, date_image, date_docs):
    if os.path.exists('index.json'):
        with open('index.json', 'r') as f:
            dat = json.load(f)
    else:
        dat = []
    dat.append({'sha': sha, 'date_image': date_image, 'date_docs': date_docs})
    with open('index.json', 'w') as f:
        json.dump(dat, f)

def generate_index():
    print("updating index")
    with open('index.json', 'r') as f:
        dat = json.load(f)
    with open('index.html.template', 'r') as f:
        template = f.read()
    fmt = '<li><a href = docs/{sha}/index.html>{sha}</a> ' + \
          '({date_image}, generated {date_docs})</li>'

    data = max(dat, key = lambda x: x['date_image'])
    data['versions'] = '\n'.join([fmt.format(**i) for i in dat])
    index = template.format(**data)
    with open('index.html', 'w') as f:
        f.write(index)

def generate(db_sha):
    if generate_docs(db_sha):
        generate_index()

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) != 1:
        raise Exception("Expected exactly one argument")
    generate(args[0])
