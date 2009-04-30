from distutils.core import setup
import py2exe

setup(
    name         = "Timber",
    version      = "1.0",
    author       = "Eric W. Wallace",
    author_email = "e@ewall.org",
    description  = "Tails a log file and sends alert emails when the watched terms are seen.",
    
    console      = ['Timber.py']

    )

"""
        options      = {
                            "py2exe":{
                                "unbuffered": True,
                                "optimize": 2,
                                "includes": ["email"]
                            }
                       }
"""
