'use strict';
const NodeHelper = require('node_helper');

const {PythonShell} = require('python-shell');
var pythonStarted = false


//var websockets = require("websockets");

module.exports = NodeHelper.create({

	python_start: function () {
		const self = this;
		console.log("[" + self.name + "] starting python");
    	self.pyshell = new PythonShell('modules/' + this.name + '/python_scripts/center-display-combine.py', {args: [JSON.stringify(this.config)]});

  	},

	// Subclass socketNotificationReceived received.
  socketNotificationReceived: function(notification, payload) {
	const self = this;
	if(notification === 'CENTER_DISPLAY_CONFIG') {
      this.config = payload
      this.python_start(); 
    }else if(notification === 'CENTER_DISPLAY'){
		var data = {"SET": payload};
		self.pyshell.send(JSON.stringify(data));
	};
  },

	stop: function() {
		const self = this;
		self.pyshell.childProcess.kill('SIGINT');
		self.pyshell.end(function (err) {
           	if (err){
        		//throw err;
    		};
    		console.log('finished');
		});
		self.pyshell.childProcess.kill('SIGKILL');
	}

});
