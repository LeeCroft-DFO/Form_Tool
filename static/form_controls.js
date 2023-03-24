
// track the number of instances for each group of objects
var num_instances = [];

// list of possible input type elements that need ID prefixes assigned to properly track responses
var input_selectors = ['input[type="text"]', 'input[type="number"]', 'textarea', 'select'];


// configure the delete object instance button
function configure_btn(obj, id){
	
	// if a template instance has been encountered, do not modify it
	if (id.includes('_0~'))
		return	
	
	// look up the delete buttons (there may be multiple if there are nested objects) for the object instance
	var del_btns = obj.querySelectorAll('input[name="obj_btn_del"]');
	
	del_btns.forEach(function(del_btn){

		var parent_id = del_btn.parentNode.id;
	
		// if the button belongs to an instance that is the first in the group, remove the button (the first instance cannot be deleted)
		if (parent_id.substring(parent_id.length-2) == '_1')
			obj.removeChild(del_btn);
	
		// otherwise, give it a click handler to delete the object instance
		else
			del_btn.addEventListener('click', function(){
				var div = del_btn.parentNode;
				div.parentNode.removeChild(div);
			});
	});
	
	
	
	return false;
}


// click handler for the add object instance button, enclosed for parameterization
function add_instance(id) {
	return function() {
		
		// look up the clone template and make a copy of it
		var obj = document.getElementById(`${id}~obj_0`);
		var new_obj = obj.cloneNode(true);
		
		// increase the instance count
		num_instances[id] += 1;
		
		// update the id for the cloned instance and remove its invisibility
		new_obj.id = `${id}~obj_${num_instances[id]}`;
		new_obj.classList.remove('invisible');
		
		// look up the fieldset of the cloned instance and enable it
		var fieldset = new_obj.querySelector('fieldset[name="obj_fieldset"]');
		fieldset.removeAttribute('disabled');
		
		// configure the delete button for the cloned instance
		configure_btn(new_obj, id);
		
		// add the cloned instance to the DOM
		obj.parentNode.appendChild(new_obj);
		
		// for each input element, prefix its name with its parent id
		input_selectors.forEach(function(input_selector){
			var inputs = new_obj.querySelectorAll(input_selector);
			
			inputs.forEach(function(node){			
				var prefix = node.parentNode.parentNode.id
				var question_short = node.name.substring(node.name.lastIndexOf('~')+1);
				node.name = `${prefix}~${question_short}`;
			});
		});
		
		return false;
	};
}


// click handler for the add section instance button, enclosed for parameterization
function add_sec_instance(id, fieldset){
	return function(){
		
		num_instances[id] += 1;
		
		// create a div container for the new instance and give it a unique ID
		var div = document.createElement('div');
		div.id = `${id}~${num_instances[id]}`;
		
		// create a hidden input element used to track information about the instance ID
		var input_hidden = document.createElement('input');
		input_hidden.type = 'hidden';
		input_hidden.name = `~${id}`;
		input_hidden.value = num_instances[id];
		
		// create an edit instance button and give it a click listener to update the value of a hidden input field to the ID of the instance to be edited (navigation to that page is then handled by the form submission in the default behaviour of the button)
		var input_edit = document.createElement('input');
		input_edit.type = 'submit';
		input_edit.name = 'sec_btn_edit';
		input_edit.value = 'Edit Instance';
		input_edit.addEventListener('click', function(){
			document.getElementById('hidden_edit_index').value = div.id;
		});
		
		// create a delete button and give it a click listener to delete the div tag containing the instance
		var input_del = document.createElement('input');
		input_del.type = 'button';
		input_del.name = 'sec_btn_del';
		input_del.value = 'Delete Instance';
		input_del.addEventListener('click', function(){
			fieldset.removeChild(div);
		});
		
		// add the created elements to the div container and add the div container to the DOM
		div.appendChild(input_hidden);
		div.appendChild(input_edit);
		div.appendChild(input_del);
		fieldset.appendChild(div);
	};
}


// run when the page is first loaded
window.onload = function pageInit() {
	
	// look up all hidden tags containing object id prefixes (each represents one group of object instances)
	var hidden_ids = document.querySelectorAll('p[name="hidden_id"]');
	
	// for each group of object instances
	hidden_ids.forEach(function(node){
		num_instances[node.id] = 0

		// make the clone template invisible
		var obj = document.getElementById(`${node.id}~obj_0`)
		obj.classList.add('invisible');
		
		// disable the clone template
		var fieldset = obj.querySelector('fieldset[name="obj_fieldset"]');
		fieldset.setAttribute('disabled', '');
		
		// create a click handler for the add instance button
		var btn = document.getElementById(`${node.id}_btn_add`);
		btn.addEventListener('click', add_instance(node.id));
		
		// loop through object instances for the current group
		var obj = document.getElementById(`${node.id}~obj_${num_instances[node.id]+1}`);
		while (obj){
			
			// increase the instance count
			num_instances[node.id] += 1
			
			// configure the delete button for the current instance
			configure_btn(obj, node.id);
			
			// look up the next instance
			obj = document.getElementById(`${node.id}~obj_${num_instances[node.id]+1}`);
		}
		
		// if there are no instances (no saved data has been loaded), create one blank instance
		if (num_instances[node.id] == 0)
			add_instance(node.id)();
	});
	
	
	// look up all hidden tags containing section ids (each represents one group of section instances)
	var section_ids = document.querySelectorAll('p[name="section_id"]');
	
	// for each group of section instances
	section_ids.forEach(function(node){
		
		// keep track of the highest known instance ID number, starting from 0 which is the default instance ID number
		num_instances[node.id] = 0;
		
		// loop through each saved instance that was rebuilt when generating the template and record the highest ID number among these
		var sec_instance_nums = node.parentNode.querySelectorAll(`input[name="${node.id}"]`);
		sec_instance_nums.forEach(function(instance_node){
			num_instances[node.id] = Math.max(num_instances[node.id], Number(instance_node.value));
		});
		
		// add a click listener to the button used to generate additional section instances within the current group
		var btn = document.getElementById(`${node.id}_btn_add`);
		btn.addEventListener('click', add_sec_instance(node.id, node.parentNode));
		
		// for each section instance, add a click listener to the button used to edit the instance
		var sec_edit_btns = node.parentNode.querySelectorAll('input[name="sec_btn_edit"]');
		sec_edit_btns.forEach(function(edit_btn){
			// use the click listener to update the value of a hidden input field to the ID of the instance to be edited (navigation to that page is then handled by the form submission in the default behaviour of the button)
			edit_btn.addEventListener('click', function(){
				document.getElementById('hidden_edit_index').value = edit_btn.parentNode.id;
			});
		});
		
		// for each section instance, add a click listener to the button used to delete the instance
		var sec_del_btns = node.parentNode.querySelectorAll('input[name="sec_btn_del"]');
		sec_del_btns.forEach(function(del_btn){
			// use the click listener to delete the div tag containing the instance
			del_btn.addEventListener('click', function(){
				var div = del_btn.parentNode;
				div.parentNode.removeChild(div);
			});
		});
	});
}





