import importlib
import inspect
import os
import sys

from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings
from starlette.routing import Mount


class App:
    def __init__(
        self,
        name=None,
        routes=None,
        middlewares=None,
    ):
        self.name = name or getattr(self, 'name', type(self).__name__)
        self.routes = routes or getattr(self, 'routes', [])
        self.middlewares = middlewares or getattr(self, 'middlewares', [])

    def get_middlewares(self, *extra):
        return self.middlewares + list(extra)

    def get_pattern(self):
        return getattr(self, 'pattern', self.name.lower())

    def get_mount(self):
        if self.routes or self.controllers or self.views:
            return Mount(
                '/' + self.get_pattern(),
                name=self.name,
                routes=self.get_routes()
            )

    def get_routes(self, *extra):
        return list(extra) + self.routes

    def setup(self):
        pass  # pragma: no cover

    def startup(self):
        pass  # pragma: no cover


class Project:
    @classmethod
    def current(cls):
        """Return the current project, from PROJECT env var if necessary."""
        if '_singleton' not in cls.__dict__:  # pragma: no cover
            parts = os.environ['PROJECT'].split('.')
            mod = importlib.import_module('.'.join(parts[:-1]))
            cls._singleton = getattr(mod, parts[-1])
            assert cls._singleton, f'Project {os.environ["PROJECT"]} not found'
        return cls._singleton

    def __init__(self, **settings):
        self.config = Config('.env', settings)
        self.project_setup()
        self.apps_setup()

    def project_setup(self):  # pragma: no cover
        """Setup the PROJECT env var."""
        Project._singleton = self
        self.project = self.config('PROJECT', default=None)
        if not self.project:
            frame = inspect.stack()[-1]
            filename = frame.filename.split('/')[-1]
            self.project_module = filename.replace('.py', '')
            self.project_variable = frame.code_context[0].split('=')[0].strip()
            self.project = ':'.join([
                self.project_module,
                self.project_variable,
            ])
        else:
            self.project_module, self.project_variable = self.project.split(':')  # noqa
        os.environ['PROJECT'] = self.project

    def apps_setup(self):
        self.apps = dict()

        apps = self.config('APPS', cast=CommaSeparatedStrings, default=[])
        for arg in apps:
            mod = importlib.import_module(arg)
            app = getattr(mod, 'app')
            if not getattr(app, 'name', None):
                app.name = arg.split('.')[-1]
            app.module = mod
            app.project = self
            self.apps[app.name] = app
            app.setup()

    @property
    def mode(self):
        if '_mode' not in self.__dict__:
            if '--reload' in sys.argv:  # pragma: no cover
                self._mode = 'dev'
            elif 'pytest' in sys.modules:
                self._mode = 'test'
            else:  # pragma: no cover
                self._mode = 'production'
        return self._mode

    def starlette(self, **kwargs):
        kwargs.setdefault('debug', self.mode in ('test', 'dev'))

        kwargs.setdefault('middleware', [])
        for app in self.apps.values():
            kwargs['middleware'] += app.get_middlewares()

        kwargs.setdefault('on_startup', [])
        kwargs['on_startup'].append(self.startup)

        kwargs.setdefault('routes', [])
        kwargs['routes'] += self.routes()

        return Starlette(**kwargs)

    def routes(self):
        routes = []
        for app in self.apps.values():
            mount = app.get_mount()
            if mount:
                routes.append(mount)
        return routes

    async def startup(self):  # pragma: no cover
        for app in self.app.values():
            await app.startup()
