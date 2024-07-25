 #  ________   ___   __    ______   ______   ______    ______   ______   ___   __    ______   ________   ___ __ __     
 # /_______/\ /__/\ /__/\ /_____/\ /_____/\ /_____/\  /_____/\ /_____/\ /__/\ /__/\ /_____/\ /_______/\ /__//_//_/\    
 # \::: _  \ \\::\_\\  \ \\:::_ \ \\::::_\/_\:::_ \ \ \::::_\/_\::::_\/_\::\_\\  \ \\::::_\/_\::: _  \ \\::\| \| \ \   
 #  \::(_)  \ \\:. `-\  \ \\:\ \ \ \\:\/___/\\:(_) ) )_\:\/___/\\:\/___/\\:. `-\  \ \\:\/___/\\::(_)  \ \\:.      \ \  
 #   \:: __  \ \\:. _    \ \\:\ \ \ \\::___\/_\: __ `\ \\_::._\:\\::___\/_\:. _    \ \\_::._\:\\:: __  \ \\:.\-/\  \ \ 
 #    \:.\ \  \ \\. \`-\  \ \\:\/.:| |\:\____/\\ \ `\ \ \ /____\:\\:\____/\\. \`-\  \ \ /____\:\\:.\ \  \ \\. \  \  \ \
 #     \__\/\__\/ \__\/ \__\/ \____/_/ \_____\/ \_\/ \_\/ \_____\/ \_____\/ \__\/ \__\/ \_____\/ \__\/\__\/ \__\/ \__\/    
 #                                                                                                               
 # Project: RSS Parser on GKE Autopilot Spot Pod Demo
 # @author : Samuel Andersen
 # @version: 2024-04-30
 #
 # General Notes:
 #
 # TODO: Continue adding functionality 
 #

from flask import Flask, request
from flask_restful import Api, Resource

# Setup the Flask app
app = Flask(__name__)

# Setup the RESTful API
api = Api(app)

## Simple Response to the /healthz call
class Healthy(Resource):

    ## Method to respond to OPTIONS
    def options(self):

        return {'Allow': 'GET'}, 200

    ## Method to handle GET requests
    def get(self):

        return "This app is indeed healthy!", 200

## Define the APIs we're exposing in this section
# K8s Health Check:
api.add_resource(Healthy, '/healthz')