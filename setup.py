import setuptools


setuptools.setup(
    name="herokuify_scrapyd",
    version="1.0",
    author="Ahmed Rafik Djerah",
    author_email="djerahahmedrafik@mail.com",
    description="A package to deploy scrapy spiders to Heroku",
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    install_requires=[
        'scrapyd'
    ],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
