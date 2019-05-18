import os
import sys


# Add custom CSS
def setup(app):
    app.add_stylesheet("css/custom.css")


# Set variable so that todos are shown in local build
on_rtd = os.environ.get("READTHEDOCS") == "True"

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------

project = "respy"
copyright = "2015-2019, Philipp Eisenhauer"
author = "Philipp Eisenhauer"

# The short X.Y version.
version = "1.2"
# The full version, including alpha/beta/rc tags.
release = "1.2.0"

# -- General configuration ------------------------------------------------

master_doc = "index"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.ifconfig",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "nbsphinx",
]

autodoc_mock_imports = ["numba", "numpy", "pandas", "yaml", "pytest", "scipy"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]
html_static_path = ["_static"]

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# If true, `todo` and `todoList` produce output, else they produce nothing.
if on_rtd:
    pass
else:
    todo_include_todos = True
    todo_emit_warnings = True

# Configure Sphinx' linkcheck
linkcheck_ignore = ["https://(dx\.)?doi\.org/*.", "https://zenodo\.org/*."]

# Configuration for nbsphinx
nbsphinx_execute = "never"
nbsphinx_allow_errors = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"
