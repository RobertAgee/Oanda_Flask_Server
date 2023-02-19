# Oanda_Flask_Server
Ready-to-Deploy Trading Server for Oanda

# What is this?
A simple Flask server using the <a href="https://github.com/kieran-mackle/AutoTrader">AutoTrader library</a> to connect to Oanda for trading forex, crypto, and precious metals.  
This repo takes care of the bootstrappy bits so it's ready-to-deploy on a home computer or in the cloud.

# What can it do?
It has a couple of built-in endpoints for checking your balance `GET /balance` or placing an order `POST /order`. 
Additional features and commands can be added by exploring <a href="https://autotrader.readthedocs.io/en/latest/index.html">AutoTrader's documentation.</a>

# How do I use it?
Simply put your keys into the `config/keys.yaml` file and run it from its folder on the command line `flask run` or host it on a service like Heroku.




