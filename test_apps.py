from apps import App, Project
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse


testroute = Route('/', lambda *a: PlainTextResponse())


class TestMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        return await self.app(scope, receive, send)


class ExampleApp(App):
    routes = [testroute]
    middlewares = [Middleware(TestMiddleware)]
    was_setup = False

    def setup(self):
        self.was_setup = True


app = ExampleApp()


def test_declarative():
    assert app.name == 'ExampleApp'
    assert app.get_routes() == [testroute]

    middlewares = app.get_middlewares()
    assert len(middlewares) == 1
    assert middlewares[0].cls == TestMiddleware

    assert app.get_mount() == Mount(
        '/exampleapp',
        name='ExampleApp',
        routes=[testroute],
    )


def test_project():
    assert not ExampleApp.was_setup

    project = Project(APPS=['test_apps'])

    global app
    assert project.apps['ExampleApp'] == app
    assert app.was_setup

    starlette = project.starlette()

    assert len(starlette.routes) == 1
    assert starlette.routes[0] == Mount(
        '/exampleapp',
        name='ExampleApp',
        routes=[testroute],
    )

    assert len(starlette.user_middleware) == 1
    assert starlette.user_middleware[0].cls == TestMiddleware

    assert project.mode == 'test'
    assert Project.current() == project
