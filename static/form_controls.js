
// track the number of instances for each group of objects
var num_instances = [];

// configure the delete instance button
function configure_btn(obj, id){
	
	// look up the button for the object instance
	var btn = obj.querySelector('input[name="obj_btn_del"]');
	
	// if the button belongs to an instance that is not the first in the group, give it a click handler
	if (num_instances[id] > 1)
		btn.addEventListener('click', delete_instance(num_instances[id], id));
	
	// otherwise, remove the button (the first instance cannot be deleted)
	else
		obj.removeChild(btn);
	
	return false;
}

// click handler for the delete instance button, enclosed for parameterization
function delete_instance(obj_num, id){
	return function(){
		
		// look up and delete the object instance
		var obj = document.getElementById(`${id}_obj_${obj_num}`);
		obj.parentNode.removeChild(obj);
		
		return false;
	}
}

// click handler for the add instance button, enclosed for parameterization
function add_instance(id) {
	return function() {
		
		// look up the clone template and make a copy of it
		var obj = document.getElementById(`${id}_obj_0`);
		var new_obj = obj.cloneNode(true);
		
		// increase the instance count
		num_instances[id] += 1;
		
		// update the id for the cloned instance and remove its invisibility
		new_obj.id = `${id}_obj_${num_instances[id]}`;
		new_obj.classList.remove('invisible');
		
		// look up the fieldset of the cloned instance and enable it
		var fieldset = new_obj.querySelector('fieldset[name="obj_fieldset"]');
		fieldset.removeAttribute('disabled');
		
		// configure the delete button for the cloned instance
		configure_btn(new_obj, id);
		
		// add the cloned instance to the DOM
		obj.parentNode.appendChild(new_obj);
		
		return false;
	}
}

window.onload = function pageInit() {
	
	// look up all hidden tags containing object id prefixes (each represents one group of object instances)
	var hidden_ids = document.querySelectorAll('p[name="hidden_id"]');
	
	// for each group of object instances
	hidden_ids.forEach(function(node){
		num_instances[node.id] = 0
		
		// make the clone template invisible
		var obj = document.getElementById(`${node.id}_obj_0`)
		obj.classList.add('invisible');
		
		// disable the clone template
		var fieldset = obj.querySelector('fieldset[name="obj_fieldset"]');
		fieldset.setAttribute('disabled', '');
		
		// create a click handler for the add instance button
		var btn = document.getElementById(`${node.id}_btn_add`);
		btn.addEventListener('click', add_instance(node.id));

		// loop through object instances for the current group
		var obj = document.getElementById(`${node.id}_obj_${num_instances[node.id]+1}`);
		while (obj){
			// increase the instance count
			num_instances[node.id] += 1
			
			// configure the delete button for the current instance
			configure_btn(obj, node.id);
			
			// look up the next instance
			obj = document.getElementById(`${node.id}_obj_${num_instances[node.id]+1}`);
		}
		
		// if there are no instances (no saved data has been loaded), create one blank instance
		if (num_instances[node.id] == 0)
			add_instance(node.id)();
	});
}