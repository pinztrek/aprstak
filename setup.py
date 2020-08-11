from setuptools import setup

with open("README.md", "r") as fh:
      long_description = fh.read()

setup(name='aprstak',
      version='0.5',
      description='daemon to inject APRS reports into TAK servers',
      url='http://github.com/pinztrek/aprstak',
      author='Alan Barrow',
      author_email='traveler@pinztrek.com',
      license='GPLv3+',
      packages=setuptools.find_packages(),
      #packages=['takpak'],
      zip_safe=True,
      python_requires='>=3.6',
      classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
      ]
      )
