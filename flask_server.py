from flask import Flask, request, render_template, redirect, url_for
import json
import os
import copy
   
#specification of the id for the section to use as the root of the tree structuring of sections
top_level_section = 'lu_questions_data_project_tombstone'

#object to track the responses  
responses = {'question_index': 0}




#load the questionnaire json data
with open('data/CostingFramework_Min_Enh.json', 'rb') as json_file:
    questions = json.load(json_file)
    
  
#expand the full object structure for a section of questions
def parse_questions(section_name):

    #for each question, if the question is a non-section object, expand it with a sub_questions attribute
    for question in questions[section_name]:
        if ((question['type'] == 'object') and (not('lu_questions' in question['format']))):
            question['sub_questions'] = parse_questions(question['format'])

    return questions[section_name]
    
    
#iterate over all question sections and expand the full object structures
for key in questions.keys():
    if ('lu_questions' in key):
        questions[key] = parse_questions(key)
    
    
    
           

#restore the tree structure for responses that were flattened by the HTML form submission
def parse_responses(res_dict):

    #create a dictionary to store a structured version of the responses after parsing
    parsed_dict = {}

    #for each response in the flat res_dict
    for res_key in res_dict.keys():
    
        # if there is only 1 ~ in the key, this is a leaf node and can go in the dictionary without further parsing
        if (res_key.count('~') == 1):
            parsed_dict[res_key[1:]] = res_dict[res_key]
            
        #otherwise, parsing is required to build up the structure
        elif(res_key.count('~') > 1):
            
            #extract the key for the current object between the first two ~s
            key = res_key[1:(res_key[1:].find('~')+1)]
 
            #only parse this object if it has not already been done (the object will show up in the flat res_dict for each one of its children)
            if (not(key) in parsed_dict):
            
                #create a dictionary to store flat collections of responses for each instance of the object
                instance_dict = {}
            
                #loop through the flat res_dict again to pick out all objects matching the current key
                for other_res_key in res_dict.keys():
                    if (other_res_key.count('~') > 1):
                    
                        tilde_ind = other_res_key[1:].find('~') + 1
                        other_key = other_res_key[1:tilde_ind]
                        
                        #if a key corresponding to the object has been found
                        if (other_key == key):
            
                            #extract the object instance number
                            next_tilde_ind = other_res_key[(tilde_ind+1):].find('~') + tilde_ind + 1
                            instance_num = other_res_key[(tilde_ind+5):next_tilde_ind]
                    
                            #if the instance number is not yet represented in the instance_dict, give it an empty object
                            if (not(instance_num) in instance_dict):
                                instance_dict[instance_num] = {}
                            
                            #using the remainder of the key after the object instance number identifier, add the current flat res_dict data for the instance to instance_dict
                            remaining_key = other_res_key[next_tilde_ind:]
                            instance_dict[instance_num][remaining_key] = res_dict[other_res_key]
                
                #create a list to store the parsed instances and populate it by recursively calling parse_responses on the flat instance_dict entries
                instance_list = []

                for instance_num in instance_dict.keys():
                    instance_list.append(parse_responses(instance_dict[str(instance_num)]))
                    
                #add the strucutre version of the of the instances to parsed_dict
                parsed_dict[key] = instance_list
                
    return parsed_dict


#build a table of contents data structure as a tree of sections that have been reach by the user so far
def extract_toc(response_obj):

    toc = {}
    num_incomplete = 0
    
    #for each key pertaining to a section at the current level of responses
    for key in response_obj.keys():
        if (('lu_questions' in key) and not('_subsection_instance_name' in key)):
        
            sub_toc = {}
            
            #for each instance of the section that has been created
            for ind in range(len(response_obj[key])):
            #for ind in response_obj[key]:
            
                sub_key = '%s~%s' % (key, response_obj[key][ind])
            
                #if the instance has its own response data, recursively parse it
                if (sub_key in responses):
                    children, sub_num_incomplete = extract_toc(responses[sub_key])
                    sub_toc[sub_key] = {'complete': True, 'children': children}
                    num_incomplete += sub_num_incomplete
                    
                #otherwise, store the instance as a leaf node of the tree
                else:
                    sub_toc[sub_key] = {'complete': False, 'children': {}}
                    num_incomplete += 1
                    
                sub_toc[sub_key]['name'] = response_obj['%s_subsection_instance_name' % key][ind]
              
            #store all the instances for the section
            toc[key] = sub_toc
            
    return toc, num_incomplete




  
