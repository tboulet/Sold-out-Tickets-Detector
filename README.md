# Sold-out-Tickets-Detector
A bot for detecting when concerts and festival tickets are sold out.

# Use the MVP script

## Installation
Follows those steps :
- Install python. This bot works at least in python version 3.9.7 so I suggest you to install this version. You can download it [here](https://www.python.org/downloads/release/python-397/). For Windows users, use the 'Windows installer (64-bit)' installer in the bottom of the page.
- Assert you are using the good python version. If not, you would have to replace 'python' by the path to the python 3.9.7 executable in the next command (but not for the other commands, since you will already be placed in the good python environment):
    
    ```bash
    python --version
    ```

- Create a python virtual environment for the project and activate it :

    ```bash
    python -m venv venv
    venv\Scripts\activate  # use this command on windows
    source venv/bin/activate  # use this command on linux
    ```
    You should see '(venv)' at the beginning of your command line now. This means you are placed in the virtual environment used for this project. You can deactivate it with the command 'deactivate', but for when you are using the project, please stay in this virtual environment.


- Install the required libraries :
    
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Use this command for evaluating whether the ticket of the url is working :
    
```bash
python is_soldout.py <the_ticket_url>
```

For example, this should print 'True' in the console :

```bash
python is_soldout.py https://concerts.livenation.com/don-toliver-thee-love-sick-tour-houston-texas-07-08-2023/event/3A005E7D223A7CD8?
```

Note :
- The command only works with webticket urls
- The command (probably) only works with urls of the form 'https://www.ticketweb.com/event/event_name/0123456789'. The criteria is the url must lead to a page with a "ticket" section. This is not verified and possibly unstable.
- This simple script should in the future evolve to a bot that tracks the ticket availability of registered urls and sends an notification when the ticket is sold out.