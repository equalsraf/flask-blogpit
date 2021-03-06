"""
Flask-blogpit
-------------

Flask extension to use blogpit as blog storage
"""
from setuptools import setup


setup(
    name='Flask-blogpit',
    version='0.1',
    license='BSD',
    author='ruiabreuferreira',
    author_email='raf-ep@gmx.com',
    description='Blogpit blog storage provider',
    long_description=__doc__,
    packages=['flask_blogpit'],
    package_data={'flask_blogpit':['templates/blogpit/*','templates/*.html']},
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask', 'BeautifulSoup', 'Flask-WTF', 'markdown',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
