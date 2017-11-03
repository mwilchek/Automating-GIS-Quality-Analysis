# coding=utf-8
"""
This is the program to load dependencies for AAMP and Start the Execution of the Application
All credit to the development of the application goes to Kevin Holmes, Melinda Schinstock and Matthew Wilchek
For any questions in regarding the technical process of AAMP please email one of them above.
"""
import Tkinter as tk
import pip
import os
from AAMP_Application import AAMP_Application

pip.main(['install', '--upgrade', 'pygubu'])
pip.main(['install', 'openpyxl'])
import openpyxl
import pygubu

if __name__ == '__main__':
    root = tk.Tk()
    app = AAMP_Application(root)
    app.run()

__author__ = 'Matt Wilchek, Kevin Holmes, Melinda Schinstock'
