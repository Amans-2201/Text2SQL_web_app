from setuptools import setup, find_packages

setup(
    name="text2sql-app",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "mysql-connector-python",
        "psycopg2-binary",
        "python-dotenv",
        "pydantic"
    ],
    entry_points={
        'console_scripts': [
            'text2sql=launcher:main',
        ],
    },
)
