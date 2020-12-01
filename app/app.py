from flask import Flask, jsonify, request # initialize our Flask application
import requests

app= Flask(__name__)

@app.route("/v1", methods=["POST"])
def getData():
    if request.method=='POST':
        posted_data = request.get_json()
        data = posted_data['data'][::-1]
        all_caps_response = requests.post("HTTP://API.SHOUTCLOUD.IO/V1/SHOUT", json={'input': data})
        returned_data = all_caps_response.json()
        our_response = {'input': returned_data['INPUT'], 'output': returned_data['OUTPUT']}
        return jsonify(str(our_response['output']))
    
if __name__=='__main__':
    app.run(host='0.0.0.0')