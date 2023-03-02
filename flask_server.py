from flask import Flask, request, render_template, redirect, url_for
import json
import os
   

#load the questionnaire json data
with open('data/CostingFramework_Min.json', 'rb') as json_file:
    questions = json.load(json_file)
    
#build an ordered list of the question categories
question_keys = []
for key in questions.keys():
    if ('lu_questions' in key):
        question_keys.append(key)
        
        #for any questions with objects as answer types, add the object structure to the question
        for question in questions[key]:
            if (question['type'] == 'object'):
                question['sub_questions'] = questions[question['format']]
        
#create an object to track the responses  
responses = {'question_index': 0}
    
  
#create the web app
app = Flask(__name__)


#spash page with options to load or start a new questionnaire
@app.route("/")
def index():
    return render_template('index.html')
       
    
#generic form template to display questions from one category
@app.route('/costing', methods=['GET', 'POST'])
def costing():   

    global responses
    
    #if responses were submitted
    if (request.method == 'POST'):
    
        #look up the key for the current set of questions
        question_key = question_keys[responses['question_index']]
    
        #update the response data in memory
        responses['question_index'] += 1
        responses[question_key] = request.form.to_dict(flat=False)
        
        #remove the imposed list structure from non-multivalue responses
        for response_key in responses[question_key].keys():
            if (len(responses[question_key][response_key]) == 1):
                responses[question_key][response_key] = responses[question_key][response_key][0]
        
        #save the updated responses to disk
        with open('data/responses.json', 'w') as json_file:
            json.dump(responses, json_file)
        
        #redirect to the next page of questions
        return redirect(url_for('costing', action='next'))
    
    #if a question category form was requested
    else:
        #if the user starts a new questionnaire
        if (request.args.get('action') == 'new'):
            responses = {'question_index': 0}
            
        #if the user loads existing response data
        elif (request.args.get('action') == 'load'):
            if (os.path.exists('data/responses.json')):
                with open('data/responses.json', 'rb') as json_file:
                    responses = json.load(json_file)
            #treat this as starting a new questionnaire if saved data does not exist
            else:
                responses = {'question_index': 0}
                
        #if the user navigates back to the previous category of questions
        elif (request.args.get('action') == 'prev'):
            responses['question_index'] -= 1
        
        #look up the key for the current set of questions
        question_key = question_keys[responses['question_index']]
        
        #look up any saved responses to repopulate the input fields
        if (question_key in responses):
            saved_responses = responses[question_key]
        else:
            saved_responses = {}
                
        #render the template for the current question category
        return render_template('costing.html', question_index=responses['question_index'], questions=questions[question_key], saved_responses=saved_responses)
    
    
    
    
    
    
    