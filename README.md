# IoC for configuration of Starlette projects

IoC stands for "Inversion of Control", it offers an alternate way to configure
Starlette projects, in the fashion of Django's INSTALLED_APPS, but following an
injection model such as CakePHP (since 2019) and Django-GDAPS.

## Install

Install with pip:

    pip install starlette-apps

## Purpose

The purpose is to split up imports and configurations from your starlette ASGI
declaration script as such:

```python
import apps

project = apps.Project(
    TIMEZONE='Europe/Paris',
    APPS=[
        'your_db_config',
        'your_app',
    ],
)

app = project.starlette()
```

Then, your apps can inject routes, middlewares, startup code, and also run
setup code at import time.

Initially, I made this for my own little framework experiment, and had a lot of
specific stuff in the Project class. After refactoring for a while, it turned
out all dependencies could be extracted out into apps. And then, it became
worth sharing. It's really not much code, but I think it would be nice if
somehow we could have an ecosystem of Starlette apps that are just pluggable.
This is a solution.

## Apps

### Instanciation

Instanciating a Project will basically get the `.app` attribute of each modulle
in `APPS`, which you may define for example as such:

```python
import apps

app = apps.App(
    name='YourApp',
    middlewares=[
        Middleware(YourMiddleware)
    ],
    routes=[
        Route('/pattern', YourView),
    ],
)
```

### Methods & Declarative

You may also define your App declaratively, for example if you want to override
some methods:

```python
class YourApp(apps.App):
    middlewares = [Middleware(YourMiddleware)]

    def get_routes(self):
        if self.project.mode == 'production':
            return your_production_routes
        elif self.project.mode in ('test', 'dev'):
            return your_production_routes + your_debug_routes

    def setup(self):
        """
        Do something as soon as your app is imported.
        Useful to setup things such as a database connection.
        """

    def startup(self):
        """
        This will be passed to starlette on_startup.
        Useful to run migrations for example.
        """
```

Note that Project will not just build a list of `get_routes()` results, instead
it will call `App.get_mount()` which in turn will return a `Mount` of the
result from `get_routes()`.

## Project & IoC Flow

### Project mode

A `project.mode` dynamic property returns `production` by default, but if the
`pytest` module is loaded it will return `test`, and if `--reload` is in
sys.argv it will return `dev`. You may override this to your taste, it may help
your apps decide what kind of configuration is best to inject.

### Instanciation of the project

This section describes the flow of the Project instanciation.

#### 1. Setting project.config

Then, the project will create a `self.config` instance of `starlette.Config`
with the settings that were passed in the constructor kwargs, and reading a
`.env` file that would be in the current working directory.

You can then get settings through something like `project.config("TIMEZONE")`.
Of course, this means that you need to have the project instance from outside
the module, which you can do as such:

#### 2. Setting Project.current()

```python
from apps import Project

project = Project.current()
```

This is because the first thing that instanciating the Project class is setting
a class attribute with itself. But this also works from subshells because it
writes the `PROJECT` environment variable, ie. if you instanciate the project,
run a shell command which invokes Python: `Project.current()` will still work.

#### 3. Apps setup

Finally, it will import every app module one by one, as it does so it will:

- get the ``app`` variable from the module,
- set ``app.name`` to the module name if ``app.name`` set, to ensure all apps
  have a name
- add the app to ``project.apps[app.name]``,
- set ``app.module`` to the module that it was imported from,
- set ``app.project`` to the project instance,
- call ``app.setup()``

So, if your first app is ``your_orm``, you can setup the database connection in
``your_orm.app.setup()`` and it will be available to all subsequent apps.

### Starlette generation

`project.starlette(**kwargs)` returns a Starlette instance a such:

- if `project.mode` is `test` or `dev`, then it will set `debug=True`,
- it will add the result of each app's `get_middlewares()` to the `middlewares`
  kwarg,
- it will add its `project.startup()` callback to the `on_startup` kwarg, which
  by default will execute each app's `startup()` method
- it will add the Mount object returned by each app's `get_mount()` method to
  the `routes` kwarg
