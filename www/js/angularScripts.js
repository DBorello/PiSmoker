angular.module(['Program'],["firebase"])
    .controller('ProgramController',function($scope, $firebaseArray) {
        this.Program = $firebaseArray(ProgramRef);

        this.add = function add() {
            //this.Program.push({"mode": "Off", "target": 0, "trigger": "Time", "triggerValue": 600})
            this.Program.$add({"mode": "Off", "target": 0, "trigger": "Time", "triggerValue": 600});
        };

    });
