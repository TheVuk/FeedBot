from configparser import ConfigParser
import os


class FBObjects:
    # General config to set config file
    parser = ConfigParser()
    parser.read(os.getenv("FEEDBOT_CONFIG"))

    # To Store and maintain top movers and ib subscription request id
    TOP_MOVERS = {}

    # top mover corn thread flag when it become false nse corn will be stoped
    STOP_NSE_TOOL = False

