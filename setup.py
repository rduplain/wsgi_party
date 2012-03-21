from setuptools import setup

setup(
    name='wsgi_party',
    version='0.1b1',
    url='http://github.com/rduplain/wsgi_party',
    license='BSD',
    author='Ron DuPlain',
    author_email='ron.duplain@gmail.com',
    description='A partyline middleware for WSGI with good intentions.',
    long_description=open('README.rst').read(),
    py_modules=['wsgi_party'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        # Werkzeug is convenient to get us started. Could potentially remove.
        'Werkzeug',
    ],
    test_suite='tests',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
