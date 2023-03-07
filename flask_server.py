from flask import Flask, request, render_template, redirect, url_for
import json
import os
import copy
   
#ordered list of the question categories
question_keys = []

#object to track the responses  
responses = {'question_index': 0}


#load the questionnaire json data
with open('data/CostingFramework_Min.json', 'rb') as json_file:
    questions = json.load(json_file)
    

#iterate over all question categories
for key in questions.keys():
    if ('lu_questions' in key):
    
        #store the key to enforce an order for the categories
        question_keys.append(key)
        
        #check if each question has an object as an answer type, add the object structure to the question if so
        for question in questions[key]:
            if (question['type'] == 'object'):
                question['sub_questions'] = copy.deepcopy(questions[question['format']])
                
                #create a unique name for each subquestion
                for sub_question in question['sub_questions']:
                    sub_question['question_short'] = '%s_%s' % (question['question_short'], sub_question['question_short'])
                

  
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
        responses[question_key] = request.form.to_dict(flat=False)
        
        #increase the question index unless the final page has just been completed
        if (responses['question_index'] < len(question_keys)):
            responses['question_index'] += 1
        
        #save the updated responses to disk
        with open('data/responses.json', 'w') as json_file:
            json.dump(responses, json_file)
        
        #redirect to the report if the final page has been completed, otherwise redirect to the next page of questions
        if (responses['question_index'] == len(question_keys)):
            return redirect(url_for('report'))
        else:
            return redirect(url_for('costing', action='next'))
    
    #if a question category form was requested
    else:
        #if the user starts a new questionnaire
        if (request.args.get('action') == 'new'):
            responses = {'question_index': 0}
            
        #if the user loads existing response data
        elif (request.args.get('action') == 'load'):
        
            #if a load was requested when a fully complete questionnaire is present in memory, step back to the last question
            if (responses['question_index'] == len(question_keys)):
                responses['question_index'] -= 1
        
            #if data is present, load it
            elif (os.path.exists('data/responses.json')):
                with open('data/responses.json', 'rb') as json_file:
                    responses = json.load(json_file)
                    
                #if a fully completed questionnaire was loaded, display the report
                if (responses['question_index'] == len(question_keys)):
                    return redirect(url_for('report'))
                    
            #otherwise, treat this as starting a new questionnaire if saved data does not exist
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
        return render_template('costing.html', question_index=responses['question_index'], total_pages=len(question_keys), questions=questions[question_key], saved_responses=saved_responses)
        
        
#report of questions, responses and recommendations
@app.route("/report")
def report():
    return render_template('report.html', questions=questions, responses=responses)
    
    
    
    
    
    
    