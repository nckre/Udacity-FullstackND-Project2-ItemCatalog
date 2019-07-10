# Project 2: Catalog Application
### Udacity Full Stack Web Development ND
_______________________
## Item Catalog Project
This project, Noah's Ark, was developed to pass the second project in Udacity's Full Stack Nanodegree program (July '19'). The application tracks which animals are on board of the ark. It categorizes animals in a variety of classes and families. Classes and Families can be added by users who have registered & loged in via an OAUTH authentication system. Authenticated users can further edit and delete items they have created.
_______________________
## Prerequisites
### Python, SQL & Flask
This project makes use of a Linux-based virtual machine (VM), a SQLite database and Python.
### Virtual Box
VirtualBox is software that runs virtual machines. Download it from [virtualbox.org](https://www.virtualbox.org/wiki/Downloads). Install the platform package for Mac. No need to download the extension pack or the SDK.

### Vagrant
Vagrant is the software that configures the VM and lets you share files between your host computer and the VM's filesystem. Download it from [vagrantup.com](https://www.vagrantup.com/downloads.html). This project requires a specific vagrant file (`udacity fullstack vm`) provided by Udacity for the nanodegree. Please download it [here] (https://github.com/udacity/fullstack-nanodegree-vm).

### Python
The main app, project.py, is written in Python and makes use of SQLAlchemy and a SQLite database (animal_catalog.db) to store information on animal classes (table: AnimalClasses), families (table: ClassFamilies) and the users who created them (table: Users). Flask is used to render interactive HTML templates that GET and POST information from/to the database. The authentication is done via exchanging tokens with Google OAUTH2's service. The login page performs the authentication via AJAX scripts.
_______________________
## Running the application
In order to run the python script, follow these steps:
1. Download and extract the .zip file into your /vagrant directory
2. Bring the virtual machine online (with `vagrant up`). Then log into it with `vagrant ssh`. Your shell prompt should start with the word "vagrant" displaying that you're logged into your Linux VM.
3. Use your shell to `cd` into the `vagrant` directory

### Run the .py files
1. To create a test entry, run the file:
```
python prepopulateDB.py
```
2. Run the main file to start hosting the web application on your localhost
```
python project.py
```
3. You can test out the API functionality by adding a `/JSON` to URLs of the overview of all classes, the overview of all families in a class and individual family members. For example, `/classes/1/family/JSON` will show the name, id and description of the animal class with the `id = 1` in JSON format.

_______________________
### Log in and manage the Ark
Use your favorite browser to connect to the application at http://localhost:8000/classes.
After you go to the page Login and authenticate via Google OAUTH, you can add, edit and delete your animal classes and families.

### Log out and terminate the server
Once you're logged in, you will see a Logout link in the sidebar navigation. Click on the link to end your session.
In the shell, you can end the web server and exit vagrant by pressing CTRL+C twice.
