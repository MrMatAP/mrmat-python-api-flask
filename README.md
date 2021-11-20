# MrMat :: Python :: API :: Flask

Boilerplate code for a Python Flask API

[![Build](https://github.com/MrMatOrg/mrmat-python-api-flask/actions/workflows/build.yml/badge.svg)](https://github.com/MrMatOrg/mrmat-python-api-flask/actions/workflows/build.yml)

This variant of a Python Flask API is code-first and using native Flask
 
## Features

* Code-first
* Pluggable APIs and multiple API versions
* Database schema migration using Flask-Migrate
* API body serialisation using Flask-Marshmallow
* OIDC Authentication using Flask-OIDC
* No TLS, because this is intended to run behind a reverse proxy
* Healthz API

## How to build this

In bash:

```shell
$ pip install -r requirements.txt  # Manually install dependencies (see note in requirements.txt!)
$ export PYTHONPATH=`pwd`                # In order to find the build-time ci module
$ export MRMAT_VERSION=1.0.27            # Optional: To influence the version. Normally calculated and set by CI
$ python -m build -n                     # Use -n in an interactive, virtual environment
$ ls dist/
mrmat_python_api_flask-1.0.27.dev0-py3-none-any.whl
```

In PowerShell:

```powershell
PS> pip install -r build-requirements.txt     # Manually install dependencies (see note in requirements.txt!)
PS> $Env:PYTHONPATH=(pwd)                     # In order to find the build-time ci module
PS> $Env:MRMAT_VERSION = "1.0.27"             # Optional: To influence the version. Normally calculated and set by CI
PS> python -m build
```

## How to run this

You have the choice of running this 

* as a CLI app
* as a WSGI app 
* as a container image. 

### To run as a CLI app

To run this directly:

```shell
$ mrmat-python-api-flask -h
usage: mrmat-python-api-flask [-h] [-d] [--host HOST] [--port PORT] [--instance-path INSTANCE_PATH] [--db DB]
                              --oidc-secrets OIDC_SECRETS

mrmat-python-api-flask - 0.0.2

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           Debug
  --host HOST           Host interface to bind to
  --port PORT           Port to bind to
  --instance-path INSTANCE_PATH
                        Fully qualified path to instance directory
  --db DB               Database URI
  --oidc-secrets OIDC_SECRETS
                        Path to file containing OIDC registration
```

```shell
$ mrmat-python-api-flask 
[2021-06-06 15:30:18,005] INFO: Using instance path at /opt/dyn/python/mrmat-python-api-flask/var/mrmat_python_api_flask-instance
[2021-06-06 15:30:18,005] WARNING: Running without any authentication/authorisation
 * Serving Flask app "mrmat_python_api_flask" (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
INFO  [werkzeug]  * Running on http://localhost:8080/ (Press CTRL+C to quit)

<Ctrl-C>
```

The instance directory defaults to `var/instance/` but you can override that to be a fully qualified path via the 
`--instance-path` option. Any database supported by SQLAlchemy can be provided by the `--db` option. The database is 
a SQLite database within the instance directory by default.

### To run as a WSGI app

To run as a WSGI app, execute the following. When running as a WSGI app, the database is not created and migrated
on its own.

```
$ flask db upgrade
$ gunicorn --workers 2 'mrmat_python_api_flask:create_app()'
```
### To run as a container

To run as a container, first build that container:

```
$ python ./setup.py sdist
$ docker build -t mrmat-python-api-flask:0.0.1 -f var/docker/Dockerfile .
...
$ docker run --rm mrmat-python-api-flask:0.0.1
```

>You may be tempted by Alpine, but most of the Python wheels do not work for it. Go for slim-buster instead

## How to use this

Once started, you can curl towards the APIs mounted at various places. See the invocations of `app.register_blueprint`
within `mrmat_python_api_flask/__.init__.py` to find out where. 

>Note that omitting the last slash will cause a redirect that you can follow using curls -L option. We can probably
>get rid of that by using a more clever versioning scheme that doesn't make the root resource listen on / (e.g. `/greeting`).

## How to test this

Unit tests are within the `tests` directory. You can use the built-in Pycharm test configuration or do it on the CLI.

```
$ python ./setup.py install
$ python -m flake8
$ python -m pytest
```

Tests for authenticated APIs will be skipped until the testsuite is configured with OIDC secrets.

## Clients

A client for the (currently) the authenticated Greeting API v3 is installed along with the API server. 

```shell
$ mrmat-python-api-flask-client -h
usage: mrmat-python-api-flask-client [-h] [-q] [-d] [--config CONFIG] [--client-id CLIENT_ID] [--client-secret CLIENT_SECRET] [--discovery-url DISCOVERY_URL]

mrmat-python-api-flask-client - 0.0.2

optional arguments:
  -h, --help            show this help message and exit
  -q, --quiet           Silent Operation
  -d, --debug           Debug

File Configuration:
  Configure the client via a config file

  --config CONFIG, -c CONFIG
                        Path to the configuration file for the flask client

Manual Configuration:
  Configure the client manually

  --client-id CLIENT_ID
                        The client_id of this CLI itself (not yours!)
  --client-secret CLIENT_SECRET
                        The client_secret of the CLI itself. Not required for AAD, required for Keycloak
  --discovery-url DISCOVERY_URL
                        Discovery of endpoints in the authentication platform
```

>The client requires configuration with OIDC secrets and currently implements the Device code flow

## Configuration

You can provide configuration by pointing to a JSON file via the FLASK_CONFIG environment variable. The file is expected
to be in the following format:

```json
{
  "web": {
    "client_id":                OIDC client_id of the API server itself
    "client_secret":            OIDC client_secret of the API server itself
    "auth_uri":                 OIDC Authorization endpoint
    "token_uri":                OIDC Token endpoint
    "userinfo_uri":             OIDC UserInfo endpoint
    "redirect_uris":            OIDC redirect URI 
    "issuer":                   OIDC Issuer
    "token_introspection_uri":  OIDC Introspection URI
  },
  "OIDC_CLIENT_SECRETS":        Can be an external file
}
```

You can externalise `web` into a separate file which you may generate via [Flask-OIDCs oidc-register](https://flask-oidc.readthedocs.io/en/latest/).
If you wish to save yourself an external file, `OIDC_CLIENT_SECRETS` should point to the same file it is declared in
(i.e. the same file that FLASK_CONFIG points to) but `web` must be the first entry due to some unfortunate assumptions
made in Flask-OIDC.

The same or a separate configuration file can be used to configure the testsuite so it includes auth/z/n tests. An 
additional dictionary is required to configure the client side:

```json
{
  "web": {
    "client_id":                OIDC client_id of the API server itself
    "client_secret":            OIDC client_secret of the API server itself
    "auth_uri":                 OIDC Authorization endpoint
    "token_uri":                OIDC Token endpoint
    "userinfo_uri":             OIDC UserInfo endpoint
    "redirect_uris":            OIDC redirect URI 
    "issuer":                   OIDC Issuer
    "token_introspection_uri":  OIDC Introspection URI
  },
  "client": {
    "client_id":                OIDC client_id for the API test client
    "client_secret":            OIDC client_secret for the API test client
    "preferred_name":           OIDC expected name to test for. The test looks for the preferred_name assertion, which
                                may not match the client_id.
  },
  "OIDC_CLIENT_SECRETS":        Can be an external file
}
```

The client may also be configured via a configuration file, which should have the following format:

```json
{
  "client_id":                  OIDC client_id of the client script (not whoever ultimately authenticates)
  "client_secret":              OIDC client_secret of the client script (not whoever ultimately authenticates)
                                This is required when using Keycloak, which is unfortunate because for instance,
                                Microsofts AAD doesn't need it and it would make the client app far more distributable
  "discovery_url":              OIDC discovery URL
}
```

## OIDC

The API has currently been tested with [Keycloak](https://www.keycloak.org). If your Keycloak instance is behind a
self-signed CA then you must point the `HTTPLIB2_CA_CERTS` environment variable to that CA certificate before executing
either the client or the server, otherwise the validation of the tokens will fail in mysterious ways. Only a stack trace
will tell you that communication with the introspection endpoint failed due to missing CA trust.

Configure the following clients as needed:

### API Server

* Suggested client_id: mrmat-python-api-flask
* Access Type: confidential
* Flow: Authorization Code Flow (Keycloak: "Standard Flow")

### API Client

* Suggested client_id: mrmat-python-api-flask-client
* Access Type: confidential (but if it wasn't Keycloak, should be public)
* Flow: Device Authorization Grant

Keycloak's default polling interval during the device authorization flow is set to a rather long 600s. I strongly
suggest reducing that to 5s in the realm settings.

### Test Client

* Suggested client_id: mrmat-python-api-flask-test
* Access Type: confidential
* Flow: Client Credentials Grant (Keycloak: "Service Accounts Enabled")

### Scopes

The resource API uses two scopes that need to be defined within the IDP:

* mrmat-python-api-flask-resource-write - Permit create/modify/remove of resources
* mrmat-python-api-flask-resource-read  - Permit reading resources
