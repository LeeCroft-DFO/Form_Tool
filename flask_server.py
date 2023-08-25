from flask import Flask, request, render_template, redirect, url_for
import json
import os
import copy
   
#specification of assessment type
assessment_type = 'data_ethics' # 'data_ethics', 'responsible_ai'
   
#specification of the id for the section to use as the root of the tree structuring of sections
top_level_section = 'sec_top'

#object to track the responses  
responses = {'question_index': 0}




#load the questionnaire json data
if (assessment_type == 'data_ethics'):
    with open('data/Data_Ethics.json', 'rb') as json_file:
        questions = json.load(json_file)
        
elif (assessment_type == 'responsible_ai'):
    with open('data/Responsible_AI.json', 'rb') as json_file:
        questions = json.load(json_file)
    
  
#expand the full object structure for a section of questions
def parse_questions(section_name):

    #for each question, if the question is a non-section object, expand it with a sub_questions attribute
    for question in questions[section_name]:
        if ((question['type'] == 'object') and (not('sec_' in question['format']))):
            question['sub_questions'] = parse_questions(question['format'])

    return questions[section_name]
    
    
#look up the title and instructions for the given section
def get_instructions(question_index):

    section_title = 'Self-Assessment Questionnaire'
    
    if (assessment_type == 'data_ethics'):
        section_instructions = 'The questions in the following sections should be answered in relation to a planned activity involving interactions with data (henceforth, the Activity). These interactions may include, but are not limited to, collection, usage (e.g., for operational decision-making, research, exploratory analysis, etc.) and dissemination of data. The Activity may vary in scope from small-scale interactions to large-scale projects and may involve interactions with multiple sources of data.'
    
    elif (assessment_type == 'responsible_ai'):
        section_instructions = 'The questions in the following sections should be answered in relation to a project involving interactions with AI. These interactions may include, but are not limited to, training, usage and monitoring of an AI model.'
    
    for section in questions.values():
        for question in section:
            if (('sec_' in question['question_short']) and (question['question_short'] == question_index)):
                section_title = question['question_title']
                section_instructions = question['question_long']
                
                break
            
    return section_title, section_instructions
    
    
#count the number of total sections and how many have been completed
def count_sections(question_index):

    sections_complete = 0
    sections_total = 0

    for section in questions[question_index]:
        if (section['format'][:4] == 'sec_'):
            sections_total += 1
            
            child_sections_complete, child_sections_total = count_sections(section['format'])

            if ((child_sections_complete == child_sections_total) and ('%s~0' % section['format']) in responses.keys()):
                sections_complete += 1
          
    return sections_complete, sections_total
    
    
#iterate over all question sections and expand the full object structures
for key in questions.keys():
    if ('sec_' in key):
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
            return redirect(url_for('costing', action='goto', question_index='sec_top'))
            
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
                          
        #get the title and instructions for the requested section
        section_title, section_instructions = get_instructions(question_index) 
        
        #count the number of total sections and how many have been completed
        sections_complete, sections_total = count_sections(top_level_section)
                         
        #render the template for the current question category
        return render_template('costing.html', section_title=section_title, section_instructions=section_instructions, sections_complete=sections_complete, sections_total=sections_total, question_index=responses['question_index'], questions=questions[question_index], saved_responses=saved_responses)
        

  
#report of questions, responses and recommendations
@app.route("/report")
def report():
    return render_template('report.html', questions=questions, responses=responses, top_level_section=top_level_section)
  
    
    
    
    
    
    
    