#create the web app
app = Flask(__name__)


#spash page with options to load or start a new questionnaire
@app.route("/")
def index():
    return render_template('index.html')
       
    
#generic form template to display questions from one section
@app.route('/costing', methods=['GET', 'POST'])
def costing():   

    global responses
    
    #if responses were submitted
    if (request.method == 'POST'):
    
        toc_redirect = False
    
        #parse the submitted responses back into a tree structure and store this in the response data in memory
        responses[request.form['question_index']] = parse_responses(request.form.to_dict(flat=False))
        
        #if response data has been submitted without requesting navigation to a subsection, set up for navigation to the table of contents
        if (responses['question_index'] == request.form['edit_index']):
            toc_redirect = True
        
        #record the next section to edit
        responses['question_index'] = request.form['edit_index']
        
        #save the updated responses to disk
        with open('data/responses.json', 'w') as json_file:
            json.dump(responses, json_file)
        
        #if navigation to the table of contents is needed, redirect to the appropriate route
        if (toc_redirect):
            return redirect(url_for('toc'))
            
        #otherwise, redirect to the requested subsection
        else:
            return redirect(url_for('costing'))
    
    #if a question category form was requested
    else:
        #if the user starts a new questionnaire
        if (request.args.get('action') == 'new'):
            responses = {'question_index': top_level_section}
            
            #save the updated responses to disk
            with open('data/responses.json', 'w') as json_file:
                json.dump(responses, json_file)
            
        #if the user loads existing response data
        elif (request.args.get('action') == 'load'):
        
            #if data is present, load it
            if (os.path.exists('data/responses.json')):
                with open('data/responses.json', 'rb') as json_file:
                    responses = json.load(json_file)
                    
                #if a fully completed questionnaire was loaded, display the report
                if (responses['question_index'] == 'complete'):
                    return redirect(url_for('report'))
                    
            #otherwise, treat this as starting a new questionnaire if saved data does not exist
            else:
                responses = {'question_index': top_level_section}
        
        #if the user has navigated to a section form the table of contents, record what section is being accessed
        elif (request.args.get('action') == 'goto'):
            responses['question_index'] = request.args.get('question_index')
        
        #look up any saved responses to repopulate the input fields
        if (responses['question_index'] in responses):
            saved_responses = responses[responses['question_index']]
        else:
            saved_responses = {}
          
        #if the requested section corresponds to a section instance, remove the instance identifier from the question index
        if ('~' in responses['question_index']):
            question_index = responses['question_index'][:responses['question_index'].index('~')]
        else:
            question_index = responses['question_index']
                          
        #render the template for the current question category
        return render_template('costing.html', question_index=responses['question_index'], questions=questions[question_index], saved_responses=saved_responses)
        
  
#table of contents used for navigation through questionnaire sections
@app.route("/toc")
def toc():

    if (top_level_section in responses):
        toc, num_incomplete = extract_toc(responses[top_level_section])
    else:
       toc= {}
       num_incomplete = 1
       
    return render_template('toc.html', top_level_name=top_level_section, toc=toc, num_incomplete=num_incomplete)

  
#report of questions, responses and recommendations
@app.route("/report")
def report():
    return render_template('report.html', questions=questions, responses=responses, top_level_section=top_level_section)
  
    
    
    
    
    
    
    