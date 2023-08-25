
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
				var prefix = node.parentNode.parentNode.parentNode.id
				var question_short = node.name.substring(node.name.lastIndexOf('~')+1);
				node.name = `${prefix}~${question_short}`;
			});
		});
		
		// for each question fieldset, prefix its name with its parent id
		var fieldsets = new_obj.querySelectorAll('fieldset');
		fieldsets.forEach(function(node){	
			if (node.name.includes('~')){
				var prefix = node.parentNode.parentNode.id
				var question_short = node.name.substring(node.name.lastIndexOf('~')+1);
				node.name = `fieldset_${prefix}~${question_short}`;
			}			
		});

		return false;
	};
}


// THIS FUNCTIONALITY REQUIRES TESTING IF IT WILL LATER BE USED FOR TOGGLING WITHIN DYNAMICALLY ADDED OBJECT INSTANCES
function add_toggle_action(node, toggle_type){
	
	// extract the name of the target element
	var start = node.name.indexOf(toggle_type);
	var end = start + toggle_type.length
	var pre_toggle = node.name.substring(0, start);
	var post_toggle = node.name.substring(end);
	
	// look up the target element
	var fieldset = document.querySelector(`fieldset[name="fieldset_${pre_toggle}${post_toggle}"]`);
	
	// initially set the target element to be invisible
	if ((toggle_type == '__toggle_yes__') && (node.value != 'Yes') || (toggle_type == '__toggle_no__') && (node.value != 'No')){
		fieldset.classList.add('invisible');
		fieldset.setAttribute('disabled', '');
	}

	// apply and remove a hidden class based on the selection value
	node.addEventListener('change', function() {
		if ((toggle_type == '__toggle_yes__') && (this.value == 'Yes') || (toggle_type == '__toggle_no__') && (this.value == 'No')){
			fieldset.classList.remove('invisible');
			fieldset.removeAttribute('disabled', '');
		}else{
			fieldset.classList.add('invisible');
			fieldset.setAttribute('disabled', '');
		}
	});
}


// run when the page is first loaded
window.onload = function pageInit() {
	
	required_instances = new Object();
	
	// look up all hidden tags containing object id prefixes (each represents one group of object instances)
	var hidden_ids_mandatory = document.querySelectorAll('p[name="hidden_id_mandatory"]');
	
	// for each group of object instances
	hidden_ids_mandatory.forEach(function(node){
		required_instances[node.id] = 1;
	});
	
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
		if (btn !== null)
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
		if ((num_instances[node.id] == 0) && required_instances.hasOwnProperty(node.id))
			add_instance(node.id)();
	});
	
	
	// look up all hidden tags containing section ids (each represents one group of section instances)
	var section_ids = document.querySelectorAll('p[name="section_id"]');
	
	// for each group of section instances
	section_ids.forEach(function(node){
		
		// keep track of the highest known instance ID number, starting from 0 which is the default instance ID number
		num_instances[node.id] = 0;
		
		// loop through each saved instance that was rebuilt when generating the template and record the highest ID number among these
		var sec_instance_nums = node.parentNode.querySelectorAll(`input[name="~${node.id}"]`);
		sec_instance_nums.forEach(function(instance_node){
			num_instances[node.id] = Math.max(num_instances[node.id], Number(instance_node.value));
		});
		
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
	
	// look up all select elements
	var select_nodes = document.querySelectorAll('select');
	
	// for each select element, apply a toggle action if needed
	select_nodes.forEach(function(node){
		if (node.name.includes('__toggle_yes__'))
			add_toggle_action(node, '__toggle_yes__');
		
		if (node.name.includes('__toggle_no__'))
			add_toggle_action(node, '__toggle_no__');
	});
}





