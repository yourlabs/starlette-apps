# IoC for configuration of Starlette projects

IoC stands for "Inversion of Control", it offers an alternate way to configure
Starlette projects, in the fashion of Django's INSTALLED_APPS.

## Install

Install with pip:

    pip install starlette-apps

## Purpose

The purpose is to split up imports and configurations from your starlette ASGI declaration script as such:

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

## IoC Flow

Instanciating a Project will basically get the `.app` attribute of each modulle
in `APPS`, which you may define for example as such:

```python
    import apps

    app = apps.App(
        name='Some app',
        middlewares=[
            Middleware(YourMiddleware)
        ],
        routes=[
            Route('/pattern', YourView),
        ],
    )
```

## App

You may also define your App declaratively, for example if you want to override
some methods:

```python
class YourApp(apps.App):
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
