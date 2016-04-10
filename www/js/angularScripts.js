var app = angular.module(['PiSmoker'],["firebase",'toggle-switch']);
    app.controller('ProgramController',function($scope, $firebaseArray) {
        this.Program = $firebaseArray(ProgramRef);

        this.add = function add() {
            //this.Program.push({"mode": "Off", "target": 0, "trigger": "Time", "triggerValue": 600})
            this.Program.$add({"mode": "Off", "target": 0, "trigger": "Time", "triggerValue": 600});
        };

    });

//angular.module(['Parameters'],["firebase", 'toggle-switch'])
    app.controller('ParametersController',function($scope, $firebaseObject, $interval) {
        ctrl = this;
        this.Auth = false;
        this.Active = false;

        var syncObject = $firebaseObject(ParametersRef);
        syncObject.$bindTo($scope, "Parameters");

        //Authenticate
        Ref.authWithCustomToken(window.location.search.substring(1), function(error, authData) {
            if (error) {
                //console.log("Login Failed!", error);
                document.getElementById('ParmForm').style.visibility = 'hidden'
            } else {
                console.log("Login Succeeded!", authData);
                ctrl.Auth = true;
            }
        });


        this.CheckActive = function CheckActive() {
            if (T1.length > 0 && ((new Date).getTime() - T1[T1.length-1][0]) < 5000  ) {
                ctrl.Active = true;
            } else {
                ctrl.Active = false;
            }
        }

        $interval(this.CheckActive,3000)


    });