from setuptools import setup


setup(
    name='starlette-apps',
    versioning='dev',
    setup_requires='setupmeta',
    py_modules=['apps'],
    author='James Pic',
    author_email='jamespic@gmail.com',
    url='https://yourlabs.io/oss/starlette-apps',
    include_package_data=True,
    license='MIT',
    keywords='django cli',
    python_requires='>=3',
    install_requires=['starlette'],
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'itsdangerous',
        ],
    },
)
