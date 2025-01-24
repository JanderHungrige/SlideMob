# SlideMob

SlideMob interacts with your PPT files and performes actions such as translating without affecting the layout.

> Below you will find *Markdown* citations containing comments and suggestions on how to extend and adapt this `README.md` file. The idea is that you replace them with appropriate content. The remaining regular content outside the citation blocks hopefully is a useful starting point.


**Table of Contents**

[[_TOC_]]


## Installation

> Provide instructions on how to install or get started using the released software that results from this repository. Note that this is *not* a section on how to get started *developing* this package, library or application - such content is part of the [Getting Started](#getting-started) section in [Contributing and Development](#contributing-and-development) further down below.

## Usage

> Use examples liberally, and show the expected output if you can. It's helpful to have inline the smallest example of usage that you can demonstrate, while providing links to more sophisticated examples if they are too long to reasonably include in the `README.md`.


## Support

> Tell people where they can go to for help. It can be any combination of an issue tracker, a chat room, an email address, etc.


## Contributing and Development

> State if you are open to contributions and what your requirements are for accepting them.
>
> For people who want to make changes to your project, it's helpful to have some documentation on how to get started. Perhaps there is a script that they should run or some environment variables that they need to set. Make these steps explicit. These instructions could also be useful to your future self.
>
> You can also document commands to lint the code or run tests. These steps help to ensure high code quality and reduce the likelihood that the changes inadvertently break something. Having instructions for running tests is especially helpful if it requires external setup, such as starting a *Selenium* server for testing in a browser.


### Getting Started

[*Poetry*](https://python-poetry.org) is used as package/dependency manager as well as for handling the virtual environment into which the dependencies are installed.

Install tkinter via brew (restart maybe required)

    brew install python-tk

Install [LM Studio](https://lmstudio.ai/) via their website and the CLI via terminal

    npx lmstudio install-cli

After you have installed a model of your choice, you can start the server and load the model

    lms server start
    lms load

Enter the repository's root folder

    cd slidemob/

Create the virtual environment and install the dependencies - including the optional dependencies for development and testing - by using [*Poetry*](https://python-poetry.org/docs/basic-usage/) (make sure to be on a more recent version, there were some errors with poetry < 2):

    poetry install

Activate the virtual environment with

    poetry shell

Initialize a [*Git*](https://git-scm.com/) repository - e.g. by running

    git init -b develop

which will also create and switch to a new branch called `develop` - and connect it to the corresponding empty repository in the hosted *Git* provider you are using, such as *Bitbucket*, *GitHub*, or *GitLab*.

Install the configured [*pre-commit*](https://pre-commit.com/) hooks with

    pre-commit install

If you're using an IDE, please make sure to set your virtual environment as project interpreter.

Verify your installation by running the [*pytest*](https://pre-commit.com/) test suite:

    pytest

Done - happy coding!


### Unit and Integration Tests

All available tests be run in their entirety with
```bash
pytest
```
or separately according to their type with
```bash
pytest tests/unit/
pytest tests/integration/
```

Splitting the tests by their type not only allows running them separately, but also e.g. creating dedicated coverage reports for each type of test - as done in `scripts/coverage.sh` - all without having to fall back on *pytest* markers.

Since at this moment there are no pre-configured integration tests included, the running of integration tests is commented out in `scripts/coverage.sh`. Once you add them, please comment in this line again to activate dedicated coverage reporting for the integration tests as well.

> Depending on your needs and the requirements on this project, you may want to consider adding further test suites, such as functional tests or suites of example / tutorial *Jupyter* notebooks.


### Jupyter Notebooks

It is very strongly recommended to only commit *Jupyter* notebooks that were converted to their equivalent `.py` *Python* files. To this end, [*Jupytext*](https://jupytext.readthedocs.io/en/latest/) is already installed for you and `.ipynb` files are vetoed through the `.gitignore` file.

Currently, there is only one example Jupyter notebook included in this repository, `tutorials/1-example-notebook.py`, which showcases how Jupyter notebooks can be included in the documentation. See the [*Documentation*](#documentation) section for instructions on how to create the documentation.

Use [*Jupytext*](https://jupytext.readthedocs.io/en/latest/) to convert the `.py` notebook equivalents to their corresponding `.ipynb` Jupyter notebooks:
```bash
jupytext --sync tutorials/*.py
```

`ipynb` and `py:percent` are set as the default formats in the `[tool.jupytext]` section of the `pyproject.toml`.

When first opening an `.ipynb` file, you will need to specify the kernel - which can be figured out as the last component, i.e. folder, of the path to the virtual environment created by *Poetry*:
```bash
poetry env info -p
```


### Documentation

This project is documented with [*Material for MkDocs*](https://squidfunk.github.io/mkdocs-material/), a popular theme built on top of [*MkDocs*](https://www.mkdocs.org/), and features

- an automatically generated recursive source code / API reference built with [*mkdocstrings*](https://mkdocstrings.github.io/), [*mkdocs-gen-files*](https://oprypin.github.io/mkdocs-gen-files/index.html) and [*mkdocs-literate-nav*](https://oprypin.github.io/mkdocs-literate-nav/reference.html)
- rendering of Jupyter notebooks with [*mkdocs-jupyter*](https://github.com/danielfrg/mkdocs-jupyter)
- coverage reports generated with [*pytest-cov*](https://pytest-cov.readthedocs.io/en/latest/) and included with [*mkdocs-coverage*](https://pawamoy.github.io/mkdocs-coverage/)
- [GDPR compliance](https://squidfunk.github.io/mkdocs-material/plugins/privacy/) and support for [offline browsing](https://squidfunk.github.io/mkdocs-material/plugins/offline/)

To build the documentation, please run
```bash
tox
```
or
```bash
tox -e docs
```
This will do three things:

- [*tox*](https://tox.wiki) will invoke `scripts/coverage.sh` which will in turn run `pytest --cov` to generate the coverage report in HTML form and store it in `.coverage-unit-html/`. From there, it is included in the [Development](coverage-unit.md) section of this documentation.
- [*tox*](https://tox.wiki) will use *jupytext* to execute the example notebook `tutorials/1-example-notebook.py` and save the resulting `.ipynb` - including the outputs - into the `docs/tutorials/` folder, from where it is included into the documentation.
- Finally, [*tox*](https://tox.wiki) will trigger a local build of the documentation into the `site/` folder. The landing page will be located at `site/index.html`.

During development, you can also locally serve the documentation from the repository root folder with:
```bash
mkdocs serve
```
This can be convenient during development because in this project, *MkDocs* is configured such that it will watch for changes in the `docs/` and `src/` folders as well as the `README.md` and `CHANGELOG.md` files and will automatically rebuild the documentation when modifications are detected.

Note that while *MkDocs* can be configured so as to execute any included *Jupyter* notebooks when serving or building the documentation - and also to trigger this automatically by watching the `tutorials/` folder - the conscious decision was made *not* to do this. The reason is that the automatic rebuilding always reruns all *Jupyter* notebooks - even if they haven't changed. Therefore, the notebooks are only executed manually on demand through *tox* as described above.


## Authors and Acknowledgments

Jan Werth


> ## Possible Additions
>
> You can have a look at [*Make a README*](https://www.makeareadme.com/) for further suggestions on what to include in this `README.md`. Feel free to add any of these - or additional other sections, of course - above if, when and where appropriate.
>
> ### Badges
> At the top of some `README.md`s, you may see small images that convey metadata, such as whether or not all the tests are passing for the project. There are many providers - [*Shields.io*](https://shields.io/) is just one example. If you are interested in using badges, please check which badges are provided and supported by the [*Git*](https://git-scm.com/) hosting provider you are using before adding them to your `README.md`. Many services also have instructions for adding a badge.
>
> ### Visuals
> Depending on what you are making, it can be a good idea to include screenshots or even a video (you'll frequently see GIFs rather than actual videos). Tools like [*ttygif*](https://github.com/icholy/ttygif) can help, but check out [*Asciinema*](https://asciinema.org/) for a more sophisticated method.
>
> ### Roadmap
> If you have ideas for releases in the future, it is a good idea to track them in the relevant Git hosting provider or issue tracker, such as *Bitbucket*, *GitLab*, *GitHub*, or at least list them in a `TODO.md`. You can refer
>
> ### License
> For open source projects, say how it is licensed.
>
> ### Project status
> If you have run out of energy or time for your project, put a note at the top of the `README.md` saying that development has slowed down or stopped completely. Someone may choose to fork your project or volunteer to step in as a maintainer or owner, allowing your project to keep going. You can also make an explicit request for maintainers.
