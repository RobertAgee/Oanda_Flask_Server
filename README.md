# Oanda_Flask_Server
Ready-to-Deploy Trading Server for Oanda

# What is this?
A simple Flask server using the <a href="https://developer.oanda.com/rest-live-v20/introduction/">Oanda v20 REST API</a> to connect to Oanda for trading forex, crypto, and precious metals. This repo takes care of the bootstrappy bits so it's ready-to-deploy on a home computer or in the cloud.

# What can it do?
It has a number of built-in endpoints for checking your balance `GET /balance` or placing an IOC LIMIT order with TAKE_PROFIT `POST /order/ioc-limit-tp`. 
Additional features and commands can be added by exploring the Oanda documentation.

# How do I use it?
Simply put your keys and position details into the `.env` file and run it from its folder on the command line `flask run` or host it on a service like Koyeb.




